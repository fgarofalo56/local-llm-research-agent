"""
Tests for Documents API Routes
Phase 2.1+ Document Management API

Tests for:
- Document listing
- Document upload
- Document reprocessing
- Document tags update
- Document deletion
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException


class MockDocument:
    """Mock Document ORM model."""

    def __init__(
        self,
        id: int = 1,
        filename: str = "test-uuid.pdf",
        original_filename: str = "test.pdf",
        mime_type: str = "application/pdf",
        file_size: int = 1024,
        chunk_count: int | None = 10,
        processing_status: str = "completed",
        error_message: str | None = None,
        created_at: datetime = None,
        processed_at: datetime = None,
    ):
        self.id = id
        self.filename = filename
        self.original_filename = original_filename
        self.mime_type = mime_type
        self.file_size = file_size
        self.chunk_count = chunk_count
        self.processing_status = processing_status
        self.error_message = error_message
        self.created_at = created_at or datetime.utcnow()
        self.processed_at = processed_at


class TestDocumentResponse:
    """Tests for DocumentResponse model."""

    def test_response_from_document(self):
        """Test creating response from document."""
        from src.api.routes.documents import DocumentResponse

        doc = MockDocument()
        response = DocumentResponse(
            id=doc.id,
            filename=doc.filename,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            chunk_count=doc.chunk_count,
            processing_status=doc.processing_status,
            error_message=doc.error_message,
            created_at=doc.created_at,
            processed_at=doc.processed_at,
        )

        assert response.id == 1
        assert response.filename == "test-uuid.pdf"
        assert response.original_filename == "test.pdf"
        assert response.processing_status == "completed"
        assert response.chunk_count == 10

    def test_response_with_none_values(self):
        """Test response with optional None values."""
        from src.api.routes.documents import DocumentResponse

        response = DocumentResponse(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            mime_type=None,
            file_size=1024,
            chunk_count=None,
            processing_status="pending",
            error_message=None,
            created_at=datetime.utcnow(),
            processed_at=None,
        )

        assert response.mime_type is None
        assert response.chunk_count is None
        assert response.processed_at is None


class TestDocumentListResponse:
    """Tests for DocumentListResponse model."""

    def test_list_response(self):
        """Test list response structure."""
        from src.api.routes.documents import DocumentListResponse, DocumentResponse

        doc_response = DocumentResponse(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            mime_type="application/pdf",
            file_size=1024,
            chunk_count=10,
            processing_status="completed",
            error_message=None,
            created_at=datetime.utcnow(),
            processed_at=datetime.utcnow(),
        )

        list_response = DocumentListResponse(
            documents=[doc_response],
            total=1,
        )

        assert len(list_response.documents) == 1
        assert list_response.total == 1


class TestDocumentTagsUpdate:
    """Tests for DocumentTagsUpdate model."""

    def test_tags_update_model(self):
        """Test tags update request model."""
        from src.api.routes.documents import DocumentTagsUpdate

        data = DocumentTagsUpdate(tags=["research", "ml", "2024"])

        assert len(data.tags) == 3
        assert "research" in data.tags
        assert "ml" in data.tags

    def test_empty_tags(self):
        """Test empty tags list."""
        from src.api.routes.documents import DocumentTagsUpdate

        data = DocumentTagsUpdate(tags=[])

        assert len(data.tags) == 0


class TestReprocessEndpoint:
    """Tests for document reprocess endpoint logic."""

    @pytest.mark.asyncio
    async def test_reprocess_not_found(self):
        """Test reprocessing non-existent document."""
        from src.api.routes.documents import reprocess_document

        # Mock database session
        mock_db = AsyncMock()
        mock_db.get.return_value = None

        # Mock background tasks
        mock_bg = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await reprocess_document(
                document_id=999,
                background_tasks=mock_bg,
                db=mock_db,
                vector_store=None,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_reprocess_invalid_status(self):
        """Test reprocessing document with invalid status."""
        from src.api.routes.documents import reprocess_document

        # Mock document with pending status
        mock_doc = MockDocument(processing_status="processing")

        # Mock database session
        mock_db = AsyncMock()
        mock_db.get.return_value = mock_doc

        # Mock background tasks
        mock_bg = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await reprocess_document(
                document_id=1,
                background_tasks=mock_bg,
                db=mock_db,
                vector_store=None,
            )

        assert exc_info.value.status_code == 400
        assert "cannot reprocess" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_reprocess_file_not_found(self):
        """Test reprocessing when file doesn't exist on disk."""
        from src.api.routes.documents import reprocess_document

        # Mock document with failed status
        mock_doc = MockDocument(
            processing_status="failed",
            filename="nonexistent.pdf",
        )

        # Mock database session
        mock_db = AsyncMock()
        mock_db.get.return_value = mock_doc

        # Mock background tasks
        mock_bg = MagicMock()

        # Mock settings to return a path that doesn't exist
        with patch("src.api.routes.documents.get_settings") as mock_settings:
            mock_settings.return_value.upload_dir = "/nonexistent/path"

            with pytest.raises(HTTPException) as exc_info:
                await reprocess_document(
                    document_id=1,
                    background_tasks=mock_bg,
                    db=mock_db,
                    vector_store=None,
                )

            assert exc_info.value.status_code == 404
            assert "file not found" in exc_info.value.detail.lower()


