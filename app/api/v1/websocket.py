from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import asyncio
import json
from uuid import UUID

from app.api import deps
from app.models.chat_job import ChatJob
from app.models import SessionLocal

router = APIRouter()

@router.websocket("/ws/{job_id}")
async def websocket_chat(websocket: WebSocket, job_id: UUID):
    await websocket.accept()
    
    try:
        while True:
            async with SessionLocal() as db:
                result = await db.execute(select(ChatJob).where(ChatJob.id == job_id))
                job = result.scalars().first()
                
                if not job:
                    await websocket.send_json({"error": "Job not found"})
                    break
                
                if job.status == "completed":
                    await websocket.send_json({
                        "status": "completed",
                        "response_text": job.response_text
                    })
                    break
                
                if job.status == "failed":
                    await websocket.send_json({
                        "status": "failed",
                        "error": job.error_message
                    })
                    break
                
                # Still processing
                await websocket.send_json({"status": job.status})
            
            # Wait before polling again
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for job {job_id}")
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
