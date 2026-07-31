"""A seeded plan must actually grant the features it advertises.

The bug this pins was a silent one. ``check_feature_access`` denies any name it
does not find (``features.get(name, False)``), while the seeded plans spelled
two of those names differently — ``image_generation`` instead of ``image_gen``,
``code_agent`` instead of ``code_executions`` — and omitted ``chat_messages``
entirely. Nothing errored. Every non-admin plan, including the paid ones, just
returned HTTP 402 for chat, image generation and code execution, and only the
Enterprise plan escaped because ``is_admin_plan`` bypasses the lookup before the
dict is ever read.

Two spellings of the same concept cannot be caught by reading either side alone,
so these tests compare the two sides against each other rather than against a
hand-written list that would drift in the same way.
"""

import pytest

from app.services.seed_plans import DEFAULT_PLANS, LEGACY_FEATURE_KEYS, _repair_feature_keys
from app.services.subscription_service import (
    FEATURE_PATH_MAP,
    GATED_FEATURES,
    validate_plan_features,
)


def _plan(name: str) -> dict:
    return next(p for p in DEFAULT_PLANS if p["name"] == name)


# ── The drift guard ───────────────────────────────────────────

@pytest.mark.parametrize("plan", DEFAULT_PLANS, ids=lambda p: p["name"])
def test_seeded_plan_declares_every_gated_feature(plan):
    """Every name the gate can look up must be present in every plan.

    A missing key is not a missing feature — it is a *denied* feature, because
    the gate defaults to False.
    """
    missing = validate_plan_features(plan["features"])
    assert not missing, (
        f"plan '{plan['name']}' omits {missing}; check_feature_access() denies "
        f"unknown names, so these would 402 for every user on this plan"
    )


@pytest.mark.parametrize("plan", DEFAULT_PLANS, ids=lambda p: p["name"])
def test_seeded_plan_carries_no_legacy_spellings(plan):
    """The old names are inert — present in the dict but never read."""
    stale = sorted(set(plan["features"]) & set(LEGACY_FEATURE_KEYS))
    assert not stale, (
        f"plan '{plan['name']}' still uses legacy key(s) {stale}; the gate reads "
        f"{[LEGACY_FEATURE_KEYS[k] for k in stale]}"
    )


def test_gated_features_tracks_the_path_map():
    """GATED_FEATURES is the authority; it must not be a stale hand-copy."""
    assert GATED_FEATURES == frozenset(FEATURE_PATH_MAP.values())


# ── What the plans actually entitle ───────────────────────────

def test_paid_plans_grant_the_features_they_charge_for():
    """Regression: Starter/Pro/Max returned 402 for chat, images and code."""
    for name in ("Starter", "Pro", "Max"):
        features = _plan(name)["features"]
        for feature in ("chat_messages", "image_gen", "code_executions"):
            assert features.get(feature) is True, (
                f"paying '{name}' customers cannot use '{feature}'"
            )


def test_free_plan_grants_chat_but_not_premium_generation():
    """Free is limited by quota, not by having chat switched off entirely."""
    features = _plan("Free")["features"]
    assert features.get("chat_messages") is True, "Free plan cannot chat at all"
    assert features.get("image_gen") is False
    assert features.get("code_executions") is False


def test_free_plan_limits_use_canonical_limit_keys():
    """The limits dict is what makes Free actually free — 20 messages/day."""
    limits = _plan("Free")["limits"]
    assert limits["chat_messages_per_day"] == 20
    assert limits["image_gen_per_month"] == 0
    assert limits["code_executions_per_month"] == 0


# ── The repair path for installs that already have plans ──────

class _FakePlan:
    def __init__(self, name, features):
        self.name = name
        self.features = features


class _FakeQuery:
    def __init__(self, plans):
        self._plans = plans

    def all(self):
        return self._plans


class _FakeSession:
    """Just enough Session to drive _repair_feature_keys without a database."""

    def __init__(self, plans):
        self._plans = plans
        self.committed = False

    def query(self, _model):
        return _FakeQuery(self._plans)

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_repair_renames_legacy_keys_on_existing_rows():
    """seed_plans() returns early once rows exist, so constants alone never
    reached a deployed install. The repair is what fixes those."""
    plan = _FakePlan("Pro", {
        "deep_research": True,
        "image_generation": True,
        "code_agent": True,
        "rag": True,
    })
    db = _FakeSession([plan])

    _repair_feature_keys(db)

    assert db.committed
    assert plan.features["image_gen"] is True
    assert plan.features["code_executions"] is True
    assert "image_generation" not in plan.features
    assert "code_agent" not in plan.features
    assert not validate_plan_features(plan.features)


