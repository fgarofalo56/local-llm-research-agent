"""
Document Processor
Phase 2.1: Backend Infrastructure & RAG Pipeline

Processes documents using Docling for PDF, DOCX, and other formats.
"""

import tempfile
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class DocumentProcessor:
    """Process documents using Docling."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".md", ".txt"}

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize the document processor.

        Args:
            chunk_size: Target size for text chunks
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._converter = None

    @property
    def converter(self):
        """Lazy initialization of Docling converter."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
        return self._converter

    def _chunk_text(self, text: str) -> list[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk

        Returns:
            List of text chunks
        """
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                for boundary in [". ", ".\n", "! ", "!\n", "? ", "?\n"]:
                    last_boundary = text.rfind(boundary, start, end)
                    if last_boundary > start:
                        end = last_boundary + len(boundary)
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap
            if start >= text_length:
                break

        return chunks

    async def process_file(self, file_path: Path) -> dict[str, Any]:
        """
        Process a file and return chunks.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with chunks, metadata, and full text

        Raises:
            ValueError: If file type is not supported
        """
        logger.info("processing_file", path=str(file_path))

        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Convert document
        result = self.converter.convert(str(file_path))

        # Extract text
        full_text = result.document.export_to_markdown()

        # Chunk text
        chunks = self._chunk_text(full_text)

        # Extract metadata
        metadata = {
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "page_count": (
                len(result.document.pages) if hasattr(result.document, "pages") else None
            ),
        }

        logger.info(
            "file_processed",
            path=str(file_path),
            chunk_count=len(chunks),
        )

        return {
            "chunks": chunks,
            "metadata": metadata,
            "full_text": full_text,
        }

    async def process_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> dict[str, Any]:
        """
        Process file content from bytes.

        Args:
            content: File content as bytes
            filename: Original filename (used for extension detection)

        Returns:
            Dictionary with chunks, metadata, and full text
        """
        suffix = Path(filename).suffix
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            result = await self.process_file(tmp_path)
            return result
        finally:
            tmp_path.unlink()

    async def process_text(self, text: str, source_name: str = "text") -> dict[str, Any]:
        """
        Process plain text directly (no file conversion needed).

        Args:
            text: Text content
            source_name: Name for the source

        Returns:
            Dictionary with chunks and metadata
        """
        chunks = self._chunk_text(text)

        return {
            "chunks": chunks,
            "metadata": {
                "filename": source_name,
                "extension": ".txt",
                "page_count": None,
            },
            "full_text": text,
        }
