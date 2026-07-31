"""Seed default subscription plans into the database."""

import logging
from app.database.db import SessionLocal
from app.models.subscription import SubscriptionPlan
from app.services.subscription_service import GATED_FEATURES, validate_plan_features

logger = logging.getLogger(__name__)

# Feature flags that were once seeded under a different name than the one the
# entitlement gate looks up. check_feature_access() denies unknown names, so a
# plan carrying only the legacy spelling blocks the feature it means to grant.
# Mapping is legacy -> canonical; the stored boolean is carried across unchanged
# so a Free plan's "no image generation" stays "no".
LEGACY_FEATURE_KEYS = {
    "image_generation": "image_gen",
    "code_agent": "code_executions",
}

DEFAULT_PLANS = [
    {
        "name": "Free",
        "description": "Basic access to get started with limited features",
        "price_monthly": 0,
        "price_annual": 0,
        "sort_order": 0,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "chat_messages": True,
            "deep_research": False,
            "deep_thinking": False,
            "image_gen": False,
            "code_executions": False,
            "rag": True,
            "voice": True,
            "web_search": False,
        },
        "limits": {
            "chat_messages_per_day": 20,
            "chat_tokens_per_day": 10000,
            "deep_research_per_month": 0,
            "deep_thinking_per_month": 0,
            "image_gen_per_month": 0,
            "code_executions_per_month": 0,
            "rag_documents": 3,
            "web_search_per_day": 0,
            "max_tokens_per_response": 1024,
            "max_context_length": 4096,
        },
    },
    {
        "name": "Starter",
        "description": "For casual users who need more capabilities",
        "price_monthly": 199,
        "price_annual": 1990,
        "sort_order": 1,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "chat_messages": True,
            "deep_research": True,
            "deep_thinking": True,
            "image_gen": True,
            "code_executions": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 100,
            "chat_tokens_per_day": 50000,
            "deep_research_per_month": 25,
            "deep_thinking_per_month": 50,
            "image_gen_per_month": 25,
            "code_executions_per_month": 50,
            "rag_documents": 10,
            "web_search_per_day": 20,
            "max_tokens_per_response": 2048,
            "max_context_length": 8192,
        },
    },
    {
        "name": "Pro",
        "description": "For power users and professionals",
        "price_monthly": 499,
        "price_annual": 4990,
        "sort_order": 2,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "chat_messages": True,
            "deep_research": True,
            "deep_thinking": True,
            "image_gen": True,
            "code_executions": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 500,
            "chat_tokens_per_day": 250000,
            "deep_research_per_month": 100,
            "deep_thinking_per_month": 200,
            "image_gen_per_month": 100,
            "code_executions_per_month": 200,
            "rag_documents": 50,
            "web_search_per_day": 100,
            "max_tokens_per_response": 4096,
            "max_context_length": 16000,
        },
    },
    {
        "name": "Max",
        "description": "Maximum power for demanding workloads",
        "price_monthly": 999,
        "price_annual": 9990,
        "sort_order": 3,
        "is_admin_plan": False,
        "is_public": True,
        "features": {
            "chat_messages": True,
            "deep_research": True,
            "deep_thinking": True,
            "image_gen": True,
            "code_executions": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 2000,
            "chat_tokens_per_day": 1000000,
            "deep_research_per_month": 500,
            "deep_thinking_per_month": 1000,
            "image_gen_per_month": 500,
            "code_executions_per_month": 1000,
            "rag_documents": 200,
            "web_search_per_day": 500,
            "max_tokens_per_response": 8192,
            "max_context_length": 32000,
        },
    },
    {
        "name": "Enterprise",
        "description": "Unlimited everything — admin assigned only",
        "price_monthly": 0,
        "price_annual": 0,
        "sort_order": 99,
        "is_admin_plan": True,
        "is_public": False,
        "features": {
            "chat_messages": True,
            "deep_research": True,
            "deep_thinking": True,
            "image_gen": True,
            "code_executions": True,
            "rag": True,
            "voice": True,
            "web_search": True,
        },
        "limits": {
            "chat_messages_per_day": 999999,
            "chat_tokens_per_day": 999999999,
            "deep_research_per_month": 999999,
            "deep_thinking_per_month": 999999,
            "image_gen_per_month": 999999,
            "code_executions_per_month": 999999,
            "rag_documents": 999999,
            "web_search_per_day": 999999,
            "max_tokens_per_response": 99999,
            "max_context_length": 999999,
        },
    },
]

