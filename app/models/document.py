import uuid
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.models import Base
from app.config import settings

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # owner_id can point to user or family_member, so we use a UUID but handle owner_type in logic
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    owner_type = Column(String, nullable=False) # 'user' or 'family_member'
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String, nullable=False) # prescription, lab_report, etc.
    
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    
    document_date = Column(Date, nullable=True)
    doctor_details = Column(JSONB, nullable=True)
    hospital_details = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)
    content_text = Column(Text, nullable=True)
    embedding = Column(Vector(settings.EMBEDDING_DIM), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
