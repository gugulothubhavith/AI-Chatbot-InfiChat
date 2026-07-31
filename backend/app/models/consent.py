"""Consent audit model — append-only history of user consent events.

Withdrawal is recorded as a new row, never as an update to an existing row.
Privacy regulations (GDPR Art. 7(3), UK-GDPR, CCPA/CPRA, India DPDP 2023)
require the ability to demonstrate consent was given, and when it was
withdrawn. This table provides that trail.
"""

from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from app.models.types import UUID
from app.database.db import Base
from datetime import datetime, timezone


class ConsentEvent(Base):
    __tablename__ = "consent_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event type: 'accept', 'withdraw', 're-consent'
    event_type = Column(String, nullable=False)

    # Versions accepted at this event (NULL for withdrawal events)
    terms_version = Column(String, nullable=True)
    privacy_version = Column(String, nullable=True)

    # Audit metadata captured at consent time
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="consent_events")