# Every plan above must be gateable before it is ever written to a database.
# A typo here is not a cosmetic bug: it makes the affected feature return HTTP
# 402 for every paying customer on that plan, so it should stop the process at
# import time rather than surface as a support ticket.
for _plan in DEFAULT_PLANS:
    _missing = validate_plan_features(_plan["features"], plan_name=_plan["name"])
    if _missing:
        raise RuntimeError(
            f"DEFAULT_PLANS['{_plan['name']}'].features is missing gated feature(s) "
            f"{_missing}. check_feature_access() denies unknown names, so these "
            f"would be blocked for every user on the plan. Canonical names: "
            f"{sorted(GATED_FEATURES)}"
        )
del _plan, _missing


def _repair_feature_keys(db) -> None:
    """Rename drifted feature flags on plans that already exist in the database.

    seed_plans() returns early once any plan row is present, so fixing the
    constants above only ever helped brand-new installs. Every existing
    deployment kept the legacy spellings and kept 402-ing on chat, image
    generation and code execution.

    The repair is deliberately narrow rather than a wholesale overwrite from
    DEFAULT_PLANS: an operator may have tuned a plan through the admin UI, and
    clobbering that would be a second bug. Only two things happen — a legacy key
    is renamed to its canonical name carrying its boolean across, and a missing
    canonical name is added as True. Missing defaults to True because the plan's
    ``limits`` entry is the real control (Free allows 20 chat messages/day); a
    plan that should deny a feature outright sets its limit to 0, which
    check_usage_limit() already enforces.
    """
    repaired = 0
    try:
        for plan in db.query(SubscriptionPlan).all():
            # JSONB is not wrapped in MutableDict, so SQLAlchemy does not see
            # in-place edits. Build a new dict and reassign to mark it dirty.
            original = plan.features or {}
            features = dict(original)

            for legacy, canonical in LEGACY_FEATURE_KEYS.items():
                if legacy in features:
                    # An explicit canonical value always wins over the legacy one.
                    features.setdefault(canonical, features[legacy])
                    del features[legacy]

            for name in GATED_FEATURES:
                features.setdefault(name, True)

            if features != original:
                plan.features = features
                repaired += 1
                logger.info(
                    "Repaired feature flags on plan '%s': %s -> %s",
                    plan.name, sorted(original), sorted(features),
                )

        if repaired:
            db.commit()
            msg = f"Repaired feature flags on {repaired} subscription plan(s)"
            logger.info(msg)
            print(f"[seed] {msg}")
    except Exception as e:
        db.rollback()
        # Never let a repair failure take down startup — the plans are merely
        # left as they were, which is the pre-existing behaviour.
        logger.error(f"Failed to repair plan feature keys: {e}")
        print(f"[seed] feature-key repair FAILED: {e}")


def seed_plans():
    """Insert default plans if they don't already exist, then repair drifted ones."""
    db = SessionLocal()
    try:
        existing = db.query(SubscriptionPlan).count()
        if existing > 0:
            logger.info(f"Plans already seeded ({existing} plans found), skipping insert")
            # Existing installs still need the feature-key repair below — an
            # early return here is what let the drift survive every restart.
            _repair_feature_keys(db)
            return

        for plan_data in DEFAULT_PLANS:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)

        db.commit()
        msg = f"Seeded {len(DEFAULT_PLANS)} default subscription plans"
        logger.info(msg)
        print(f"[seed] {msg}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to seed plans: {e}")
        print(f"[seed] FAILED: {e}")
    finally:
        db.close()
