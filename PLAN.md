# Trinetra AI Chat API - Implementation Plan (Comprehensive & Detailed)

## 1. Project Overview

**Goal**: Build a production-ready FastAPI backend for Trinetra, an AI-powered health records companion. It accepts text/file/voice input and returns text/voice responses in multiple Indian languages (Hindi default) using the gemma-4-E2B-it.litertlm model. Features include ABHA-based record fetching, manual OCR uploads, family member management, health trend analytics, and secure time-bound sharing with doctors, all with a fully non-blocking architecture via WebSocket.

---

## 2. Technology Stack

| Layer | Technology |
|-------|-------------|
| API Framework | FastAPI (async) |
| Database | PostgreSQL + SQLAlchemy (async) |
| Vector Search | pgvector for semantic search |
| ORM | SQLAlchemy 2.0 with async support |
| Migration | Alembic |
| Task Queue | Background tasks (FastAPI built-in) |
| Real-time | WebSocket for streaming responses |
| AI Model | gemma-4-E2B-it.litertlm (local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| ABDM Integration | ABDM Sandbox/Gateway APIs (M1, M2, M3) |
| TTS (Voice Output) | Coqui TTS (Hindi/Multilingual models) + Google Cloud TTS (fallback) |
| File Storage | Local filesystem with async handling |
| Health Parsing | Custom FHIR-lite parsers for medical records |
| Validation | Pydantic v2 |
| Environment | python-dotenv |

---

## 3. Proposed Folder Structure

```
liteRT/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration/settings
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── family_member.py
│   │   ├── document.py
│   │   ├── health_metric.py       # New: Structured health data
│   │   ├── share_link.py          # New: Secure sharing logic
│   │   ├── notification.py        # New: Alerts & Activity
│   │   ├── chat_session.py
│   │   ├── message.py
│   │   └── file_attachment.py
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── abha.py                # New: ABHA/ABDM schemas
│   │   ├── family_member.py
│   │   ├── document.py
│   │   ├── health.py              # New: Dashboard/Trends schemas
│   │   ├── chat.py
│   │   └── file.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # Dependencies (get_db, get_current_user)
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── abha.py            # New: ABHA/ABDM endpoints
│   │   │   ├── family.py          # Family member management
│   │   │   ├── documents.py       # Document management
│   │   │   ├── chat.py            # Chat endpoints
│   │   │   ├── health.py          # New: Trends & Dashboard
│   │   │   ├── sharing.py         # New: Secure doctor sharing
│   │   │   ├── files.py          # File upload endpoints
│   │   │   └── websocket.py      # WebSocket endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── abdm_service.py        # New: M1, M2, M3 logic
│   │   ├── health_service.py      # New: Metric extraction & trends
│   │   ├── ai_service.py          # LiteRT LM wrapper + Multilingual
│   │   ├── tts_service.py        # TTS (local + fallback)
│   │   ├── file_service.py       # File handling
│   │   ├── document_service.py   # Document management & RAG
│   │   ├── embedding_service.py   # pgvector embedding generation
│   │   └── chat_service.py       # Chat logic
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── helpers.py
│   └── core/
│       ├── __init__.py
│       └── security.py            # JWT/token handling
├── alembic/                       # Database migrations
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
├── models/                        # AI models (gemma, TTS)
├── uploads/                       # User uploaded files (temp)
├── documents/                    # Stored user documents
├── outputs/                      # Generated TTS audio files
├── exports/                      # Generated PDFs for sharing
├── tests/                        # Unit/integration tests
├── .env                          # Environment variables
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 4. Database Schema

### Tables

**users**
- `id` (UUID, PK)
- `email` (VARCHAR, unique)
- `password_hash` (VARCHAR)
- `full_name` (VARCHAR, nullable)
- `abha_number` (VARCHAR, unique, nullable)
- `abha_address` (VARCHAR, unique, nullable)
- `preferred_language` (VARCHAR, default='hi')
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**family_members**
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `name` (VARCHAR) - Name of family member
- `relationship` (VARCHAR) - e.g., father, mother, spouse, child
- `date_of_birth` (DATE, nullable)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**documents**
- `id` (UUID, PK)
- `owner_id` (UUID, FK -> users.id OR family_members.id)
- `owner_type` (VARCHAR) - 'user' or 'family_member'
- `title` (VARCHAR)
- `description` (TEXT, nullable)
- `document_type` (VARCHAR) - prescription, lab_report, discharge_summary, imaging, other
- `file_path` (VARCHAR) - path to stored file
- `file_name` (VARCHAR)
- `content_type` (VARCHAR)
- `size_bytes` (INTEGER)
- `document_date` (DATE, nullable)
- `tags` (JSONB, nullable)
- `content_text` (TEXT, nullable)
- `embedding` (VECTOR(384))
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**health_metrics** (New)
- `id` (UUID, PK)
- `owner_id` (UUID, FK)
- `owner_type` (VARCHAR)
- `metric_type` (VARCHAR) - e.g., 'blood_glucose', 'systolic_bp', 'hemoglobin'
- `value` (FLOAT)
- `unit` (VARCHAR)
- `recorded_at` (TIMESTAMP)
- `source_doc_id` (UUID, FK -> documents.id)
- `created_at` (TIMESTAMP)

**doctor_shares** (New)
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `share_token` (VARCHAR, unique)
- `document_ids` (JSONB) - list of shared docs
- `expires_at` (TIMESTAMP)
- `access_count` (INTEGER)
- `created_at` (TIMESTAMP)

**notifications** (New)
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `title` (VARCHAR)
- `message` (TEXT)
- `type` (VARCHAR) - 'record_fetched', 'trend_alert', 'system'
- `is_read` (BOOLEAN)
- `created_at` (TIMESTAMP)

**chat_sessions**
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `person_id` (UUID, nullable) - links to user or family_member
- `person_type` (VARCHAR) - 'user' or 'family_member'
- `title` (VARCHAR)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**messages**
- `id` (UUID, PK)
- `session_id` (UUID, FK -> chat_sessions.id)
- `role` (VARCHAR) - 'user' | 'assistant'
- `content` (TEXT)
- `audio_url` (VARCHAR, nullable)
- `input_type` (VARCHAR) - 'text' | 'file' | 'audio'
- `created_at` (TIMESTAMP)

**file_attachments**
- `id` (UUID, PK)
- `message_id` (UUID, FK -> messages.id)
- `filename` (VARCHAR)
- `file_path` (VARCHAR)
- `content_type` (VARCHAR)
- `size_bytes` (INTEGER)
- `created_at` (TIMESTAMP)

**chat_jobs**
- `id` (UUID, PK)
- `session_id` (UUID, FK -> chat_sessions.id)
- `status` (VARCHAR) - pending, processing, completed, failed
- `input_text` (TEXT)
- `input_file_path` (VARCHAR, nullable)
- `response_text` (TEXT, nullable)
- `response_audio_url` (VARCHAR, nullable)
- `error_message` (TEXT, nullable)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

---

## 5. API Endpoints

### Authentication & ABHA
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login (returns JWT) |
| POST | `/api/v1/abha/registration/aadhaar/otp` | Step 1: Request OTP for ABHA creation |
| POST | `/api/v1/abha/registration/aadhaar/verify` | Step 2: Verify OTP and create ABHA |
| GET | `/api/v1/abha/card` | Download digital ABHA card |
| POST | `/api/v1/abha/records/fetch` | Trigger auto-fetch from ABDM |

### Family Members
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/family` | Add family member (max 5) |
| GET | `/api/v1/family` | List all family members |
| GET | `/api/v1/family/{member_id}` | Get family member details |
| PUT | `/api/v1/family/{member_id}` | Update family member |
| DELETE | `/api/v1/family/{member_id}` | Remove family member |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents` | Upload document with metadata |
| GET | `/api/v1/documents` | List documents (filter by person_id) |
| GET | `/api/v1/documents/{doc_id}` | Get document details |
| GET | `/api/v1/documents/{doc_id}/download` | Download document file |
| PUT | `/api/v1/documents/{doc_id}` | Update document metadata |
| DELETE | `/api/v1/documents/{doc_id}` | Delete document |
| GET | `/api/v1/documents/search?q={query}` | Search documents by text/tags |

### Health & Dashboard (New)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/dashboard` | Get summary (last records, active trends) |
| GET | `/api/v1/health/trends/{metric_type}`| Get historical data for a metric |
| POST | `/api/v1/metrics/manual` | Manually log a vital (sugar, BP) |

### Secure Sharing (New)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/sharing/share` | Generate time-bound secure link for docs |
| GET | `/api/v1/sharing/active` | List active share links |
| DELETE | `/api/v1/sharing/revoke/{share_id}`| Expire a link immediately |

### Chat (Async with WebSocket)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/submit` | Submit chat job with person_id |
| WebSocket | `/api/v1/chat/ws/{job_id}` | Connect for streaming results |
| GET | `/api/v1/chat/status/{job_id}` | Poll job status |
| GET | `/api/v1/chat/history/{session_id}` | Get chat history |
| POST | `/api/v1/chat/sessions` | Create new chat session |

---

## 6. Non-Blocking Architecture

### Flow: Submit → Background Process → WebSocket Stream

```
1. Client POST /api/v1/chat/submit
   - Validates input (text + optional file)
   - Includes person_id (user or family member) for document context
   - Saves file to uploads/ (async)
   - Creates job in DB with status "pending"
   - Returns job_id immediately (non-blocking)

2. Background task (asyncio.create_task)
   - Loads file content (if any)
   - If person_id provided: searches that person's documents for context
   - Builds prompt with document context + user query (Hindi default)
   - Calls gemma-4-E2B-it.litertlm
   - Gets text response
   - If voice requested: generates TTS audio (Coqui local)
   - Updates job status to "completed" with result

3. Client connects to WebSocket /api/v1/chat/ws/{job_id}
   - Server streams chunks of response in real-time
   - If voice: streams audio URL when ready
   - Connection closes when done

4. Client can also poll GET /api/v1/chat/status/{job_id}
```

---

## 7. Document-Based AI Context

### How It Works

1. **User selects person**: When starting a chat, user specifies `person_id` (themselves or a family member)
2. **Document search**: The AI service searches that person's documents for content relevant to the query
3. **Context injection**: Relevant document content is injected into the prompt as context
4. **Answer generation**: AI generates answer based on both the user's query and document context

### Document Search Strategy (Semantic Search with pgvector)

- **Semantic search**: Use pgvector for cosine similarity search on document embeddings
- **Text extraction**: Extract text from PDFs/images on upload for embedding generation
- **Embedding generation**: Use sentence-transformers (all-MiniLM-L6-v2) to generate 384-dim embeddings
- **Similarity search**: Query embedding → cosine similarity → return top 5 most relevant documents
- **Hybrid search**: Combine semantic similarity with keyword matching (title, tags)
- **Fallback**: If no relevant documents found, respond based on general knowledge

---

## 8. Semantic Search with pgvector

### Overview
PostgreSQL with pgvector extension enables efficient vector similarity search for semantic document retrieval.

### Database Setup
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table with embedding column
ALTER TABLE documents ADD COLUMN embedding vector(384);
```

### Embedding Service (`embedding_service.py`)
- Uses `sentence-transformers` (all-MiniLM-L6-v2) - lightweight, 384 dimensions
- Loads model on startup (cached for reuse)
- Generates embeddings for:
  - Document text content
  - User query during chat

### Key Implementation Details
```python
# Embedding generation
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str) -> list[float]:
    return model.encode(text).tolist()

