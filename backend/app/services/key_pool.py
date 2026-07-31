"""NVIDIA NIM API key pool with per-agent affinity, health tracking and cooldown failover.

Why this exists
---------------
Every agent in this platform (deep research, code squad, chat, memory, web search)
talks to the same NVIDIA NIM endpoint. If they all present the same API key, the
account-level rate limit is shared and concurrent stages throttle each other —
which is exactly what produced the 429/502 storms this module replaces.

The pool solves that with three mechanisms:

1. **Agent affinity** — each logical agent is pinned to a distinct key. Agent 1
   gets key 1, agent 2 gets key 2, and so on, wrapping around the pool. Agents
   that are known to run *concurrently* (the deep-research parallel stage, the
   code swarm) are hand-assigned to guarantee they never collide on one key.

2. **Cooldown failover** — a key that returns 429/quota-exceeded is parked for a
   backoff window. Callers transparently fail over to the healthiest remaining
   key instead of retrying into the same wall.

3. **Per-key concurrency** — each key carries its own semaphore, so the pool's
   total throughput scales with the number of keys instead of being capped by a
   single global limit.

Usage
-----
    async with key_pool.lease("synthesis") as lease:
        response = await call_nvidia(payload, lease.key)
        # on a rate limit, raise or call lease.mark_rate_limited()
"""

from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Tuning ────────────────────────────────────────────────────────────────
# Concurrent in-flight requests permitted per individual key. NVIDIA NIM
# tolerates a handful of parallel requests per key; beyond that it returns 429.
MAX_CONCURRENT_PER_KEY = 4

# Backoff applied to a key after a rate-limit response. Grows with consecutive
# failures so a genuinely exhausted key stops being retried aggressively.
RATE_LIMIT_COOLDOWN_BASE = 20.0    # seconds
RATE_LIMIT_COOLDOWN_MAX = 300.0    # seconds

# Backoff for hard errors (5xx, connection failures) — shorter, since these are
# usually transient and not quota-related.
ERROR_COOLDOWN_BASE = 5.0
ERROR_COOLDOWN_MAX = 60.0

# How long to wait for a key to free up before giving up entirely.
ACQUIRE_TIMEOUT = 180.0


# ── Agent affinity ────────────────────────────────────────────────────────
# Agents listed here are known to execute *concurrently*. Assigning them
# explicit, distinct slots guarantees a parallel stage spreads across all keys
# rather than stacking on one. Slots are modulo the live key count, so this
# degrades gracefully when fewer keys are configured.
#
# Slot numbering is 0-based: slot 0 -> key 1, slot 1 -> key 2, ...
EXPLICIT_AFFINITY: Dict[str, int] = {
    # ── Deep research: the four agents in the parallel analysis stage ──
    "knowledge_graph": 0,
    "temporal": 1,
    "cross_validation": 2,
    "data_scientist": 3,
    # ── Deep research: sequential stages, spread to even out quota burn ──
    "intent": 1,
    "planner": 2,
    "adversarial_query": 3,
    "local_retriever": 0,
    "scraper": 1,
    "academic": 2,
    "deep_content": 3,
    "critic": 0,
    "synthesis": 1,
    "archiver": 2,
    "gap_filler": 3,
    "verifier": 0,
    # ── Code squad: the coder swarm runs many of these at once ──
    "architect": 0,
    "spec_writer": 1,
    "task_decomposer": 2,
    "coder": 3,
    "tester": 0,
    "debugger": 1,
    "optimizer": 2,
    "reviewer": 3,
    # ── Interactive / foreground paths ──
    # Chat is latency-sensitive and user-facing, so it gets slot 0 and is the
    # first to benefit from an idle key.
    "chat": 0,
    "memory": 2,
    "web_search": 1,
    "thinking": 3,
    "image": 2,
}


@dataclass
class KeyState:
    """Live health and utilisation state for a single API key."""

    key: str
    slot: int
    semaphore: asyncio.Semaphore = field(repr=False, default=None)  # type: ignore[assignment]
    in_flight: int = 0
    cooldown_until: float = 0.0
    consecutive_failures: int = 0
    total_requests: int = 0
    total_rate_limits: int = 0
    total_errors: int = 0

    def __post_init__(self) -> None:
        if self.semaphore is None:
            self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_PER_KEY)

    @property
    def label(self) -> str:
        """Log-safe identifier — never emits the secret itself."""
        return f"key#{self.slot + 1}({self.key[:8]}…)"

    @property
    def is_cooling(self) -> bool:
        return time.monotonic() < self.cooldown_until

    @property
    def cooldown_remaining(self) -> float:
        return max(0.0, self.cooldown_until - time.monotonic())


