import os
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from uuid import UUID, uuid4
import json
from datetime import date

from app.api import deps
from app.models.user import User
from app.models.document import Document
from app.schemas.document import Document as DocumentSchema, DocumentCreate
from app.config import settings
from app.services.document_service import document_service
from app.services.health_service import health_service

router = APIRouter()

async def process_uploaded_document(doc_id: UUID, file_bytes: bytes, db_factory):
    """Background task to process document and extract metrics."""
    async with db_factory() as db:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalars().first()
        if document:
            # 1. OCR + Embeddings
            await document_service.process_document(db, document, file_bytes)
            # 2. Extract Health Metrics
            await health_service.parse_and_store_metrics(db, document)

@router.post("/", response_model=DocumentSchema)
async def upload_document(
    background_tasks: BackgroundTasks,
    owner_id: UUID = Form(...),
    title: Optional[str] = Form(None),
    document_type: Optional[str] = Form("other"),
    description: Optional[str] = Form(None),
    document_date: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    # 1. Determine Descriptive Owner Type
    owner_type = "self"
    if owner_id != current_user.id:
        from app.models.family_member import FamilyMember
        result = await db.execute(select(FamilyMember).where(FamilyMember.id == owner_id))
        member = result.scalars().first()
        if member:
            owner_type = member.relationship.lower()
        else:
            raise HTTPException(status_code=404, detail="Owner ID not found")

    # 2. Handle Dates
    parsed_document_date = date.today()
    if document_date is not None:
        document_date_str = document_date.strip()
        if document_date_str and document_date_str.lower() not in {"string", "null", "none"}:
            try:
                parsed_document_date = date.fromisoformat(document_date_str)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid document_date. Use YYYY-MM-DD."
                )

    # 3. Create directory and save file
    os.makedirs(settings.DOCUMENTS_DIR, exist_ok=True)
    file_path = os.path.join(settings.DOCUMENTS_DIR, f"{uuid4()}_{file.filename}")
    
    content = await file.read()
    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(content)
        size_bytes = len(content)

    parsed_tags = None
    if tags is not None:
        tags_str = tags.strip()
        if tags_str and tags_str.lower() not in {"string", "null", "none"}:
            try:
                decoded = json.loads(tags_str)
                if isinstance(decoded, list):
                    parsed_tags = [str(tag).strip() for tag in decoded if str(tag).strip()]
                elif isinstance(decoded, str):
                    parsed_tags = [decoded.strip()] if decoded.strip() else None
            except json.JSONDecodeError:
                parsed_tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()] or None
    
    # 4. Create DB record (with placeholders or provided data)
    db_obj = Document(
        owner_id=owner_id,
        owner_type=owner_type,
        title=title or "Processing...",
        description=description,
        document_type=document_type,
        document_date=parsed_document_date,
        tags=parsed_tags,
        file_path=file_path,
        file_name=file.filename,
        content_type=file.content_type,
        size_bytes=size_bytes
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)

    # 5. Queue background processing (AI will infer real title, type, tags)
    from app.models import SessionLocal
    background_tasks.add_task(process_uploaded_document, db_obj.id, content, SessionLocal)
    
    return db_obj


@router.get("/", response_model=List[DocumentSchema])
async def list_documents(
    owner_id: Optional[UUID] = None,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    query = select(Document)
    if owner_id:
        query = query.where(Document.owner_id == owner_id)
    # Note: In production, we'd also check if current_user has access to this owner_id
    
    result = await db.execute(query)
    return result.scalars().all()
