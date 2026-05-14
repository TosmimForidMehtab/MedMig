from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    preferred_language: str = "hi"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    abha_number: Optional[str] = None
    abha_address: Optional[str] = None

class User(UserBase):
    id: UUID
    abha_number: Optional[str] = None
    abha_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
