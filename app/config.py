from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Trinetra"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/trinetra"
    
    # Security
    SECRET_KEY: str = "super-secret-key-change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Model
    MODEL_PATH: str = "./models/gemma-4-E2B-it.litertlm"
    
    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # ABDM
    ABDM_CLIENT_ID: Optional[str] = None
    ABDM_CLIENT_SECRET: Optional[str] = None
    
    # Storage
    UPLOAD_DIR: str = "./uploads"
    DOCUMENTS_DIR: str = "./documents"
    OUTPUT_DIR: str = "./outputs"
    EXPORTS_DIR: str = "./exports"
    
    # Defaults
    DEFAULT_LANGUAGE: str = "hi"
    MAX_FAMILY_MEMBERS: int = 5
    MAX_DOCUMENT_SIZE_MB: int = 10
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