# Similarity search query
async def semantic_search(
    query: str,
    owner_id: UUID,
    limit: int = 5
) -> list[Document]:
    query_embedding = generate_embedding(query)

    result = await db.execute(
        select(Document)
        .where(Document.owner_id == owner_id)
        .order_by(Document.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return result.scalars().all()
```

---

## 9. AI & TTS Services

### AI Service (`ai_service.py`)
- Wrap `litert_lm.Engine` for async inference
- Support: text, image, audio, PDF inputs
- **Multilingual Support**: Hindi as primary; system prompts template based on `preferred_language`
- Integrate with document service for RAG
- Build context-aware prompts with document excerpts

### TTS Service (`tts_service.py`)
- **Primary**: Coqui TTS (local, open-source) - `vits-hindi` for primary output
  - Download model on startup
  - Generate WAV/MP3 from text
- **Fallback**: Google Cloud TTS API for other regional languages

---

## 10. Implementation Phases (Week 1-4)

### Phase 1: Foundation & ABHA (Week 1)
- [ ] Set up project structure & async PostgreSQL
- [ ] **ABHA M1/M2 Integration**: Aadhaar OTP flow and ABHA address creation
- [ ] Implement user authentication (JWT)
- [ ] Basic config management

### Phase 2: Record Fetching & OCR (Week 2)
- [ ] **ABDM M3 Integration**: Auto-fetching records via HIU flow
- [ ] Manual OCR service for non-ABDM records
- [ ] Health metric extraction (parsing values from text into `health_metrics`)
- [ ] Document storage and retrieval with pgvector indexing

### Phase 3: AI Chat & Multilingual (Week 3)
- [ ] Integrate gemma-4-E2B-it.litertlm model with RAG
- [ ] Implement WebSocket streaming for chat results
- [ ] Hindi-first system prompts and conversation context
- [ ] Handle all input types (text/file/audio/PDF)

### Phase 4: Analytics, Sharing & Polish (Week 4)
- [ ] Health trends visualization logic & Dashboard API
- [ ] Secure time-bound sharing service
- [ ] Coqui TTS integration & performance optimization
- [ ] Unit & integration tests

---

## 11. Key Implementation Details

### Async File Handling
```python
# Use aiofiles for non-blocking file I/O
import aiofiles

async with aiofiles.open(path, 'wb') as f:
    await f.write(content)
```

### Background Tasks
```python
from fastapi import BackgroundTasks

@app.post("/chat/submit")
async def submit_chat(background_tasks: BackgroundTasks):
    job = await create_job(...)
    background_tasks.add_task(process_chat_job, job.id)
    return {"job_id": job.id}
```

### Document Context Injection
```python
async def build_context_aware_prompt(
    user_query: str,
    person_id: UUID
) -> str:
    # Search relevant documents
    docs = await document_service.search_documents(
        query=user_query,
        owner_id=person_id
    )

    context_parts = []
    for doc in docs:
        context_parts.append(f"[Document: {doc.title}]\n{doc.excerpt}")

    prompt = f"""Medical Record Context:
{chr(10).join(context_parts)}

User Question: {user_query}

Please answer in Hindi based on the context above."""
    return prompt
```

---

## 12. Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/trinetra

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256

# AI Model
MODEL_PATH=./models/gemma-4-E2B-it.litertlm

# ABDM
ABDM_CLIENT_ID=your-id
ABDM_CLIENT_SECRET=your-secret

# TTS
DEFAULT_LANGUAGE=hi
GOOGLE_TTS_API_KEY=optional-key

# Storage
UPLOAD_DIR=./uploads
DOCUMENTS_DIR=./documents

# Limits
MAX_FAMILY_MEMBERS=5
MAX_DOCUMENT_SIZE_MB=10
```

---

## 13. Acceptance Criteria
1. **ABHA Lifecycle**: Aadhaar OTP registration and record fetching successful.
2. **AI Chat**: Responds in Hindi using context from both ABDM and manual records.
3. **Non-blocking**: Submit returns immediately; WebSocket streams response.
4. **Analytics**: Dashboard shows trends for metrics like Blood Sugar and BP.
5. **Sharing**: Secure links generated for doctor review expire correctly.
6. **Multi-modal**: Supports text, image, audio, and PDF inputs.

---

## 14. Document Types
Prescription, Lab Report, Discharge Summary, Imaging, Medical Certificate, Insurance, Other.

---

## 15. Open Questions
- Specific ABDM Gateway vendor choice (Setu, EkaCare, or direct)?
- Handling of non-standardized medical report formats in OCR.

---
*Plan comprehensive: Merged original technical details with new product requirements.*
