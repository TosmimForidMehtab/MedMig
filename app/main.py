from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.services.ai_service import ai_service
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize services
    ai_service.initialize()
    yield
    # Shutdown services if needed

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from app.api.v1 import auth, abha, family, documents, health, records, chat, websocket

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(abha.router, prefix="/api/v1/abha", tags=["abha"])
app.include_router(family.router, prefix="/api/v1/family", tags=["family"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(records.router, prefix="/api/v1/records", tags=["records"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(websocket.router, prefix="/api/v1/chat", tags=["chat"])
