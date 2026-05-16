import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, func
from sqlalchemy.dialects.postgresql import UUID
from app.models import Base

class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    owner_type = Column(String, nullable=False) # 'user' or 'family_member'
    
    metric_type = Column(String, nullable=False) # e.g., 'blood_glucose', 'systolic_bp'
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    source_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
