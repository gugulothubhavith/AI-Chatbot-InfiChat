import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from app.models.types import UUID, JSONB
from datetime import datetime, timezone
from app.database.db import Base
from sqlalchemy.orm import relationship

class PersonalAccessToken(Base):
    __tablename__ = "personal_access_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String, nullable=False)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    prefix = Column(String, nullable=False)
    scopes = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", backref="personal_access_tokens")
