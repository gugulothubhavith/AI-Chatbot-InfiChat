"""Per-user concurrency caps for expensive pipelines.

Rate limits bound how many requests a user may *start* per minute. They do not
bound how many can be **in flight at once**, and the expensive pipelines here
(deep research, the code squad) run for minutes and hold several key-pool
leases for their whole life. Ten deep-research runs launched inside one minute
sit comfortably under a 10/minute rate limit while occupying every lease in the
pool, which stalls every other user.

This module caps concurrent runs per user and fails fast: a user at their cap
gets an immediate 429 telling them what to wait for, rather than a request that
hangs until something upstream times out.

Scope: the counters live in this process. Under multiple uvicorn workers the
effective cap is ``limit x workers``, since a user's requests may land on
different workers. That still bounds one user's share — and the key pool bounds
total NVIDIA usage globally regardless — but it is not a cluster-wide cap. If
that becomes necessary, back ``_active`` with a Redis counter keyed the same
way; the call sites do not change.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import Depends, HTTPException

from app.core.deps import get_current_user

logger = logging.getLogger(__name__)


class ConcurrencyLimitExceeded(Exception):
    """Raised when a user already has `limit` runs of `name` in flight."""

    def __init__(self, name: str, limit: int) -> None:
        self.name = name
        self.limit = limit
        super().__init__(
            f"You already have {limit} {name} request(s) running. "
            f"Wait for one to finish before starting another."
        )


class UserConcurrencyLimiter:
    """Caps how many runs of one pipeline a single user may have in flight.

    Counts are kept explicitly rather than with a per-user ``asyncio.Semaphore``
    so that a user's entry can be dropped the moment their last run finishes.
    A dict of semaphores would grow one entry per user seen and never shrink.
    """

    def __init__(self, name: str, limit: int) -> None:
        if limit < 1:
            raise ValueError(f"{name}: limit must be >= 1, got {limit}")
        self._name = name
        self._limit = limit
        self._active: dict[str, int] = {}
        self._lock = asyncio.Lock()

    @property
    def limit(self) -> int:
        return self._limit

    def active_for(self, user_id: str) -> int:
        """Runs currently in flight for this user. For diagnostics only."""
        return self._active.get(str(user_id), 0)

    @asynccontextmanager
    async def slot(self, user_id: str):
        """Hold a slot for the duration of the block.

        Raises ConcurrencyLimitExceeded immediately if the user is at their cap.
        The slot is always released, including when the body raises or the
        client disconnects and the task is cancelled.
        """
        key = str(user_id)

        async with self._lock:
            current = self._active.get(key, 0)
            if current >= self._limit:
                logger.info(
                    "%s: user %s at concurrency cap (%d)", self._name, key, self._limit
                )
                raise ConcurrencyLimitExceeded(self._name, self._limit)
            self._active[key] = current + 1

        try:
            yield
        finally:
            async with self._lock:
                remaining = self._active.get(key, 1) - 1
                if remaining > 0:
                    self._active[key] = remaining
                else:
                    # Drop the key entirely so the map stays proportional to
                    # users with work in flight, not to users ever seen.
                    self._active.pop(key, None)


# Deep research fans out to many agents and runs for minutes, so one at a time
# per user is the honest cap. The code squad is shorter-lived; two lets someone
# work on a second file without waiting.
deep_research_limiter = UserConcurrencyLimiter("deep research", limit=1)
code_agent_limiter = UserConcurrencyLimiter("code agent", limit=2)


def limit_concurrency(limiter: UserConcurrencyLimiter) -> Callable:
    """Build a FastAPI dependency that holds a slot for the whole request.

    Deliberately a dependency with ``yield`` rather than a manual
    acquire/release around the handler body. FastAPI keeps the request's
    dependency exit stack open across ``await response(...)`` (see
    ``fastapi/routing.py``, ``fastapi_inner_astack``), so for a
    ``StreamingResponse`` the slot is held for the life of the *stream* — which
    is what deep research needs, since the pipeline runs after the handler has
    already returned. Releasing by hand inside the SSE producer would instead
    leak a slot on any path where the generator is closed before it ever
    starts, and a leaked slot means that user is refused service permanently.

    Because the dependency is resolved before the handler runs, a user at their
    cap gets a plain 429 and no stream is ever opened.
    """

    async def dependency(user=Depends(get_current_user)) -> AsyncIterator[None]:
        try:
            async with limiter.slot(str(user.id)):
                yield
        except ConcurrencyLimitExceeded as exc:
            raise HTTPException(
                status_code=429,
                detail=str(exc),
                headers={"Retry-After": "30"},
            ) from exc

    return dependency