def test_repair_preserves_a_denied_feature():
    """Free must not silently gain image generation from the rename."""
    plan = _FakePlan("Free", {
        "image_generation": False,
        "code_agent": False,
        "rag": True,
    })

    _repair_feature_keys(_FakeSession([plan]))

    assert plan.features["image_gen"] is False, "Free plan was upgraded by the repair"
    assert plan.features["code_executions"] is False


def test_repair_reassigns_rather_than_mutating_in_place():
    """features is a plain JSONB column, not MutableDict — SQLAlchemy only
    notices the change if the attribute is reassigned to a new object."""
    original = {"image_generation": True, "rag": True}
    plan = _FakePlan("Pro", original)

    _repair_feature_keys(_FakeSession([plan]))

    assert plan.features is not original, (
        "features was edited in place; the UPDATE would never be emitted"
    )
    assert original == {"image_generation": True, "rag": True}, "caller's dict mutated"


def test_repair_is_idempotent():
    """Startup runs this every boot; a second pass must be a no-op."""
    plan = _FakePlan("Pro", dict(_plan("Pro")["features"]))
    db = _FakeSession([plan])

    _repair_feature_keys(db)

    assert not db.committed, "already-correct plans were rewritten"


def test_repair_survives_a_null_features_column():
    """features is nullable in practice on hand-edited rows."""
    plan = _FakePlan("Broken", None)

    _repair_feature_keys(_FakeSession([plan]))

    assert not validate_plan_features(plan.features)


# ── What actually gets metered ────────────────────────────────
#
# Feature resolution is a substring match on the path, so `/chat/` matches
# `GET /chat/sessions` exactly as well as `POST /chat/stream`. Reads were
# therefore gated *and* recorded: opening the app spent generation quota, and a
# user who hit their daily limit could no longer read their own history.

import asyncio

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.middleware import usage_tracker
from app.middleware.usage_tracker import UNMETERED_METHODS, UsageTrackingMiddleware


def _metering_probe(monkeypatch):
    """A live middleware whose DB gate is replaced by a call recorder."""
    gate_calls: list[str] = []
    recorded: list[tuple[str, str]] = []

    def fake_gate(auth_header, feature):
        gate_calls.append(feature)
        return {"verdict": "allowed", "user_id": "u1", "remaining": 5, "limit": 20}

    def fake_record(user_id, feature):
        recorded.append((user_id, feature))

    monkeypatch.setattr(usage_tracker, "_check_entitlements", fake_gate)
    monkeypatch.setattr(usage_tracker, "_record_usage_sync", fake_record)

    app = Starlette(routes=[
        Route("/chat/sessions", lambda r: PlainTextResponse("ok"),
              methods=["GET", "POST", "DELETE"]),
        Route("/chat/stream", lambda r: PlainTextResponse("ok"), methods=["POST"]),
    ])
    app.add_middleware(UsageTrackingMiddleware)
    return app, gate_calls, recorded


async def _request(app, method, path):
    """Drive one request through the real middleware stack."""
    body_sent = False
    done = asyncio.Event()
    status: dict = {}

    async def receive():
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await done.wait()
        return {"type": "http.disconnect"}

    async def send(message):
        if message["type"] == "http.response.start":
            status["code"] = message["status"]
        elif message["type"] == "http.response.body" and not message.get("more_body"):
            done.set()

    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1", "method": method, "scheme": "http",
        "path": path, "raw_path": path.encode(), "query_string": b"",
        "root_path": "",
        "headers": [(b"host", b"testserver"), (b"authorization", b"Bearer t")],
        "client": ("testclient", 50000), "server": ("testserver", 80),
    }
    await app(scope, receive, send)
    return status.get("code")


async def test_reading_chat_history_costs_no_quota(monkeypatch):
    app, gate_calls, recorded = _metering_probe(monkeypatch)

    await _request(app, "GET", "/chat/sessions")

    assert gate_calls == [], "a read was gated against the chat_messages feature"
    assert recorded == [], "a read consumed generation quota"


async def test_generating_a_message_is_metered(monkeypatch):
    app, gate_calls, recorded = _metering_probe(monkeypatch)

    await _request(app, "POST", "/chat/stream")

    assert gate_calls == ["chat_messages"], "the generator was not gated"
    assert recorded == [("u1", "chat_messages")], "the generator was not billed"


async def test_state_changing_non_get_is_still_metered(monkeypatch):
    """The skip is by method, so only safe methods are exempt."""
    app, gate_calls, _ = _metering_probe(monkeypatch)

    await _request(app, "DELETE", "/chat/sessions")

    assert gate_calls == ["chat_messages"]


def test_unmetered_methods_are_only_safe_ones():
    """Widening this set past the safe methods would give away paid generation.

    Every metered generator in the app is a POST; nothing that invokes a model
    is reachable by GET/HEAD/OPTIONS.
    """
    assert UNMETERED_METHODS == frozenset({"GET", "HEAD", "OPTIONS"})
