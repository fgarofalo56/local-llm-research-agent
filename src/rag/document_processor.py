"""
Document Processor
Phase 2.1: Backend Infrastructure & RAG Pipeline

Processes documents using lightweight libraries that work fully offline.
No HuggingFace model downloads required.

Supported formats:
- PDF: Using pypdf (pure Python, no external dependencies)
- DOCX: Using python-docx
- TXT, MD, HTML: Direct text processing
"""

import tempfile
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class DocumentProcessor:
    """Process documents using lightweight offline-capable libraries."""

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".html"}

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize the document processor.

        Args:
            chunk_size: Target size for text chunks (in characters)
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

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

    def _extract_pdf_text(self, file_path: Path) -> tuple[str, int]:
        """
        Extract text from PDF using pypdf.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (extracted text, page count)
        """
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")

        reader = PdfReader(str(file_path))
        page_count = len(reader.pages)

        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {page_num} ---\n{page_text}")

        full_text = "\n\n".join(text_parts)
        logger.info("pdf_extracted", path=str(file_path), pages=page_count, chars=len(full_text))
        return full_text, page_count

    def _extract_docx_text(self, file_path: Path) -> tuple[str, int | None]:
        """
        Extract text from DOCX using python-docx.

        Args:
            file_path: Path to DOCX file

        Returns:
            Tuple of (extracted text, None for page count)
        """
        try:
            from docx import Document as DocxDocument
        except ImportError:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")

        doc = DocxDocument(str(file_path))

        text_parts = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)

        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)

        full_text = "\n\n".join(text_parts)
        logger.info("docx_extracted", path=str(file_path), paragraphs=len(text_parts), chars=len(full_text))
        return full_text, None

    def _extract_text_file(self, file_path: Path) -> tuple[str, None]:
        """
        Read plain text files (txt, md, html).

        Args:
            file_path: Path to text file

        Returns:
            Tuple of (file content, None for page count)
        """
        # Try common encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                logger.info("text_file_read", path=str(file_path), encoding=encoding, chars=len(content))
                return content, None
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Could not decode file {file_path} with any supported encoding")

    def _strip_html_tags(self, text: str) -> str:
        """
        Remove HTML tags from text (basic implementation).

        Args:
            text: HTML content

        Returns:
            Text with HTML tags removed
        """
        import re

        # Remove script and style elements
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Clean up whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

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

        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {suffix}. Supported: {self.SUPPORTED_EXTENSIONS}")

        # Extract text based on file type
        page_count = None

        if suffix == ".pdf":
            full_text, page_count = self._extract_pdf_text(file_path)
        elif suffix == ".docx":
            full_text, page_count = self._extract_docx_text(file_path)
        elif suffix == ".html":
            raw_text, _ = self._extract_text_file(file_path)
            full_text = self._strip_html_tags(raw_text)
        else:
            # .txt, .md - read as plain text
            full_text, _ = self._extract_text_file(file_path)

        # Chunk text
        chunks = self._chunk_text(full_text)

        # Build metadata
        metadata = {
            "filename": file_path.name,
            "extension": suffix,
            "page_count": page_count,
        }

        logger.info(
            "file_processed",
            path=str(file_path),
            chunk_count=len(chunks),
            total_chars=len(full_text),
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
