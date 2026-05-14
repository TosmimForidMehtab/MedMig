import os
from io import BytesIO
from typing import Optional
from pypdf import PdfReader
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.services.embedding_service import embedding_service
from app.config import settings

class DocumentService:
    async def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extracts text from a PDF file."""
        text = ""
        try:
            reader = PdfReader(BytesIO(file_bytes))
            for page in reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        return text

    async def extract_text_from_image(self, file_bytes: bytes) -> str:
        """
        Extracts text from an image. 
        Placeholder for OCR logic (e.g., Tesseract or multimodal AI).
        """
        # For now, we return an empty string or basic metadata
        # Real implementation would use pytesseract or Gemma-4-E2B-it
        return ""

    async def process_document(self, db: AsyncSession, document: Document, file_bytes: bytes):
        """
        Processes a document: extracts text, infers metadata using AI, 
        generates embedding, and updates DB.
        """
        content_text = ""
        
        if document.content_type == "application/pdf":
            content_text = await self.extract_text_from_pdf(file_bytes)
        elif document.content_type.startswith("image/"):
            content_text = await self.extract_text_from_image(file_bytes)
        elif document.content_type == "text/plain":
            content_text = file_bytes.decode("utf-8", errors="replace")

        if content_text.strip():
            document.content_text = content_text
            
            # 1. Infer Metadata using AI (LLM)
            from app.services.ai_service import ai_service
            metadata = await ai_service.infer_document_metadata(content_text)
            
            document.title = metadata.get("title", document.title)
            document.document_type = metadata.get("type", document.document_type)
            document.description = metadata.get("description", document.description)
            document.tags = metadata.get("tags", document.tags)

            # 2. Generate embedding
            embedding = await embedding_service.generate_embedding_async(content_text[:1000]) # Limit for performance
            document.embedding = embedding
            
            await db.commit()
            await db.refresh(document)
            
        return document

document_service = DocumentService()
