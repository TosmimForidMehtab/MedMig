from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List, Any

class DocumentBase(BaseModel):
    owner_id: UUID
    owner_type: str # 'user' or 'family_member'
    title: str
    description: Optional[str] = None
    document_type: str # prescription, lab_report, etc.
    document_date: Optional[date] = None
    tags: Optional[List[str]] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    document_date: Optional[date] = None
    tags: Optional[List[str]] = None

class Document(DocumentBase):
    id: UUID
    file_name: str
    content_type: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentSearch(BaseModel):
    query: str
    person_id: UUID
    limit: Optional[int] = 5
