"""
Ollama Embedder
Phase 2.1: Backend Infrastructure & RAG Pipeline

Generates vector embeddings using Ollama's embedding models.
"""

import httpx
import structlog

logger = structlog.get_logger()


class OllamaEmbedder:
    """Generate embeddings using Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
    ):
        """
        Initialize the Ollama embedder.

        Args:
            base_url: Ollama server URL
            model: Embedding model name (default: nomic-embed-text)
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._dimensions: int | None = None

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            embedding = data["embedding"]

            if self._dimensions is None:
                self._dimensions = len(embedding)
                logger.info(
                    "embedding_dimensions_detected",
                    model=self.model,
                    dimensions=self._dimensions,
                )

            return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    @property
    def dimensions(self) -> int:
        """
        Get embedding dimensions.

        Raises:
            ValueError: If dimensions are unknown (no embedding generated yet)
        """
        if self._dimensions is None:
            raise ValueError("Dimensions unknown. Call embed() first.")
        return self._dimensions

    async def get_dimensions(self) -> int:
        """
        Get embedding dimensions, generating a test embedding if needed.

        Returns:
            Number of dimensions in the embedding vector
        """
        if self._dimensions is None:
            # Generate a test embedding to determine dimensions
            await self.embed("test")
        return self._dimensions