class TestUpdateTagsEndpoint:
    """Tests for document tags update endpoint logic."""

    @pytest.mark.asyncio
    async def test_update_tags_not_found(self):
        """Test updating tags for non-existent document."""
        from src.api.routes.documents import update_document_tags, DocumentTagsUpdate

        # Mock database session
        mock_db = AsyncMock()
        mock_db.get.return_value = None

        data = DocumentTagsUpdate(tags=["test"])

        with pytest.raises(HTTPException) as exc_info:
            await update_document_tags(
                document_id=999,
                data=data,
                db=mock_db,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_update_tags_success(self):
        """Test successful tags update (placeholder implementation)."""
        from src.api.routes.documents import update_document_tags, DocumentTagsUpdate

        # Mock document
        mock_doc = MockDocument()

        # Mock database session
        mock_db = AsyncMock()
        mock_db.get.return_value = mock_doc

        data = DocumentTagsUpdate(tags=["research", "ml"])

        # The current implementation is a placeholder that doesn't persist tags
        # but should return success without error
        with patch("src.api.routes.documents.DocumentResponse") as mock_response:
            mock_response.model_validate.return_value = MagicMock(
                id=1,
                filename="test.pdf",
                original_filename="test.pdf",
                mime_type="application/pdf",
                file_size=1024,
                chunk_count=10,
                processing_status="completed",
                error_message=None,
                created_at=datetime.utcnow(),
                processed_at=datetime.utcnow(),
            )

            result = await update_document_tags(
                document_id=1,
                data=data,
                db=mock_db,
            )

            # Should not raise an error
            assert result is not None


class TestListDocuments:
    """Tests for document listing endpoint."""

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """Test listing when no documents exist."""
        from src.api.routes.documents import list_documents

        # Mock database session with empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await list_documents(skip=0, limit=20, db=mock_db)

        assert result.total == 0
        assert len(result.documents) == 0

    @pytest.mark.asyncio
    async def test_list_with_pagination(self):
        """Test listing with pagination parameters."""
        from src.api.routes.documents import list_documents

        # Mock documents
        mock_docs = [MockDocument(id=i) for i in range(1, 6)]

        # Mock database session
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.side_effect = [
            mock_docs[:5],  # First call for total count
            mock_docs[:2],  # Second call for paginated results
        ]

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        # Note: The actual implementation uses two queries,
        # so we need to handle both execute calls
        result = await list_documents(skip=0, limit=2, db=mock_db)

        # Check that pagination was requested
        assert mock_db.execute.call_count == 2


class TestGetDocument:
    """Tests for single document retrieval."""

    @pytest.mark.asyncio
    async def test_get_document_not_found(self):
        """Test getting non-existent document."""
        from src.api.routes.documents import get_document

        mock_db = AsyncMock()
        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_document(document_id=999, db=mock_db)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_success(self):
        """Test successful document retrieval."""
        from src.api.routes.documents import get_document

        mock_doc = MockDocument()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_doc

        with patch("src.api.routes.documents.DocumentResponse") as mock_response:
            mock_response.model_validate.return_value = MagicMock(id=1)

            result = await get_document(document_id=1, db=mock_db)

            assert result is not None


class TestDeleteDocument:
    """Tests for document deletion."""

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self):
        """Test deleting non-existent document."""
        from src.api.routes.documents import delete_document

        mock_db = AsyncMock()
        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await delete_document(document_id=999, db=mock_db, vector_store=None)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document_success(self):
        """Test successful document deletion."""
        from src.api.routes.documents import delete_document

        mock_doc = MockDocument()

        mock_db = AsyncMock()
        mock_db.get.return_value = mock_doc

        with patch("src.api.routes.documents.get_settings") as mock_settings:
            mock_settings.return_value.upload_dir = "/tmp/uploads"

            with patch("src.api.routes.documents.Path") as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = False
                mock_path.return_value.__truediv__.return_value = mock_path_instance

                result = await delete_document(
                    document_id=1,
                    db=mock_db,
                    vector_store=None,
                )

                assert result["status"] == "deleted"
                assert result["document_id"] == 1
