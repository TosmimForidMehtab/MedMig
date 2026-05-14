from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from uuid import UUID

from app.api import deps
from app.models.user import User
from app.models.chat_session import ChatSession
from app.models.chat_job import ChatJob
from app.schemas.chat import ChatSession as ChatSessionSchema, ChatSessionCreate, ChatSubmit, Message as MessageSchema
from app.models.message import Message
from app.services.chat_service import chat_service
from app.models import SessionLocal

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionSchema)
async def create_session(
    session_in: ChatSessionCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    db_obj = ChatSession(
        user_id=current_user.id,
        **session_in.model_dump()
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/history/{session_id}", response_model=List[MessageSchema])
async def get_history(
    session_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()

async def process_chat_background(job_id: UUID, query: str, session_id: UUID):
    async with SessionLocal() as db:
        try:
            # Update job status
            result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
            job = result.scalars().first()
            if job:
                job.status = "processing"
                await db.commit()
                
                # Process AI
                response_text = await chat_service.process_chat(db, session_id, query)
                
                # Update job completion
                job.status = "completed"
                job.response_text = response_text
                await db.commit()
        except Exception as e:
            # Re-fetch job to update error
            result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
            job = result.scalars().first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                await db.commit()

@router.post("/submit")
async def submit_chat(
    payload: ChatSubmit,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. Create Job
    job = ChatJob(
        session_id=payload.session_id,
        input_text=payload.query,
        status="pending"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # 2. Queue background task
    background_tasks.add_task(process_chat_background, job.id, payload.query, payload.session_id)
    
    return {"job_id": job.id, "status": "pending"}

@router.get("/status/{job_id}")
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "id": job.id,
        "status": job.status,
        "response_text": job.response_text,
        "error": job.error_message
    }
