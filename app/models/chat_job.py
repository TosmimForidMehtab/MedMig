import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.models import Base

class ChatJob(Base):
    __tablename__ = "chat_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    
    status = Column(String, default="pending") # pending, processing, completed, failed
    input_text = Column(Text, nullable=True)
    input_file_path = Column(String, nullable=True)
    
    response_text = Column(Text, nullable=True)
    response_audio_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
