"""Database compatibility tests — validates that all models work with SQLite."""

from app.database.db import Base, SessionLocal, engine
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.subscription import SubscriptionPlan, UserSubscription, UsageRecord


def test_create_user(db_session):
    """Create a user and verify it persists."""
    user = User(
        email="dbuser@test.com",
        username="dbuser",
        hashed_password="hashed_pwd",
    )
    db_session.add(user)
    db_session.commit()

    saved = db_session.query(User).filter(User.email == "dbuser@test.com").first()
    assert saved is not None
    assert saved.username == "dbuser"
    assert saved.is_active is True


def test_create_chat_session(db_session):
    """Create a chat session tied to a user."""
    user = User(email="chatuser@test.com", username="chatuser", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    session = ChatSession(user_id=user.id)
    db_session.add(session)
    db_session.commit()

    msg = ChatMessage(session_id=session.id, role="user", content="Hello world")
    db_session.add(msg)
    db_session.commit()

    loaded = db_session.query(ChatMessage).filter(ChatMessage.session_id == session.id).first()
    assert loaded is not None
    assert loaded.content == "Hello world"
    assert loaded.role == "user"


def test_create_subscription_plan(db_session):
    """Create a subscription plan and verify limits JSON storage."""
    plan = SubscriptionPlan(
        name="Test Plan",
        description="A test plan",
        price_monthly=499,
        features={"deep_research": True, "image_generation": True},
        limits={"chat_messages_per_day": 100, "deep_research_per_month": 50},
        is_active=True,
        is_admin_plan=False,
    )
    db_session.add(plan)
    db_session.commit()

    saved = db_session.query(SubscriptionPlan).filter(SubscriptionPlan.name == "Test Plan").first()
    assert saved is not None
    assert saved.price_monthly == 499
    assert saved.features["deep_research"] is True
    assert saved.limits["chat_messages_per_day"] == 100


def test_track_usage(db_session):
    """Create and query usage records."""
    user = User(email="usageuser@test.com", username="usageuser", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    record = UsageRecord(
        user_id=user.id,
        feature="chat_messages",
        tokens_used=150,
        requests_count=1,
        date="2026-07-08",
        month="2026-07",
    )
    db_session.add(record)
    db_session.commit()

    from sqlalchemy import func
    total = db_session.query(func.sum(UsageRecord.requests_count)).filter(
        UsageRecord.user_id == user.id,
        UsageRecord.feature == "chat_messages",
    ).scalar() or 0
    assert total >= 1


def test_portable_uuid_generation(db_session):
    """UUID columns should auto-generate for all models."""
    user = User(email="uuidtest@test.com", username="uuidtest", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert len(str(user.id)) > 10  # Should be a valid UUID string

    plan = SubscriptionPlan(
        name="UUID Test Plan",
        price_monthly=0,
        features={},
        limits={},
    )
    db_session.add(plan)
    db_session.commit()
    assert plan.id is not None
