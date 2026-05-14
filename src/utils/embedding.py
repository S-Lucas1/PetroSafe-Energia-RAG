"""
PetroSafe Energia - Cliente de Embeddings (Ollama)
Sprint 5 - Geração de embeddings via nomic-embed-text
"""

import time
import requests
import structlog

logger = structlog.get_logger()


class EmbeddingClient:
    """Gera embeddings via API do Ollama com retry e backoff."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.host = host.rstrip("/")
        self.model = model
        self.url = f"{self.host}/api/embeddings"

    def generate(self, text: str, max_retries: int = 3) -> list[float]:
        """Gera embedding para um texto."""
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    self.url,
                    json={"model": self.model, "prompt": text},
                    timeout=60,
                )
                resp.raise_for_status()
                return resp.json()["embedding"]
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning("embedding_retry", attempt=attempt + 1, wait=wait, erro=str(e))
                    time.sleep(wait)
                else:
                    logger.error("embedding_falhou", erro=str(e))
                    raise

    def generate_batch(self, texts: list[str]) -> list[list[float]]:
        """Gera embeddings para uma lista de textos."""
        return [self.generate(t) for t in texts]
