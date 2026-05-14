from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Optional

class FamilyMemberBase(BaseModel):
    name: str
    relationship: str
    date_of_birth: Optional[date] = None

class FamilyMemberCreate(FamilyMemberBase):
    pass

class FamilyMemberUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    date_of_birth: Optional[date] = None

class FamilyMember(FamilyMemberBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
