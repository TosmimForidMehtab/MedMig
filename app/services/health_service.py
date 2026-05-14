import re
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.health_metric import HealthMetric
from app.models.document import Document

class HealthService:
    def __init__(self):
        # Basic regex patterns for common metrics
        self.patterns = {
            "blood_glucose": r"(?:blood\s+glucose|sugar|glu|glucose)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(?:mg/dl|mmol/l)?",
            "systolic_bp": r"(?:bp|blood\s+pressure)\s*[:=-]?\s*(\d{2,3})\s*/\s*\d{2,3}",
            "diastolic_bp": r"(?:bp|blood\s+pressure)\s*[:=-]?\s*\d{2,3}\s*/\s*(\d{2,3})",
            "hemoglobin": r"(?:hemoglobin|hb)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(?:g/dl|gm%)?",
            "weight": r"(?:weight|wt)\s*[:=-]?\s*(\d+(?:\.\d+)?)\s*(?:kg|lbs)?",
        }

    def extract_metrics(self, text: str) -> List[Dict]:
        """
        Parses text for medical metrics using regex.
        """
        extracted = []
        text_lower = text.lower()
        
        for metric_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value = float(match.group(1))
                unit = "unknown"
                
                # Assign default units
                if "glucose" in metric_type: unit = "mg/dL"
                elif "bp" in metric_type: unit = "mmHg"
                elif "hemoglobin" in metric_type: unit = "g/dL"
                elif "weight" in metric_type: unit = "kg"
                
                extracted.append({
                    "metric_type": metric_type,
                    "value": value,
                    "unit": unit
                })
        
        return extracted

    async def parse_and_store_metrics(self, db: AsyncSession, document: Document):
        """
        Extracts metrics from document text using AI and stores them in the database.
        """
        if not document.content_text:
            return []
            
        from app.services.ai_service import ai_service
        metrics_data = await ai_service.extract_health_metrics(document.content_text)
        
        # fallback to regex if AI fails or returns empty
        if not metrics_data:
            metrics_data = self.extract_metrics(document.content_text)
            
        stored_metrics = []
        for data in metrics_data:
            try:
                val = float(data["value"])
                metric = HealthMetric(
                    owner_id=document.owner_id,
                    owner_type=document.owner_type,
                    metric_type=str(data["metric_type"]).lower().replace(' ', '_'),
                    value=val,
                    unit=str(data.get("unit", "")),
                    recorded_at=document.document_date or document.created_at,
                    source_doc_id=document.id
                )
                db.add(metric)
                stored_metrics.append(metric)
            except (ValueError, KeyError):
                continue
            
        if stored_metrics:
            await db.commit()
            
        return stored_metrics

    async def get_metric_trends(self, db: AsyncSession, owner_id: UUID, metric_type: str, limit: int = 10):
        """
        Calculates trends for a specific metric type.
        """
        from sqlalchemy import select
        result = await db.execute(
            select(HealthMetric)
            .where(HealthMetric.owner_id == owner_id, HealthMetric.metric_type == metric_type)
            .order_by(HealthMetric.recorded_at.desc())
            .limit(limit)
        )
        metrics = result.scalars().all()
        if not metrics or len(metrics) < 2:
            return {"trend": "stable", "change": 0}

        latest = metrics[0].value
        previous = metrics[1].value
        
        change = ((latest - previous) / previous) * 100 if previous != 0 else 0
        trend = "increasing" if change > 5 else "decreasing" if change < -5 else "stable"
        
        return {
            "latest_value": latest,
            "previous_value": previous,
            "change_percentage": round(change, 2),
            "trend": trend,
            "unit": metrics[0].unit
        }

    async def get_health_summary(self, db: AsyncSession, owner_id: UUID):
        """
        Generates a semantic summary based on recent documents and appends basic trends.
        """
        from app.services.ai_service import ai_service
        from sqlalchemy import select
        
        # 1. Fetch recent documents to generate an overall semantic summary
        doc_result = await db.execute(
            select(Document)
            .where(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .limit(3)
        )
        recent_docs = doc_result.scalars().all()
        
        summary_parts = []
        alerts = []
        
        if recent_docs:
            parts = []
            for doc in recent_docs:
                text = doc.content_text[:1000] if doc.content_text else ""
                parts.append(f"[Document: {doc.title}]\n{text}")
            
            prompt = f"Analyze the following recent medical documents for the patient and provide a concise 2-3 sentence overall health summary, highlighting any abnormal values or areas of concern.\n\nDocuments:\n{chr(10).join(parts)}"
            try:
                ai_summary = await ai_service.generate_response(prompt)
                summary_parts.append(ai_summary.strip())
            except Exception:
                summary_parts.append("Could not generate AI summary at this time.")
        else:
            summary_parts.append("No recent medical documents found to generate a health summary.")
            
        # 2. Check major metrics for alerts
        for m_type in ["blood_glucose", "systolic_bp"]:
            trend_data = await self.get_metric_trends(db, owner_id, m_type)
            if "latest_value" in trend_data:
                if trend_data["trend"] == "increasing" and m_type == "blood_glucose":
                    alerts.append(f"Warning: {m_type.replace('_', ' ')} has increased by {trend_data['change_percentage']}% recently.")
                elif trend_data["trend"] == "increasing" and m_type == "systolic_bp" and trend_data["latest_value"] > 140:
                    alerts.append("Alert: Blood pressure is trending high.")

        summary = "\n\n".join(summary_parts)
        return summary, alerts


health_service = HealthService()
