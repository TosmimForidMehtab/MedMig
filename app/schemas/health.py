from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class HealthMetricBase(BaseModel):
    owner_id: UUID
    owner_type: str
    metric_type: str
    value: float
    unit: str
    recorded_at: datetime

class HealthMetricCreate(HealthMetricBase):
    source_doc_id: Optional[UUID] = None

class HealthMetric(HealthMetricBase):
    id: UUID
    source_doc_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HealthDashboard(BaseModel):
    summary: str
    recent_metrics: List[HealthMetric]
    active_alerts: List[str]
