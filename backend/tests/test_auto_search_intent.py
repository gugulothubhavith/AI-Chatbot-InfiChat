"""Unit tests for auto web-search intent detection and abuse ceiling.

These cover the pure-heuristic decision paths (no model, no live services) plus
the fail-closed behaviour of the per-user daily cap. The Tier-2 classifier is
exercised via monkeypatched fakes so no network/model call is made.
"""

import os

# Minimal env so `app.core.config` imports cleanly outside the app.
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

import pytest

from app.services.web_search import intent


# ── Tier 1: positive heuristics fire without a model call ──────────────────
@pytest.mark.parametrize(
    "prompt",
    [
        "what is the latest news on AI",
        "who is the current president of France",
        "price of bitcoin today",
        "weather in Tokyo tomorrow",
        "https://example.com",
        "what happened in the 2024 elections",
    ],
)
def test_positive_heuristics(prompt):
    r = intent._heuristic(prompt)
    assert r is not None
    assert r.should_search is True
    assert r.reason == intent.REASON_POSITIVE
    assert r.used_model is False


# ── Tier 0: negative heuristics short-circuit to no-search ─────────────────
@pytest.mark.parametrize(
    "prompt",
    [
        "write me a poem about the sea",
        "refactor this python function",
        "hi there",
        "translate this paragraph",
    ],
)
def test_negative_heuristics(prompt):
    r = intent._heuristic(prompt)
    assert r is not None
    assert r.should_search is False
    assert r.reason == intent.REASON_NEGATIVE


# ── Genuinely ambiguous prompts defer to Tier 2 (heuristic returns None) ───
@pytest.mark.parametrize(
    "prompt",
    [
        "tell me about the history of Rome",
        "explain how a hashmap works",
    ],
)
def test_ambiguous_defers_to_model(prompt):
    assert intent._heuristic(prompt) is None


@pytest.mark.asyncio
async def test_should_auto_search_disabled(monkeypatch):
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_ENABLED", False)
    r = await intent.should_auto_search("what is the latest news")
    assert r.should_search is False
    assert r.reason == intent.REASON_DISABLED


@pytest.mark.asyncio
async def test_should_auto_search_empty_prompt():
    r = await intent.should_auto_search("   ")
    assert r.should_search is False


@pytest.mark.asyncio
async def test_classifier_yes_is_cached(monkeypatch):
    """Ambiguous prompt → model says YES → verdict cached, no second call."""
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_ENABLED", True)

    calls = {"n": 0}

    async def fake_call_llm(*args, **kwargs):
        calls["n"] += 1
        return {"choices": [{"message": {"content": "YES"}}]}

    # No cache hit, capture the set.
    store = {}
    monkeypatch.setattr(intent.redis_client, "get", lambda k: store.get(k))
    monkeypatch.setattr(intent.redis_client, "setex", lambda k, ttl, v: store.__setitem__(k, v))

    import app.services.llm_router as llm_router
    monkeypatch.setattr(llm_router, "call_llm", fake_call_llm)

    r = await intent.should_auto_search("tell me about the history of Rome")
    assert r.should_search is True
    assert r.reason == intent.REASON_CLASSIFIER_YES
    assert calls["n"] == 1

    # Second identical call served from cache — no new model call.
    r2 = await intent.should_auto_search("tell me about the history of Rome")
    assert r2.should_search is True
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_classifier_failsafe_on_error(monkeypatch):
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_ENABLED", True)
    monkeypatch.setattr(intent.redis_client, "get", lambda k: None)
    monkeypatch.setattr(intent.redis_client, "setex", lambda *a, **k: True)

    async def boom(*args, **kwargs):
        raise RuntimeError("model down")

    import app.services.llm_router as llm_router
    monkeypatch.setattr(llm_router, "call_llm", boom)

    r = await intent.should_auto_search("tell me about the history of Rome")
    assert r.should_search is False
    assert r.reason == intent.REASON_ERROR


# ── Abuse ceiling ──────────────────────────────────────────────────────────
def test_cap_fails_closed_when_redis_down(monkeypatch):
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_DAILY_CAP", 50)
    monkeypatch.setattr(intent.redis_client, "ping", lambda: False)
    assert intent.within_auto_search_cap("u1") is False


def test_cap_zero_disables(monkeypatch):
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_DAILY_CAP", 0)
    assert intent.within_auto_search_cap("u1") is False


def test_cap_enforced(monkeypatch):
    monkeypatch.setattr(intent.settings, "AUTO_WEB_SEARCH_DAILY_CAP", 3)
    monkeypatch.setattr(intent.redis_client, "ping", lambda: True)

    counter = {"v": 0}
    monkeypatch.setattr(intent.redis_client, "get", lambda k: counter["v"])

    def _incr(k):
        counter["v"] += 1
        return counter["v"]

    monkeypatch.setattr(intent.redis_client, "incr", _incr)
    monkeypatch.setattr(intent.redis_client, "expire", lambda k, t: True)

    allowed = 0
    for _ in range(5):
        if intent.within_auto_search_cap("u1"):
            allowed += 1
            intent.record_auto_search("u1")
    assert allowed == 3
