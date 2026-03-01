from sqlalchemy import Column, String, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from typing import Optional
from sqlalchemy.orm import relationship
from app.database.db import Base
from datetime import datetime
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
    avatar_url = Column(String, nullable=True)
    settings = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    snippets = relationship("Snippet", back_populates="user", cascade="all, delete-orphan")