from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class MessageBase(BaseModel):
    role: str
    content: str
    audio_url: Optional[str] = None
    input_type: str = "text"

class Message(MessageBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatSessionBase(BaseModel):
    person_id: Optional[UUID] = None
    person_type: Optional[str] = None
    title: Optional[str] = None

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSession(ChatSessionBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatSubmit(BaseModel):
    session_id: UUID
    query: str
    return_voice: bool = False
