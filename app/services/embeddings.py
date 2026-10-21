import httpx

from app.storage.config import settings


class EmbeddingService:

    def __init__(self):
        self.url = f"{settings.OLLAMA_URL}/api/embeddings"
        self.model = settings.EMBEDDING_MODEL

    def embed_text_sync(self, text: str) -> list[float]:
        """Sync version for use in non-async routes."""
        import httpx

        with httpx.Client(timeout=120) as client:
            response = client.post(
                self.url,
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                self.url,
                json={"model": self.model, "prompt": text},
            )
            response.raise_for_status()
            return response.json()["embedding"]
