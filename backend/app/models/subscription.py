"""Subscription plans, user subscriptions, and usage tracking models."""

from sqlalchemy import Column, String, DateTime, Enum, Boolean, Integer, ForeignKey
from app.models.types import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime, timezone
import uuid
import enum


class PlanStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    price_monthly = Column(Integer, nullable=False, default=0)  # In INR
    price_annual = Column(Integer, nullable=False, default=0)   # In INR

    # Feature limits as JSON — controls ALL feature quotas
    limits = Column(JSONB, nullable=False, default=dict)
    # Structure:
    # {
    #   "chat_messages_per_day": 20,
    #   "chat_tokens_per_day": 10000,
    #   "deep_research_per_month": 5,
    #   "deep_thinking_per_month": 10,
    #   "image_gen_per_month": 5,
    #   "code_executions_per_month": 10,
    #   "rag_documents": 3,
    #   "max_tokens_per_response": 1024,
    #   "max_context_length": 4096
    # }

    # Feature availability flags
    features = Column(JSONB, nullable=False, default=dict)
    # Structure:
    # {
    #   "deep_research": true,
    #   "deep_thinking": true,
    #   "image_generation": true,
    #   "code_agent": true,
    #   "rag": true,
    #   "voice": true,
    #   "web_search": true
    # }

    is_active = Column(Boolean, default=True)
    is_admin_plan = Column(Boolean, default=False)  # Special unlimited plan, admin-assign only
    is_public = Column(Boolean, default=True)       # Whether users can subscribe directly
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    subscriptions = relationship("UserSubscription", back_populates="plan")


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    start_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_date = Column(DateTime, nullable=True)
    is_admin_assigned = Column(Boolean, default=False)  # True if admin force-assigned
    auto_renew = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="subscription")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")


class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature = Column(String, nullable=False, index=True)
    tokens_used = Column(Integer, default=0)
    requests_count = Column(Integer, default=1)
    date = Column(String, nullable=False, index=True)    # YYYY-MM-DD
    month = Column(String, nullable=False, index=True)   # YYYY-MM
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
