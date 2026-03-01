from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.db import Base
import uuid
from datetime import datetime

class OTP(Base):
    __tablename__ = "otp_codes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True, nullable=False)
    otp_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    password_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
