from pydantic import BaseModel, Field
from typing import Optional

class AadhaarOtpRequest(BaseModel):
    aadhaar_number: str = Field(..., pattern=r"^\d{12}$")

class AadhaarOtpVerify(BaseModel):
    otp: str = Field(..., pattern=r"^\d{6}$")
    txn_id: str

class AbhaAddressSuggestionRequest(BaseModel):
    txn_id: str

class AbhaAddressCreate(BaseModel):
    txn_id: str
    preferred_abha_address: str # e.g., name@abdm

class AbhaCardResponse(BaseModel):
    abha_number: str
    abha_address: str
    name: str
    gender: str
    date_of_birth: str
    qr_code: str # base64 encoded
