from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api import deps
from app.models.user import User
from app.schemas.abha import (
    AadhaarOtpRequest, 
    AadhaarOtpVerify, 
    AbhaAddressSuggestionRequest,
    AbhaAddressCreate,
    AbhaCardResponse
)
from app.services.abdm_service import abdm_service

router = APIRouter()

@router.post("/registration/aadhaar/otp")
async def request_aadhaar_otp(
    payload: AadhaarOtpRequest,
    current_user: User = Depends(deps.get_current_user)
):
    txn_id = await abdm_service.generate_aadhaar_otp(payload.aadhaar_number)
    return {"txn_id": txn_id, "message": "OTP sent to Aadhaar-linked mobile number."}

@router.post("/registration/aadhaar/verify")
async def verify_aadhaar_otp(
    payload: AadhaarOtpVerify,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await abdm_service.verify_aadhaar_otp(payload.otp, payload.txn_id)
    if result.get("status") == "success":
        # Link ABHA number to user temporarily if needed, or wait for address creation
        return result
    raise HTTPException(status_code=400, detail="Invalid OTP or session expired.")

@router.post("/registration/suggestions")
async def get_suggestions(
    payload: AbhaAddressSuggestionRequest,
    current_user: User = Depends(deps.get_current_user)
):
    suggestions = await abdm_service.get_abha_address_suggestions(payload.txn_id)
    return {"suggestions": suggestions}

@router.post("/registration/create-address")
async def create_abha_address(
    payload: AbhaAddressCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    success = await abdm_service.create_abha_address(payload.preferred_abha_address, payload.txn_id)
    if success:
        # In a real flow, verify_aadhaar_otp would have returned the ABHA number
        # Here we mock it for the demo
        current_user.abha_address = payload.preferred_abha_address
        current_user.abha_number = "91-1234-5678-9012" 
        await db.commit()
        return {"message": "ABHA created and linked successfully."}
    raise HTTPException(status_code=400, detail="Failed to create ABHA address.")

@router.get("/card", response_model=AbhaCardResponse)
async def get_abha_card(
    current_user: User = Depends(deps.get_current_user)
):
    if not current_user.abha_number:
        raise HTTPException(status_code=404, detail="No ABHA linked to this account.")
    
    card_data = await abdm_service.get_abha_card(current_user.abha_number)
    return {
        "abha_number": card_data["abhaNumber"],
        "abha_address": card_data["abhaAddress"],
        "name": card_data["name"],
        "gender": card_data["gender"],
        "date_of_birth": card_data["dob"],
        "qr_code": card_data["qrCode"]
    }
