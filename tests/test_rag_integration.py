"""
RAG Pipeline Integration Tests

Tests the complete flow: Document → Embed → Store → Search → Retrieve
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from tempfile import NamedTemporaryFile

from src.rag.document_processor import DocumentProcessor
from src.rag.embedder import OllamaEmbedder
from src.rag.vector_store_base import VectorStoreBase
from src.rag.vector_store_factory import VectorStoreFactory


class TestDocumentProcessing:
    """Tests for document parsing."""

    def test_parse_text_content(self):
        """Test parsing plain text."""
        processor = DocumentProcessor()
        text = "This is test content. " * 100
        chunks = processor._chunk_text(text)
        assert len(chunks) > 0
        assert all(len(c) <= 550 for c in chunks)  # chunk_size + overlap

    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
        text = "Word " * 200
        chunks = processor._chunk_text(text)
        # Verify overlap exists between consecutive chunks
        assert len(chunks) > 1
        for i in range(len(chunks) - 1):
            # Some words should appear in both chunks due to overlap
            chunk1_words = set(chunks[i].split())
            chunk2_words = set(chunks[i + 1].split())
            overlap_words = chunk1_words & chunk2_words
            # Should have at least some overlap
            assert len(overlap_words) > 0, "No overlap found between consecutive chunks"

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        processor = DocumentProcessor()
        chunks = processor._chunk_text("")
        assert chunks == []

    def test_chunk_text_single_chunk(self):
        """Test text that fits in a single chunk."""
        processor = DocumentProcessor(chunk_size=500)
        text = "Short text."
        chunks = processor._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    @pytest.mark.asyncio
    async def test_process_text_directly(self):
        """Test processing plain text without file."""
        processor = DocumentProcessor()
        result = await processor.process_text("Sample text content.", source_name="test")
        assert "chunks" in result
        assert "metadata" in result
        assert "full_text" in result
        assert result["metadata"]["filename"] == "test"

    @pytest.mark.asyncio
    async def test_process_unsupported_file_type(self):
        """Test handling of unsupported file types."""
        processor = DocumentProcessor()
        # Create a temporary file with unsupported extension
        with NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                await processor.process_file(tmp_path)
            assert "Unsupported file type" in str(exc_info.value)
        finally:
            tmp_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_process_nonexistent_file(self):
        """Test handling of nonexistent files."""
        processor = DocumentProcessor()
        with pytest.raises(ValueError) as exc_info:
            await processor.process_file(Path("/nonexistent/file.txt"))
        assert "File not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_bytes_empty(self):
        """Test processing empty bytes."""
        processor = DocumentProcessor()
        with pytest.raises(ValueError) as exc_info:
            await processor.process_bytes(b"", "test.txt")
        assert "0 bytes" in str(exc_info.value)


class TestEmbeddingGeneration:
    """Tests for embedding generation."""

    @pytest.mark.asyncio
    async def test_embedding_dimensions(self):
        """Test embeddings have correct dimensions."""
        mock_response = {"embedding": [0.1] * 768}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response,
                )
            )
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder()
            embedding = await embedder.embed("test text")
            assert len(embedding) == 768

    @pytest.mark.asyncio
    async def test_embedding_batch(self):
        """Test batch embedding generation."""
        mock_response = {"embedding": [0.1] * 768}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response,
                )
            )
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder()
            texts = ["text 1", "text 2", "text 3"]
            embeddings = await embedder.embed_batch(texts, batch_size=2)
            assert len(embeddings) == 3
            assert all(len(e) == 768 for e in embeddings)

    @pytest.mark.asyncio
    async def test_embedding_timeout(self):
        """Test embedding timeout handling."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder(timeout=1.0)
            with pytest.raises(httpx.TimeoutException):
                await embedder.embed("test")

    @pytest.mark.asyncio
    async def test_embedding_http_error(self):
        """Test embedding HTTP error handling."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
            mock_post = AsyncMock(return_value=mock_response)
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder()
            with pytest.raises(httpx.HTTPStatusError):
                await embedder.embed("test")

    @pytest.mark.asyncio
    async def test_get_dimensions_lazy_load(self):
        """Test lazy loading of embedding dimensions."""
        mock_response = {"embedding": [0.1] * 768}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(
                return_value=MagicMock(
                    status_code=200,
                    json=lambda: mock_response,
                )
            )
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder()
            # Before first embed, dimensions should be unknown
            with pytest.raises(ValueError):
                _ = embedder.dimensions

            # After get_dimensions, should work
            dims = await embedder.get_dimensions()
            assert dims == 768
            assert embedder.dimensions == 768


class TestVectorStoreOperations:
    """Tests for vector store operations."""

    @pytest.mark.asyncio
    async def test_add_and_search(self):
        """Test adding documents and searching."""
        # Mock embedder
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 768)
        mock_embedder.embed_batch = AsyncMock(
            return_value=[[0.1] * 768, [0.2] * 768]
        )

        # Test with mock store
        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.add_document = AsyncMock()
        mock_store.search = AsyncMock(
            return_value=[
                {
                    "content": "test content",
                    "score": 0.9,
                    "source": "test.txt",
                    "document_id": "doc1",
                    "chunk_index": 0,
                }
            ]
        )

        await mock_store.add_document(
            document_id="doc1",
            chunks=["Test chunk 1", "Test chunk 2"],
            source="test.txt",
        )

        results = await mock_store.search("test query", top_k=5)
        assert len(results) == 1
        assert results[0]["content"] == "test content"
        assert results[0]["document_id"] == "doc1"

    @pytest.mark.asyncio
    async def test_delete_document(self):
        """Test document deletion."""
        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.delete_document = AsyncMock(return_value=5)

        deleted = await mock_store.delete_document("doc1")
        assert deleted == 5

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Test getting vector store statistics."""
        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.get_stats = AsyncMock(
            return_value={
                "num_documents": 10,
                "num_chunks": 100,
                "store_type": "mock",
                "dimensions": 768,
            }
        )

        stats = await mock_store.get_stats()
        assert stats["num_documents"] == 10
        assert stats["num_chunks"] == 100
        assert stats["dimensions"] == 768


