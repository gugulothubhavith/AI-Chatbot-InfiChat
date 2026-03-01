from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database.db import Base
from datetime import datetime, timezone
import uuid

class File(Base):
    __tablename__ = "files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(String, nullable=False)
    file_type = Column(String)
    size = Column(String)
    path = Column(String)
    extra_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))