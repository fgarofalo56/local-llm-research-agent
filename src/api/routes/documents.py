"""
Documents Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for document upload, processing, and management.
"""

import uuid
from datetime import datetime
from pathlib import Path

import aiofiles
import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db, get_vector_store_optional
from src.api.models.database import Document
from src.rag.document_processor import DocumentProcessor
from src.utils.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


class DocumentResponse(BaseModel):
    """Response model for document."""

    id: int
    filename: str
    original_filename: str
    mime_type: str | None
    file_size: int
    chunk_count: int | None
    processing_status: str
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for document list."""

    documents: list[DocumentResponse]
    total: int


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all documents."""
    # Get total count
    count_query = select(Document)
    result = await db.execute(count_query)
    total = len(result.scalars().all())

    # Get paginated results
    query = select(Document).offset(skip).limit(limit).order_by(Document.created_at.desc())
    result = await db.execute(query)
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
    )


@router.post("", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store_optional),
):
    """Upload a new document for processing."""
    settings = get_settings()

    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.max_upload_size_mb * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB",
        )

    # Validate file type
    processor = DocumentProcessor(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    suffix = Path(file.filename).suffix.lower()
    if suffix not in processor.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {processor.SUPPORTED_EXTENSIONS}",
        )

    # Save file
    filename = f"{uuid.uuid4()}{suffix}"
    upload_path = Path(settings.upload_dir) / filename
    upload_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(upload_path, "wb") as f:
        await f.write(content)

    # Create database record
    document = Document(
        filename=filename,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=file_size,
        processing_status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Process in background if vector store is available
    if vector_store:
        background_tasks.add_task(
            process_document_task,
            document.id,
            upload_path,
            settings.chunk_size,
            settings.chunk_overlap,
        )
    else:
        logger.warning("vector_store_unavailable", document_id=document.id)

    return DocumentResponse.model_validate(document)


async def process_document_task(
    document_id: int,
    file_path: Path,
    chunk_size: int,
    chunk_overlap: int,
):
    """Background task to process document."""
    from src.api.deps import _session_factory, _vector_store

    if _session_factory is None:
        logger.error("database_not_available", document_id=document_id)
        return

    processor = DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    async with _session_factory() as db:
        try:
            # Update status
            doc = await db.get(Document, document_id)
            if not doc:
                return
            doc.processing_status = "processing"
            await db.commit()

            # Process file
            result = await processor.process_file(file_path)

            # Add to vector store if available
            if _vector_store:
                await _vector_store.add_document(
                    document_id=str(document_id),
                    chunks=result["chunks"],
                    source=doc.original_filename,
                    source_type="document",
                    metadata=result["metadata"],
                )

            # Update record
            doc.chunk_count = len(result["chunks"])
            doc.processing_status = "completed"
            doc.processed_at = datetime.utcnow()
            await db.commit()

            logger.info(
                "document_processed",
                document_id=document_id,
                chunks=len(result["chunks"]),
            )

        except Exception as e:
            logger.error(
                "document_processing_failed",
                document_id=document_id,
                error=str(e),
            )
            doc = await db.get(Document, document_id)
            if doc:
                doc.processing_status = "failed"
                doc.error_message = str(e)[:500]
                await db.commit()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store_optional),
):
    """Delete a document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    if vector_store:
        await vector_store.delete_document(str(document_id))

    # Delete file
    settings = get_settings()
    file_path = Path(settings.upload_dir) / document.filename
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    await db.delete(document)
    await db.commit()

    return {"status": "deleted", "document_id": document_id}


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    document_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store_optional),
):
    """Reprocess a failed document."""
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.processing_status not in ("failed", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reprocess document with status '{document.processing_status}'",
        )

    settings = get_settings()

    # Check file still exists
    file_path = Path(settings.upload_dir) / document.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    # Delete existing embeddings if any
    if vector_store:
        try:
            await vector_store.delete_document(str(document_id))
        except Exception:
            pass  # May not exist

    # Reset status
    document.processing_status = "pending"
    document.error_message = None
    document.chunk_count = None
    document.processed_at = None
    await db.commit()
    await db.refresh(document)

    # Process in background
    if vector_store:
        background_tasks.add_task(
            process_document_task,
            document.id,
            file_path,
            settings.chunk_size,
            settings.chunk_overlap,
        )

    return DocumentResponse.model_validate(document)


class DocumentTagsUpdate(BaseModel):
    """Request model for updating document tags."""

    tags: list[str]


@router.patch("/{document_id}/tags", response_model=DocumentResponse)
async def update_document_tags(
    document_id: int,
    data: DocumentTagsUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update tags for a document.

    Note: This endpoint is a placeholder. The Document model would need a 'tags'
    column (JSON/Text) to fully support this feature. For now, it validates
    the document exists but doesn't persist tags.
    """
    document = await db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # TODO: Add tags column to Document model in a future migration
    # document.tags = json.dumps(data.tags)
    # await db.commit()
    # await db.refresh(document)

    logger.info("document_tags_update", document_id=document_id, tags=data.tags)

    return DocumentResponse.model_validate(document)
