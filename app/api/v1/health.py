from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.health_metric import HealthMetric
from app.schemas.health import HealthMetric as HealthMetricSchema, HealthDashboard
from app.services.health_service import health_service

router = APIRouter()

@router.get("/dashboard", response_model=HealthDashboard)
async def get_dashboard(
    owner_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Fetch recent metrics
    result = await db.execute(
        select(HealthMetric)
        .where(HealthMetric.owner_id == owner_id)
        .order_by(HealthMetric.recorded_at.desc())
        .limit(10)
    )
    metrics = result.scalars().all()
    
    # Get intelligent summary and alerts
    summary, alerts = await health_service.get_health_summary(db, owner_id)
    
    return {
        "summary": summary,
        "recent_metrics": metrics,
        "active_alerts": alerts
    }

@router.get("/trends/{metric_type}")
async def get_trends(
    owner_id: UUID,
    metric_type: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # Historical data list
    result = await db.execute(
        select(HealthMetric)
        .where(HealthMetric.owner_id == owner_id, HealthMetric.metric_type == metric_type)
        .order_by(HealthMetric.recorded_at.asc())
    )
    history = result.scalars().all()
    
    # Statistical trend
    trend_stats = await health_service.get_metric_trends(db, owner_id, metric_type)
    
    return {
        "metric_type": metric_type,
        "history": history,
        "stats": trend_stats
    }
