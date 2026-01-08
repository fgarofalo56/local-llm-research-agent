"""
Ollama Embedder

Generates vector embeddings using Ollama's embedding models.
"""

import asyncio

import httpx
import structlog

logger = structlog.get_logger()


class OllamaEmbedder:
    """Generate embeddings using Ollama."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 60.0,
    ):
        """
        Initialize the Ollama embedder.

        Args:
            base_url: Ollama server URL
            model: Embedding model name (default: nomic-embed-text)
            timeout: Timeout for individual embedding requests in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._dimensions: int | None = None

    async def embed(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If Ollama returns an error
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=self.timeout,
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

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 10,
        max_retries: int = 3,
    ) -> list[list[float]]:
        """
        Generate embeddings for multiple texts with progress logging and retry logic.

        Args:
            texts: List of texts to embed
            batch_size: Number of concurrent embedding requests
            max_retries: Maximum retries for failed embeddings

        Returns:
            List of embedding vectors
        """
        total = len(texts)
        if total == 0:
            return []

        logger.info("embedding_batch_started", total_chunks=total)

        embeddings = [None] * total
        failed_indices = list(range(total))

        for retry in range(max_retries):
            if not failed_indices:
                break

            if retry > 0:
                logger.warning(
                    "embedding_batch_retry",
                    retry=retry,
                    remaining=len(failed_indices),
                )
                # Exponential backoff
                await asyncio.sleep(2**retry)

            # Process in batches
            new_failed = []
            for batch_start in range(0, len(failed_indices), batch_size):
                batch_indices = failed_indices[batch_start : batch_start + batch_size]

                # Create tasks for this batch
                tasks = []
                for idx in batch_indices:
                    tasks.append(self._embed_with_error_handling(texts[idx], idx))

                # Execute batch concurrently
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for idx, result in zip(batch_indices, results, strict=True):
                    if isinstance(result, Exception):
                        new_failed.append(idx)
                        logger.debug(
                            "embedding_chunk_failed",
                            chunk_index=idx,
                            error=str(result),
                        )
                    else:
                        embeddings[idx] = result

                # Log progress
                completed = (
                    total
                    - len(new_failed)
                    - len(
                        [
                            i
                            for i in failed_indices
                            if i not in batch_indices and embeddings[i] is None
                        ]
                    )
                )
                if batch_start % (batch_size * 5) == 0 or batch_start + batch_size >= len(
                    failed_indices
                ):
                    logger.info(
                        "embedding_batch_progress",
                        completed=completed,
                        total=total,
                        percent=round(completed / total * 100, 1),
                    )

            failed_indices = new_failed

        if failed_indices:
            raise RuntimeError(
                f"Failed to generate embeddings for {len(failed_indices)} chunks after {max_retries} retries"
            )

        logger.info("embedding_batch_completed", total_chunks=total)
        return embeddings

    async def _embed_with_error_handling(self, text: str, index: int) -> list[float]:
        """Embed a single text with error handling for batch processing."""
        try:
            return await self.embed(text)
        except Exception as e:
            logger.debug(
                "embedding_error",
                chunk_index=index,
                error_type=type(e).__name__,
                error=str(e)[:100],
            )
            raise

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

    async def embed_with_cache(self, text: str, cache=None) -> list[float]:
        """
        Generate embedding with optional caching.

        Args:
            text: Text to embed
            cache: Optional RedisCacheBackend instance for caching

        Returns:
            Embedding vector

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPStatusError: If Ollama returns an error
        """
        # Try cache first if available
        if cache:
            cached = await cache.get_embedding(text)
            if cached:
                return cached

        # Generate new embedding
        embedding = await self.embed(text)

        # Cache the result if cache is available
        if cache:
            await cache.set_embedding(text, embedding)

        return embedding
