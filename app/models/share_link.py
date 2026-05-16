import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.models import Base

class DoctorShare(Base):
    __tablename__ = "doctor_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    share_token = Column(String, unique=True, index=True, nullable=False)
    document_ids = Column(JSONB, nullable=False) # list of shared document UUIDs
    
    expires_at = Column(DateTime(timezone=True), nullable=False)
    access_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
