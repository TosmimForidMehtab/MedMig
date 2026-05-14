from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.services.abdm_service import abdm_service

router = APIRouter()

@router.post("/consent/request")
async def request_consent(
    target_abha_address: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Step 1: Send a consent request to the user's ABHA app.
    """
    consent_request_id = await abdm_service.request_consent(target_abha_address)
    return {
        "consent_request_id": consent_request_id,
        "message": f"Consent request sent to {target_abha_address}. Please approve in your ABHA app."
    }

@router.get("/consent/status/{request_id}")
async def get_consent_status(
    request_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Step 2: Check if user has approved the consent.
    """
    status = await abdm_service.get_consent_status(request_id)
    return {"status": status}

@router.post("/records/fetch")
async def trigger_fetch(
    consent_id: str,
    current_user: User = Depends(deps.get_current_user)
):
    """
    Step 3: Trigger data fetch (M3 HIU flow) after consent is granted.
    """
    fetch_job_id = await abdm_service.fetch_medical_records(consent_id)
    return {
        "fetch_job_id": fetch_job_id,
        "message": "Data fetch initiated. Records will appear in your hub once processed."
    }
