from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from app.models.document import Document
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.services.embedding_service import embedding_service
from app.services.ai_service import ai_service

class ChatService:
    async def get_relevant_context(self, db: AsyncSession, person_id: UUID, query: str, limit: int = 3) -> str:
        """
        Performs semantic search using pgvector to find relevant document snippets.
        """
        query_embedding = await embedding_service.generate_embedding_async(query)
        
        # SQL for similarity search using <=> (cosine distance)
        # We use a raw SQL execution because SQLAlchemy pgvector integration 
        # can sometimes be tricky with async drivers and custom types
        sql = text("""
            SELECT content_text, title
            FROM documents 
            WHERE owner_id = :person_id AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :limit
        """)
        
        result = await db.execute(sql, {
            "person_id": person_id,
            "query_embedding": str(query_embedding),
            "limit": limit
        })
        
        rows = result.fetchall()
        context_parts = []
        for row in rows:
            content, title = row
            context_parts.append(f"[Document: {title}]\n{content[:500]}...")
            
        return "\n\n".join(context_parts)

    async def build_prompt(self, query: str, context: str, language: str = "hi") -> str:
        """
        Constructs the multilingual system prompt with context.
        """
        lang_instruction = "Please answer in Hindi." if language == "hi" else "Please answer in English."
        
        prompt = f"""
Medical Record Context:
{context}

User Question: {query}

Instruction: {lang_instruction} Base your answer ONLY on the context provided above. 
If the information is not in the context, say that you don't have enough information from the records.
Explain any medical terms in simple language for a caregiver.
"""
        return prompt

    async def process_chat(self, db: AsyncSession, session_id: UUID, user_query: str):
        """
        Full RAG cycle for a chat message.
        """
        # 1. Get session info
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalars().first()
        if not session:
            raise ValueError("Chat session not found")

        # 2. Retrieve Context (if person_id is set)
        context = ""
        if session.person_id:
            context = await self.get_relevant_context(db, session.person_id, user_query)

        # 3. Build Prompt
        # In a real app, we'd fetch the user's preferred language
        final_prompt = await self.build_prompt(user_query, context)

        # 4. Generate AI Response (CPU Only)
        ai_response_text = await ai_service.generate_response(final_prompt)

        # 5. Store Messages
        user_msg = Message(session_id=session_id, role="user", content=user_query)
        ai_msg = Message(session_id=session_id, role="assistant", content=ai_response_text)
        
        db.add(user_msg)
        db.add(ai_msg)
        await db.commit()
        
        return ai_response_text

chat_service = ChatService()
