from sentence_transformers import SentenceTransformer
from typing import List, Union
import asyncio
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL

    def initialize(self):
        if self.model is None:
            # This will download the model on first run
            # Force CPU usage
            self.model = SentenceTransformer(self.model_name, device="cpu")

    def generate_embedding(self, text: str) -> List[float]:
        if self.model is None:
            self.initialize()
        embedding = self.model.encode(text)
        return embedding.tolist()

    async def generate_embedding_async(self, text: str) -> List[float]:
        # Running in a thread pool to avoid blocking the event loop
        return await asyncio.to_thread(self.generate_embedding, text)

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if self.model is None:
            self.initialize()
        embeddings = self.model.encode(texts)
        return embeddings.tolist()

embedding_service = EmbeddingService()
