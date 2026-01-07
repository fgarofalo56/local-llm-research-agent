"""
Document Service
Phase 2.1: Backend Infrastructure & RAG Pipeline

Business logic for document upload, processing, and RAG operations.
Extracted from src/api/routes/documents.py to separate concerns.
"""

import contextlib
import json
import uuid
from datetime import datetime
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.database import Document
from src.rag.docling_processor import get_document_processor
from src.utils.config import get_settings

logger = structlog.get_logger()


class DocumentService:
    """Service for document management and RAG operations."""

    def __init__(
        self,
        session_factory=None,
        vector_store=None,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """Initialize document service.

        Args:
            session_factory: SQLAlchemy async session factory for database operations.
            vector_store: Vector store instance for embeddings (optional).
            chunk_size: Size of document chunks for processing (optional, uses settings default).
            chunk_overlap: Overlap between chunks (optional, uses settings default).
        """
        self._session_factory = session_factory
        self._vector_store = vector_store
        settings = get_settings()
        self._chunk_size = chunk_size or settings.chunk_size
        self._chunk_overlap = chunk_overlap or settings.chunk_overlap
        self._settings = settings

    async def list_documents(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 20,
        tag: str | None = None,
    ) -> tuple[list[Document], int]:
        """List all documents with optional tag filtering.

        Args:
            db: Database session.
            skip: Number of documents to skip (pagination).
            limit: Maximum number of documents to return.
            tag: Optional tag to filter by (case-insensitive).

        Returns:
            Tuple of (list of documents, total count).
        """
        # Get all documents
        count_query = select(Document)
        result = await db.execute(count_query)
        all_docs = result.scalars().all()

        # Filter by tag if provided
        if tag:
            filtered_docs = []
            for doc in all_docs:
                if doc.tags:
                    try:
                        doc_tags = json.loads(doc.tags)
                        if tag.lower() in [t.lower() for t in doc_tags]:
                            filtered_docs.append(doc)
                    except (json.JSONDecodeError, TypeError):
                        logger.debug(
                            "skipping_document_with_invalid_tags",
                            document_id=doc.id,
                            tags_value=doc.tags,
                        )
            total = len(filtered_docs)
            # Apply pagination
            documents = filtered_docs[skip : skip + limit]
        else:
            total = len(all_docs)
            # Get paginated results
            query = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
            result = await db.execute(query)
            documents = result.scalars().all()

        return documents, total

    async def get_document(self, db: AsyncSession, document_id: int) -> Document | None:
        """Get a specific document by ID.

        Args:
            db: Database session.
            document_id: ID of the document to retrieve.

        Returns:
            Document instance or None if not found.
        """
        return await db.get(Document, document_id)

    async def get_all_tags(self, db: AsyncSession) -> list[str]:
        """Get all unique tags across all documents.

        Args:
            db: Database session.

        Returns:
            Sorted list of unique tags.
        """
        query = select(Document)
        result = await db.execute(query)
        documents = result.scalars().all()

        all_tags: set[str] = set()
        for doc in documents:
            if doc.tags:
                try:
                    doc_tags = json.loads(doc.tags)
                    all_tags.update(doc_tags)
                except (json.JSONDecodeError, TypeError):
                    # Silently skip documents with malformed tags JSON
                    pass

        return sorted(all_tags)

    async def validate_upload(self, file_content: bytes, filename: str) -> None:
        """Validate uploaded file before processing.

        Args:
            file_content: Raw file bytes.
            filename: Original filename.

        Raises:
            ValueError: If file is invalid (too large, unsupported type).
        """
        # Validate file size
        file_size = len(file_content)
        max_size = self._settings.max_upload_size_mb * 1024 * 1024

        if file_size > max_size:
            raise ValueError(
                f"File too large. Maximum size is {self._settings.max_upload_size_mb}MB"
            )

        # Validate file type using Docling processor (supports more formats)
        processor = get_document_processor(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )
        suffix = Path(filename).suffix.lower()
        if suffix not in processor.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type. Supported: {processor.SUPPORTED_EXTENSIONS}"
            )

    async def save_upload(
        self,
        db: AsyncSession,
        file_content: bytes,
        filename: str,
        mime_type: str | None,
    ) -> Document:
        """Save uploaded file to disk and create database record.

        Args:
            db: Database session.
            file_content: Raw file bytes.
            filename: Original filename.
            mime_type: MIME type of the file.

        Returns:
            Created Document instance with pending status.
        """
        # Generate unique filename
        suffix = Path(filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{suffix}"
        upload_path = Path(self._settings.upload_dir) / unique_filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        # Save file to disk
        upload_path.write_bytes(file_content)

        # Create database record
        document = Document(
            filename=unique_filename,
            original_filename=filename,
            mime_type=mime_type,
            file_size=len(file_content),
            processing_status="pending",
        )
        db.add(document)
        await db.commit()
        await db.refresh(document)

        return document

    async def process_document(
        self,
        document_id: int,
        file_path: Path,
    ) -> None:
        """Process a document: extract text, chunk, and create embeddings.

        This is typically called as a background task after upload.

        Args:
            document_id: ID of the document to process.
            file_path: Path to the uploaded file.

        Note:
            Requires session_factory and vector_store to be set during initialization.
        """
        if self._session_factory is None:
            logger.error("session_factory_not_available", document_id=document_id)
            return

        # Use Docling processor for comprehensive document handling
        processor = get_document_processor(
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
        )

        error_message = None

        # First, set status to "processing"
        try:
            async with self._session_factory() as db:
                doc = await db.get(Document, document_id)
                if not doc:
                    logger.warning("document_not_found", document_id=document_id)
                    return
                doc.processing_status = "processing"
                await db.commit()
        except Exception as e:
            logger.error(
                "document_status_update_failed",
                document_id=document_id,
                error=str(e),
            )
            return

        # Now process the document
        try:
            # Process file
            result = await processor.process_file(file_path)

            # Add to vector store if available
            if self._vector_store:
                await self._vector_store.add_document(
                    document_id=str(document_id),
                    chunks=result["chunks"],
                    source=file_path.name,
                    source_type="document",
                    metadata=result["metadata"],
                )

            # Update record with success
            async with self._session_factory() as db:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.chunk_count = len(result["chunks"])
                    doc.processing_status = "completed"
                    doc.processed_at = datetime.utcnow()
                    await db.commit()

            logger.info(
                "document_processed",
                document_id=document_id,
                chunks=len(result["chunks"]),
            )
            return

        except Exception as e:
            error_message = str(e)[:500]
            logger.error(
                "document_processing_failed",
                document_id=document_id,
                error=error_message,
            )

        # If we got here, processing failed
        try:
            async with self._session_factory() as db:
                doc = await db.get(Document, document_id)
                if doc:
                    doc.processing_status = "failed"
                    doc.error_message = error_message or "Unknown error"
                    await db.commit()
                    logger.info(
                        "document_marked_failed",
                        document_id=document_id,
                    )
        except Exception as e2:
            logger.error(
                "document_failed_status_update_error",
                document_id=document_id,
                original_error=error_message,
                status_update_error=str(e2),
            )

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> bool:
        """Delete a document from database, disk, and vector store.

        Args:
            db: Database session.
            document_id: ID of the document to delete.

        Returns:
            True if deleted successfully, False if not found.
        """
        document = await db.get(Document, document_id)
        if not document:
            return False

        # Delete from vector store
        if self._vector_store:
            await self._vector_store.delete_document(str(document_id))

        # Delete file from disk
        file_path = Path(self._settings.upload_dir) / document.filename
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        await db.delete(document)
        await db.commit()

        return True

    async def update_document_tags(
        self,
        db: AsyncSession,
        document_id: int,
        tags: list[str],
    ) -> Document | None:
        """Update tags for a document.

        Args:
            db: Database session.
            document_id: ID of the document to update.
            tags: List of tags to set (will be normalized).

        Returns:
            Updated Document instance or None if not found.
        """
        document = await db.get(Document, document_id)
        if not document:
            return None

        # Normalize tags: lowercase, strip whitespace, remove duplicates
        normalized_tags = list({tag.strip().lower() for tag in tags if tag.strip()})

        # Update tags
        document.tags = json.dumps(normalized_tags)
        await db.commit()
        await db.refresh(document)

        logger.info("document_tags_updated", document_id=document_id, tags=normalized_tags)

        return document

    async def reprocess_document(
        self,
        db: AsyncSession,
        document_id: int,
    ) -> tuple[Document | None, str | None]:
        """Reprocess a failed, completed, or stuck document.

        Args:
            db: Database session.
            document_id: ID of the document to reprocess.

        Returns:
            Tuple of (Document instance or None, error message or None).
        """
        document = await db.get(Document, document_id)
        if not document:
            return None, "Document not found"

        # Allow reprocessing for failed, completed, or stuck "processing" documents
        if document.processing_status not in ("failed", "completed", "processing"):
            return None, f"Cannot reprocess document with status '{document.processing_status}'"

        # Check file still exists
        file_path = Path(self._settings.upload_dir) / document.filename
        if not file_path.exists():
            return None, "Document file not found on disk"

        # Delete existing embeddings if any
        if self._vector_store:
            with contextlib.suppress(Exception):
                await self._vector_store.delete_document(str(document_id))

        # Reset status
        document.processing_status = "pending"
        document.error_message = None
        document.chunk_count = None
        document.processed_at = None
        await db.commit()
        await db.refresh(document)

        return document, None

    async def recover_stuck_documents(
        self,
        db: AsyncSession,
    ) -> tuple[list[int], int]:
        """Recover documents stuck in 'processing' status.

        Finds all documents with 'processing' status and resets them to 'pending'
        or 'failed' (if file is missing). Used after server restarts or crashes.

        Args:
            db: Database session.

        Returns:
            Tuple of (list of recovered document IDs, count of missing files).
        """
        # Find all stuck documents
        query = select(Document).where(Document.processing_status == "processing")
        result = await db.execute(query)
        stuck_documents = result.scalars().all()

        recovered_ids = []
        missing_count = 0

        for document in stuck_documents:
            # Check file still exists
            file_path = Path(self._settings.upload_dir) / document.filename
            if not file_path.exists():
                # Mark as failed if file is missing
                document.processing_status = "failed"
                document.error_message = "Document file not found on disk during recovery"
                missing_count += 1
                logger.warning(
                    "document_file_missing_during_recovery",
                    document_id=document.id,
                    filename=document.filename,
                )
                continue

            # Delete existing embeddings if any
            if self._vector_store:
                with contextlib.suppress(Exception):
                    await self._vector_store.delete_document(str(document.id))

            # Reset status to pending
            document.processing_status = "pending"
            document.error_message = None
            document.chunk_count = None
            document.processed_at = None
            recovered_ids.append(document.id)

        await db.commit()

        logger.info(
            "stuck_documents_recovered",
            recovered_count=len(recovered_ids),
            missing_count=missing_count,
            document_ids=recovered_ids,
        )

        return recovered_ids, missing_count
