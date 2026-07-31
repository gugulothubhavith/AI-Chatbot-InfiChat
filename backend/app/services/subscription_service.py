"""Subscription plan management, user subscription assignment, and usage tracking service."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.subscription import (
    SubscriptionPlan, UserSubscription, UsageRecord, SubscriptionStatus,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Plan Management
# ═══════════════════════════════════════════════════════════════

def get_available_plans(db: Session, include_admin_plan: bool = False):
    """Get all public subscription plans."""
    query = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.is_active == True,
        SubscriptionPlan.is_public == True,
    )
    if not include_admin_plan:
        query = query.filter(SubscriptionPlan.is_admin_plan == False)
    return query.order_by(SubscriptionPlan.sort_order).all()


def get_plan_by_id(plan_id: str, db: Session) -> Optional[SubscriptionPlan]:
    """Get a single plan by ID."""
    import uuid
    try:
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == uuid.UUID(plan_id)
        ).first()
    except (ValueError, AttributeError):
        return db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id
        ).first()


def create_plan(db: Session, **kwargs) -> SubscriptionPlan:
    """Create a new subscription plan."""
    plan = SubscriptionPlan(**kwargs)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(plan_id: str, db: Session, **kwargs) -> Optional[SubscriptionPlan]:
    """Update an existing plan."""
    plan = get_plan_by_id(plan_id, db)
    if not plan:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(plan_id: str, db: Session) -> bool:
    """Delete a plan."""
    plan = get_plan_by_id(plan_id, db)
    if plan:
        db.delete(plan)
        db.commit()
        return True
    return False


# ═══════════════════════════════════════════════════════════════
# User Subscription
# ═══════════════════════════════════════════════════════════════

def get_user_subscription(user_id: str, db: Session) -> dict:
    """Get user's active subscription with plan details.

    Returns a dict with:
        - plan: SubscriptionPlan object (or Free plan if none)
        - is_active: bool
        - is_admin_assigned: bool
        - start_date: datetime or None
        - end_date: datetime or None
    """
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        uid = user_id

    sub = db.query(UserSubscription).filter(
        UserSubscription.user_id == uid,
        UserSubscription.status == SubscriptionStatus.ACTIVE,
        (UserSubscription.end_date.is_(None)) | (UserSubscription.end_date >= datetime.now(timezone.utc)),
    ).first()

    # If active subscription exists
    if sub and sub.plan:
        return {
            "plan": sub.plan,
            "is_active": sub.status == SubscriptionStatus.ACTIVE,
            "is_admin_assigned": sub.is_admin_assigned,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
        }

    # No active subscription — return default Free plan
    free_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.price_monthly == 0,
        SubscriptionPlan.is_active == True,
        SubscriptionPlan.is_admin_plan == False,
    ).order_by(SubscriptionPlan.sort_order).first()

    return {
        "plan": free_plan,
        "is_active": True,
        "is_admin_assigned": False,
        "start_date": None,
        "end_date": None,
    }


def assign_plan_to_user(
    user_id: str, plan_id: str, db: Session, admin_assigned: bool = False
) -> UserSubscription:
    """Assign or change a user's subscription plan."""
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        uid = user_id
    try:
        pid = uuid.UUID(plan_id)
    except (ValueError, AttributeError):
        pid = plan_id

    # Deactivate existing active subscriptions
    existing = db.query(UserSubscription).filter(
        UserSubscription.user_id == uid,
        UserSubscription.status == SubscriptionStatus.ACTIVE,
    ).all()
    for sub in existing:
        sub.status = SubscriptionStatus.CANCELLED

    # Create new subscription
    new_sub = UserSubscription(
        user_id=uid,
        plan_id=pid,
        status=SubscriptionStatus.ACTIVE,
        is_admin_assigned=admin_assigned,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


# ═══════════════════════════════════════════════════════════════
# Feature Access & Usage Limits
# ═══════════════════════════════════════════════════════════════

# Map API paths to feature names
FEATURE_PATH_MAP = {
    "/chat/": "chat_messages",
    "/research/": "deep_research",
    "/thinking/": "deep_thinking",
    "/image/": "image_gen",
    "/code/": "code_executions",
    "/rag/": "rag",
    # Manual web search only. Auto-triggered search runs inside /chat/ and is
    # deliberately NOT metered here — it is charged as a normal chat message,
    # never against the web_search quota. The web_search quota is consumed ONLY
    # when the user explicitly enables the toggle and hits this endpoint.
    "/web_search/": "web_search",
}

# The canonical set of feature flags a plan's ``features`` dict is keyed by.
#
# This is the authority, and it is derived rather than hand-written: every value
# in FEATURE_PATH_MAP is a name that check_feature_access() will look up, and
# that function denies by default (``features.get(name, False)``). A plan whose
# features dict is missing one of these names therefore *blocks* that feature,
# silently, for every user on the plan — which is exactly how the seeded plans
# came to spell these "image_generation" and "code_agent" while the gate looked
# up "image_gen" and "code_executions". Import this instead of retyping the
# names; see validate_plan_features() below.
GATED_FEATURES = frozenset(FEATURE_PATH_MAP.values())


def validate_plan_features(features: dict, *, plan_name: str = "plan") -> list[str]:
    """Return the canonical feature names missing from ``features``.

    Empty list means the dict can be gated correctly. Callers that seed or
    repair plans use this to fail loudly instead of shipping a plan that returns
    HTTP 402 for a feature the customer is paying for.
    """
    return sorted(name for name in GATED_FEATURES if name not in (features or {}))

# Daily features vs monthly features
DAILY_FEATURES = {"chat_messages", "chat_tokens", "web_search"}
MONTHLY_FEATURES = {"deep_research", "deep_thinking", "image_gen", "code_executions"}

# Map features to their limit keys in the plan
FEATURE_LIMIT_KEY = {
    "chat_messages": "chat_messages_per_day",
    "chat_tokens": "chat_tokens_per_day",
    "deep_research": "deep_research_per_month",
    "deep_thinking": "deep_thinking_per_month",
    "image_gen": "image_gen_per_month",
    "code_executions": "code_executions_per_month",
    "rag": "rag_documents",
    "web_search": "web_search_per_day",
}


def get_feature_from_path(path: str) -> Optional[str]:
    """Determine feature name from API path."""
    path_lower = path.lower()
    for route, feature in FEATURE_PATH_MAP.items():
        if route in path_lower:
            return feature
    return None


def check_feature_access(user_id: str, feature: str, db: Session) -> bool:
    """Check if user has access to a feature based on their plan.

    Returns True when no plan is configured (fresh installation) to avoid
    blocking all access before plans are seeded.
    """
    sub_info = get_user_subscription(user_id, db)
    plan = sub_info["plan"]

    if not plan:
        return True  # Allow when no plans configured yet (fresh install)

    # Admin unlimited plan has everything
    if plan.is_admin_plan or getattr(plan, "is_admin_plan", False):
        return True

    # Check feature flags
    features = plan.features or {}
    return features.get(feature, False)


def check_usage_limit(user_id: str, feature: str, db: Session) -> tuple:
    """Check if user has exceeded usage limit.

    Returns (allowed: bool, remaining: int, limit: int).
    """
    sub_info = get_user_subscription(user_id, db)
    plan = sub_info["plan"]

    if not plan:
        return True, 9999, 9999  # Allow when no plans configured yet (fresh install)

    # Admin unlimited plan = no limits
    if plan.is_admin_plan:
        return True, 999999, 999999

    limits = plan.limits or {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # Determine limit key
    limit_key = FEATURE_LIMIT_KEY.get(feature)
    if not limit_key:
        return True, 1, 1  # Unknown feature, allow

    limit = limits.get(limit_key, 0)
    if limit <= 0:
        return True, 1, 1  # No limit set

    # Determine period
    if feature in DAILY_FEATURES:
        period_field = UsageRecord.date
        period = today
    elif feature in MONTHLY_FEATURES:
        period_field = UsageRecord.month
        period = this_month
    else:
        return True, 1, 1

    # Count current usage
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        uid = user_id

    usage = db.query(func.sum(UsageRecord.requests_count)).filter(
        UsageRecord.user_id == uid,
        UsageRecord.feature == feature,
        period_field == period,
    ).scalar() or 0

    remaining = max(0, limit - usage)
    return usage < limit, remaining, limit


def record_usage(user_id: str, feature: str, tokens: int = 0, db: Session = None):
    """Record usage for a user. Creates its own session if db not provided."""
    close_session = False
    if db is None:
        from app.database.db import SessionLocal
        db = SessionLocal()
        close_session = True

    try:
        import uuid
        try:
            uid = uuid.UUID(user_id)
        except (ValueError, AttributeError):
            uid = user_id

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        this_month = datetime.now(timezone.utc).strftime("%Y-%m")

        record = UsageRecord(
            user_id=uid,
            feature=feature,
            tokens_used=tokens,
            requests_count=1,
            date=today,
            month=this_month,
        )
        db.add(record)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        if db:
            db.rollback()
    finally:
        if close_session:
            db.close()


def get_user_usage_summary(user_id: str, db: Session) -> dict:
    """Get usage summary for a user across all features for the current month."""
    import uuid
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, AttributeError):
        uid = user_id

    this_month = datetime.now(timezone.utc).strftime("%Y-%m")

    usage = db.query(
        UsageRecord.feature,
        func.sum(UsageRecord.requests_count).label("count"),
        func.sum(UsageRecord.tokens_used).label("tokens"),
    ).filter(
        UsageRecord.user_id == uid,
        UsageRecord.month == this_month,
    ).group_by(UsageRecord.feature).all()

    return {
        row.feature: {"count": int(row.count), "tokens": int(row.tokens or 0)}
        for row in usage
    }


def get_all_users_usage(db: Session) -> list:
    """Get platform-wide usage stats for admin."""
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")

    usage = db.query(
        UsageRecord.feature,
        func.sum(UsageRecord.requests_count).label("count"),
        func.sum(UsageRecord.tokens_used).label("tokens"),
        func.count(func.distinct(UsageRecord.user_id)).label("users"),
    ).filter(
        UsageRecord.month == this_month,
    ).group_by(UsageRecord.feature).all()

    return [
        {
            "feature": u.feature,
            "requests": int(u.count),
            "tokens": int(u.tokens or 0),
            "active_users": int(u.users),
        }
        for u in usage
    ]