class TestVectorStoreFactory:
    """Tests for vector store factory."""

    @pytest.mark.asyncio
    async def test_create_invalid_type(self):
        """Test factory with invalid store type."""
        mock_embedder = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            await VectorStoreFactory.create(
                store_type="invalid",
                embedder=mock_embedder,
            )
        assert "Invalid vector store type" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_mssql_missing_session(self):
        """Test MSSQL store creation without session factory."""
        mock_embedder = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            await VectorStoreFactory.create(
                store_type="mssql",
                embedder=mock_embedder,
                session_factory=None,
            )
        assert "session_factory is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_redis_missing_client(self):
        """Test Redis store creation without client."""
        mock_embedder = MagicMock()
        with pytest.raises(ValueError) as exc_info:
            await VectorStoreFactory.create(
                store_type="redis",
                embedder=mock_embedder,
                redis_client=None,
            )
        assert "redis_client is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_with_fallback_success(self):
        """Test factory with successful fallback."""
        mock_embedder = MagicMock()
        mock_redis = MagicMock()

        with patch.object(
            VectorStoreFactory, "_create_mssql_store", side_effect=RuntimeError("MSSQL failed")
        ):
            with patch.object(
                VectorStoreFactory,
                "_create_redis_store",
                return_value=MagicMock(spec=VectorStoreBase),
            ):
                store = await VectorStoreFactory.create_with_fallback(
                    primary_type="mssql",
                    fallback_type="redis",
                    embedder=mock_embedder,
                    redis_client=mock_redis,
                )
                assert store is not None

    @pytest.mark.asyncio
    async def test_create_with_fallback_both_fail(self):
        """Test factory when both primary and fallback fail."""
        mock_embedder = MagicMock()

        with patch.object(
            VectorStoreFactory, "_create_mssql_store", side_effect=RuntimeError("MSSQL failed")
        ):
            with patch.object(
                VectorStoreFactory, "_create_redis_store", side_effect=RuntimeError("Redis failed")
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    await VectorStoreFactory.create_with_fallback(
                        primary_type="mssql",
                        fallback_type="redis",
                        embedder=mock_embedder,
                    )
                assert "Failed to create vector store" in str(exc_info.value)


class TestRAGPipelineEndToEnd:
    """End-to-end tests for RAG pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """Test complete RAG flow with mocks."""
        # 1. Parse document
        processor = DocumentProcessor(chunk_size=100)
        text = "Sample document content. " * 50
        chunks = processor._chunk_text(text)
        assert len(chunks) > 0

        # 2. Generate embeddings (mocked)
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 768)
        mock_embedder.embed_batch = AsyncMock(
            return_value=[[0.1 * i] * 768 for i in range(len(chunks))]
        )

        # 3. Store in vector store (mocked)
        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.add_document = AsyncMock()
        mock_store.search = AsyncMock(
            return_value=[
                {
                    "content": chunks[0],
                    "score": 0.95,
                    "source": "doc.txt",
                    "document_id": "test-doc",
                    "chunk_index": 0,
                }
            ]
        )

        await mock_store.add_document(
            document_id="test-doc",
            chunks=chunks,
            source="doc.txt",
        )

        # 4. Search
        results = await mock_store.search("sample", top_k=3)
        assert len(results) > 0
        assert "content" in results[0]
        assert "score" in results[0]

    @pytest.mark.asyncio
    async def test_pipeline_with_metadata(self):
        """Test RAG pipeline with document metadata."""
        processor = DocumentProcessor()
        chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]

        mock_embedder = MagicMock()
        mock_embedder.embed_batch = AsyncMock(
            return_value=[[0.1] * 768, [0.2] * 768, [0.3] * 768]
        )

        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.add_document = AsyncMock()

        metadata = {"author": "test", "date": "2024-01-01"}

        await mock_store.add_document(
            document_id="doc1",
            chunks=chunks,
            source="test.txt",
            source_type="document",
            metadata=metadata,
        )

        mock_store.add_document.assert_called_once()
        call_kwargs = mock_store.add_document.call_args[1]
        assert call_kwargs["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_pipeline_search_with_filters(self):
        """Test RAG search with source type filters."""
        mock_embedder = MagicMock()
        mock_embedder.embed = AsyncMock(return_value=[0.1] * 768)

        mock_store = MagicMock(spec=VectorStoreBase)
        mock_store.search = AsyncMock(
            return_value=[
                {
                    "content": "schema content",
                    "score": 0.9,
                    "source": "table_schema",
                    "source_type": "schema",
                }
            ]
        )

        results = await mock_store.search(
            "test query", top_k=5, source_type="schema"
        )
        assert len(results) > 0
        assert results[0]["source_type"] == "schema"


class TestErrorHandling:
    """Tests for error handling in RAG pipeline."""

    @pytest.mark.asyncio
    async def test_invalid_document_type(self):
        """Test handling of unsupported file types."""
        processor = DocumentProcessor()
        # Create a temporary file with unsupported extension
        with NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                await processor.process_file(tmp_path)
            assert "Unsupported file type" in str(exc_info.value)
        finally:
            tmp_path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_embedding_service_unavailable(self):
        """Test handling when Ollama is unavailable."""
        import httpx

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_post = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder(base_url="http://nonexistent:11434")

            with pytest.raises(httpx.ConnectError):
                await embedder.embed("test text")

    @pytest.mark.asyncio
    async def test_embedding_batch_partial_failure(self):
        """Test batch embedding with some failures."""
        import httpx

        call_count = [0]

        async def mock_post(*args, **kwargs):
            call_count[0] += 1
            # First call fails, subsequent retries succeed
            if call_count[0] <= 3:
                raise httpx.ConnectError("Temporary error")
            return MagicMock(
                status_code=200,
                json=lambda: {"embedding": [0.1] * 768},
            )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            embedder = OllamaEmbedder()
            # Should fail after max retries
            with pytest.raises(RuntimeError) as exc_info:
                await embedder.embed_batch(["text1"], max_retries=2)
            assert "Failed to generate embeddings" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_vector_store_clear_not_implemented(self):
        """Test clear_all raises NotImplementedError for base class."""
        # Create a concrete implementation that doesn't override clear_all
        class MinimalVectorStore(VectorStoreBase):
            async def create_index(self, overwrite: bool = False) -> None:
                pass

            async def add_document(
                self, document_id: str, chunks: list[str], source: str,
                source_type: str = "document", metadata: dict = None
            ) -> None:
                pass

            async def search(
                self, query: str, top_k: int = 5, source_type: str = None
            ) -> list[dict]:
                return []

            async def delete_document(self, document_id: str) -> int:
                return 0

            async def get_stats(self) -> dict:
                return {}

        mock_embedder = MagicMock()
        store = MinimalVectorStore(embedder=mock_embedder, dimensions=768)

        with pytest.raises(NotImplementedError) as exc_info:
            await store.clear_all()
        assert "does not implement clear_all" in str(exc_info.value)


class TestDocumentProcessorMethods:
    """Additional tests for DocumentProcessor methods."""

    def test_strip_html_tags(self):
        """Test HTML tag removal."""
        processor = DocumentProcessor()
        html = "<html><head><script>alert('test')</script></head><body><p>Hello World</p></body></html>"
        text = processor._strip_html_tags(html)
        assert "Hello World" in text
        assert "<p>" not in text
        assert "script" not in text.lower()

    def test_strip_html_with_styles(self):
        """Test HTML stripping removes style tags."""
        processor = DocumentProcessor()
        html = "<style>body { color: red; }</style><div>Content</div>"
        text = processor._strip_html_tags(html)
        assert "Content" in text
        assert "style" not in text.lower()
        assert "color: red" not in text