class KeyLease:
    """A borrowed key. Report the outcome so the pool can track key health."""

    def __init__(self, pool: "KeyPool", state: KeyState, agent: str):
        self._pool = pool
        self._state = state
        self.agent = agent
        self._outcome_reported = False

    @property
    def key(self) -> str:
        return self._state.key

    @property
    def label(self) -> str:
        return self._state.label

    def mark_rate_limited(self) -> None:
        """Park this key — quota or concurrency limit hit."""
        self._outcome_reported = True
        self._pool._report_rate_limit(self._state)

    def mark_error(self) -> None:
        """Apply a short cooldown — transient server/connection failure."""
        self._outcome_reported = True
        self._pool._report_error(self._state)

    def mark_success(self) -> None:
        self._outcome_reported = True
        self._pool._report_success(self._state)

    def _finalize(self) -> None:
        """Default to success if the caller never reported an outcome."""
        if not self._outcome_reported:
            self._pool._report_success(self._state)


class NoKeysConfigured(RuntimeError):
    """Raised when the pool holds no usable keys."""


class KeyPool:
    """Manages a set of interchangeable NVIDIA NIM API keys."""

    def __init__(self, keys: Optional[List[str]] = None):
        self._states: List[KeyState] = []
        self._dynamic_affinity: Dict[str, int] = {}
        self._next_dynamic_slot = 0
        self._lock = asyncio.Lock()
        if keys:
            self.configure(keys)

    # ── Configuration ────────────────────────────────────────────────────
    def configure(self, keys: List[str]) -> None:
        """(Re)build the pool from an ordered list of keys. Duplicates removed."""
        seen: set = set()
        unique: List[str] = []
        for k in keys:
            k = (k or "").strip()
            if k and k not in seen:
                seen.add(k)
                unique.append(k)

        self._states = [KeyState(key=k, slot=i) for i, k in enumerate(unique)]
        self._dynamic_affinity.clear()
        self._next_dynamic_slot = 0

        if not self._states:
            logger.error(
                "KeyPool: no NVIDIA API keys configured. Set NVIDIA_API_KEY_1..4 "
                "(or DEFAULT_CHAT_API_KEY) in the environment."
            )
        else:
            logger.info(
                "KeyPool: %d NVIDIA key(s) active — %s",
                len(self._states),
                ", ".join(s.label for s in self._states),
            )

    @property
    def size(self) -> int:
        return len(self._states)

    # ── Affinity ─────────────────────────────────────────────────────────
    def slot_for(self, agent: str) -> int:
        """Resolve an agent name to its preferred slot index.

        Known agents use the hand-tuned EXPLICIT_AFFINITY table. Unknown agents
        are handed successive slots round-robin on first sight, so two distinct
        callers never share a key until every key has been handed out once.
        """
        if not self._states:
            return 0

        key_count = len(self._states)
        explicit = EXPLICIT_AFFINITY.get(agent)
        if explicit is not None:
            return explicit % key_count

        if agent not in self._dynamic_affinity:
            self._dynamic_affinity[agent] = self._next_dynamic_slot % key_count
            self._next_dynamic_slot += 1
            logger.debug(
                "KeyPool: agent '%s' assigned slot %d",
                agent,
                self._dynamic_affinity[agent],
            )
        return self._dynamic_affinity[agent]

    # ── Selection ────────────────────────────────────────────────────────
    def _select(self, agent: str) -> Optional[KeyState]:
        """Pick the best key for this agent, or None if all are cooling."""
        preferred_slot = self.slot_for(agent)
        healthy = [s for s in self._states if not s.is_cooling]
        if not healthy:
            return None

        # 1. Preferred key, if healthy and not saturated.
        preferred = next((s for s in healthy if s.slot == preferred_slot), None)
        if preferred is not None and preferred.in_flight < MAX_CONCURRENT_PER_KEY:
            return preferred

        # 2. Otherwise the least-loaded healthy key — keeps a hot agent from
        #    blocking behind its own affinity when a sibling key is idle.
        return min(healthy, key=lambda s: (s.in_flight, s.slot))

    @asynccontextmanager
    async def lease(self, agent: str = "default"):
        """Borrow a key for one request.

        Blocks until a healthy key has capacity, or raises on timeout.
        Always release via the context manager so in-flight counts stay accurate.
        """
        if not self._states:
            raise NoKeysConfigured(
                "No NVIDIA API keys configured. Set NVIDIA_API_KEY_1..4 in the environment."
            )

        deadline = time.monotonic() + ACQUIRE_TIMEOUT
        state: Optional[KeyState] = None

        while state is None:
            async with self._lock:
                state = self._select(agent)

            if state is None:
                # Every key is cooling — wait for the earliest to recover.
                soonest = min(s.cooldown_remaining for s in self._states)
                if time.monotonic() + soonest > deadline:
                    raise NoKeysConfigured(
                        f"All {len(self._states)} NVIDIA keys are rate-limited; "
                        f"soonest recovery in {soonest:.0f}s."
                    )
                logger.warning(
                    "KeyPool: all keys cooling, agent '%s' waiting %.0fs", agent, soonest
                )
                await asyncio.sleep(min(soonest, 5.0) + 0.1)

        # Acquire that key's concurrency slot.
        try:
            await asyncio.wait_for(
                state.semaphore.acquire(),
                timeout=max(1.0, deadline - time.monotonic()),
            )
        except asyncio.TimeoutError as exc:
            raise NoKeysConfigured(
                f"Timed out waiting for NVIDIA key capacity for agent '{agent}'."
            ) from exc

        async with self._lock:
            state.in_flight += 1
            state.total_requests += 1

        lease = KeyLease(self, state, agent)
        logger.debug("KeyPool: agent '%s' -> %s", agent, state.label)
        try:
            yield lease
        finally:
            lease._finalize()
            async with self._lock:
                state.in_flight = max(0, state.in_flight - 1)
            state.semaphore.release()

    # ── Health reporting ─────────────────────────────────────────────────
    def _report_success(self, state: KeyState) -> None:
        state.consecutive_failures = 0
        state.cooldown_until = 0.0

    def _report_rate_limit(self, state: KeyState) -> None:
        state.total_rate_limits += 1
        state.consecutive_failures += 1
        backoff = min(
            RATE_LIMIT_COOLDOWN_BASE * (2 ** (state.consecutive_failures - 1)),
            RATE_LIMIT_COOLDOWN_MAX,
        )
        state.cooldown_until = time.monotonic() + backoff
        logger.warning(
            "KeyPool: %s rate-limited (x%d) — cooling for %.0fs",
            state.label,
            state.consecutive_failures,
            backoff,
        )

    def _report_error(self, state: KeyState) -> None:
        state.total_errors += 1
        state.consecutive_failures += 1
        backoff = min(
            ERROR_COOLDOWN_BASE * (2 ** (state.consecutive_failures - 1)),
            ERROR_COOLDOWN_MAX,
        )
        state.cooldown_until = time.monotonic() + backoff
        logger.warning(
            "KeyPool: %s error (x%d) — cooling for %.0fs",
            state.label,
            state.consecutive_failures,
            backoff,
        )

    # ── Introspection (for /health and the admin dashboard) ──────────────
    def stats(self) -> dict:
        """Health snapshot. Never includes full key material."""
        return {
            "key_count": len(self._states),
            "max_concurrent_per_key": MAX_CONCURRENT_PER_KEY,
            "keys": [
                {
                    "slot": s.slot + 1,
                    "fingerprint": s.key[:8] + "…" if s.key else "",
                    "in_flight": s.in_flight,
                    "healthy": not s.is_cooling,
                    "cooldown_remaining_s": round(s.cooldown_remaining, 1),
                    "total_requests": s.total_requests,
                    "total_rate_limits": s.total_rate_limits,
                    "total_errors": s.total_errors,
                }
                for s in self._states
            ],
            "agent_affinity": {
                agent: (slot % len(self._states)) + 1 if self._states else None
                for agent, slot in {**EXPLICIT_AFFINITY, **self._dynamic_affinity}.items()
            },
        }


# ── Module-level singleton ────────────────────────────────────────────────
key_pool = KeyPool()


def init_key_pool(keys: List[str]) -> KeyPool:
    """Configure the shared pool. Called once from app startup / config load."""
    key_pool.configure(keys)
    return key_pool
