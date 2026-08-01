from sqlalchemy import Column, String, DateTime, Enum, Boolean, ForeignKey
from app.models.types import UUID, JSONB
from typing import Optional
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime, timezone
import uuid
import enum

class RoleEnum(str, enum.Enum):
    admin = "admin"
    user = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    role = Column(Enum(RoleEnum), default=RoleEnum.user)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    avatar_url = Column(String, nullable=True)
    settings = Column(JSONB, nullable=True, default=dict)
    
    # TOTP / MFA
    totp_secret = Column(String, nullable=True) # Base32 generic secret
    is_mfa_enabled = Column(Boolean, default=False)

    # ── Consent (Terms of Service / Privacy Policy) ─────────────────────
    # Current accepted state. The append-only history lives in
    # ``consent_events``; these columns are the fast path the request-time
    # gate in app/core/deps.py reads on every protected request.
    # NULL means "never consented" — every pre-existing row after the
    # migration, which is why the gate treats NULL as stale rather than
    # grandfathering it.
    terms_accepted_version = Column(String, nullable=True)
    privacy_accepted_version = Column(String, nullable=True)
    consent_accepted_at = Column(DateTime, nullable=True)
    consent_ip = Column(String, nullable=True)
    consent_user_agent = Column(String, nullable=True)

    organization = relationship("Organization", back_populates="users")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    snippets = relationship("Snippet", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    consent_events = relationship("ConsentEvent", back_populates="user", cascade="all, delete-orphan")

    # Every child collection reachable from a User needs a delete rule declared
    # here, or `DELETE /auth/me` fails and the right to erasure (GDPR Art. 17,
    # DPDP s.12) is unavailable in practice. The failure mode is not a silent
    # orphan — SQLAlchemy's default is to NULL the child's FK, and these columns
    # are `nullable=False`, so the flush raises NotNullViolation and the account
    # survives a reported deletion.
    #
    # `passive_deletes=True` on the first two because their FKs already carry
    # `ondelete="CASCADE"`: the database removes the rows, so there is no reason
    # to load them into the session first. `files` has no DB-level rule (its FK
    # is NO ACTION), so SQLAlchemy must issue the child deletes itself — the same
    # arrangement chat_sessions, memories and snippets above already rely on.
    personal_access_tokens = relationship(
        "PersonalAccessToken", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    subscription = relationship(
        "UserSubscription", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    files = relationship("File", cascade="all, delete-orphan")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    refresh_token_hash = Column(String, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="sessions")