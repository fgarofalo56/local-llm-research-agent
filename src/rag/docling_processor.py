"""
Docling Document Processor
Phase 2.1+: Enhanced RAG Pipeline with Docling

Processes documents using Docling for comprehensive document handling.
Supports PDF, DOCX, PPTX, XLSX, HTML, images, and more with advanced
table extraction and layout understanding.

https://github.com/DS4SD/docling
"""

import tempfile
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class DoclingDocumentProcessor:
    """
    Process documents using Docling for comprehensive document handling.

    Docling provides:
    - Advanced PDF processing with layout understanding
    - Table extraction and structure preservation
    - OCR support for scanned documents
    - Multi-format support (PDF, DOCX, PPTX, XLSX, HTML, images)
    - Hierarchical and hybrid chunking for RAG
    """

    # Supported formats by Docling
    SUPPORTED_EXTENSIONS = {
        ".pdf",    # PDF documents
        ".docx",   # Microsoft Word
        ".pptx",   # Microsoft PowerPoint
        ".xlsx",   # Microsoft Excel
        ".html",   # HTML pages
        ".htm",    # HTML pages
        ".png",    # Images
        ".jpg",    # Images
        ".jpeg",   # Images
        ".tiff",   # Images
        ".tif",    # Images
        ".bmp",    # Images
        ".md",     # Markdown
        ".txt",    # Plain text
    }

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_ocr: bool = True,
        max_tokens: int | None = None,
    ):
        """
        Initialize the Docling document processor.

        Args:
            chunk_size: Target size for text chunks (in characters, used for fallback)
            chunk_overlap: Overlap between consecutive chunks (used for fallback)
            use_ocr: Enable OCR for scanned documents (requires additional models)
            max_tokens: Maximum tokens per chunk for HybridChunker (None = auto)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_ocr = use_ocr
        self.max_tokens = max_tokens

        # Lazy initialization of Docling components
        self._converter = None
        self._chunker = None
        self._docling_available = None

    def _check_docling_available(self) -> bool:
        """Check if Docling is installed and available."""
        if self._docling_available is not None:
            return self._docling_available

        try:
            from docling.document_converter import DocumentConverter
            self._docling_available = True
            logger.info("docling_available", status="installed")
        except ImportError:
            self._docling_available = False
            logger.warning(
                "docling_not_available",
                message="Docling not installed. Install with: pip install docling"
            )
        return self._docling_available

    def _get_converter(self):
        """Get or create the Docling DocumentConverter."""
        if self._converter is None:
            from docling.document_converter import DocumentConverter

            # Create converter with default settings
            # Docling will auto-detect format and apply appropriate pipeline
            self._converter = DocumentConverter()
            logger.debug("docling_converter_initialized")

        return self._converter

    def _get_chunker(self):
        """Get or create the Docling HybridChunker for RAG-optimized chunking."""
        if self._chunker is None:
            try:
                from docling.chunking import HybridChunker

                # HybridChunker combines document-aware hierarchical chunking
                # with tokenization-aware size management
                self._chunker = HybridChunker(
                    merge_peers=True,  # Merge small consecutive chunks
                )
                logger.debug("docling_hybrid_chunker_initialized")
            except ImportError:
                # Fall back to HierarchicalChunker if HybridChunker not available
                try:
                    from docling.chunking import HierarchicalChunker
                    self._chunker = HierarchicalChunker(
                        merge_list_items=True,
                    )
                    logger.debug("docling_hierarchical_chunker_initialized")
                except ImportError:
                    logger.warning("docling_chunker_not_available")
                    self._chunker = None

        return self._chunker

    def _fallback_chunk_text(self, text: str) -> list[str]:
        """
        Fallback text chunking when Docling chunker is unavailable.

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
        Process a file using Docling and return chunks.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with chunks, metadata, and full text

        Raises:
            ValueError: If file type is not supported or processing fails
        """
        import traceback

        # Check if file exists
        if not file_path.exists():
            logger.error("file_not_found", path=str(file_path))
            raise ValueError(
                f"File not found at path: {file_path}. The file may have been moved or deleted."
            )

        file_size = file_path.stat().st_size
        suffix = file_path.suffix.lower()

        logger.info(
            "processing_file_docling",
            path=str(file_path),
            size_bytes=file_size,
            extension=suffix,
        )

        # Check if format is supported
        if suffix not in self.SUPPORTED_EXTENSIONS:
            logger.error(
                "unsupported_file_type",
                path=str(file_path),
                extension=suffix,
                supported=list(self.SUPPORTED_EXTENSIONS),
            )
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        # Check if Docling is available
        if not self._check_docling_available():
            raise ImportError(
                "Docling is required for document processing. "
                "Install with: pip install docling"
            )

        try:
            # Convert document using Docling
            converter = self._get_converter()
            result = converter.convert(str(file_path))
            doc = result.document

            # Export to markdown for full text
            full_text = doc.export_to_markdown()

            if not full_text or not full_text.strip():
                logger.warning(
                    "docling_no_text_extracted",
                    path=str(file_path),
                    message="Document may be empty or contain only images without OCR"
                )
                raise ValueError(
                    f"No text could be extracted from {file_path.name}. "
                    "The document may be empty or contain only scanned images."
                )

            # Get document metadata
            page_count = None
            if hasattr(doc, 'pages') and doc.pages:
                page_count = len(doc.pages)

            # Chunk the document
            chunker = self._get_chunker()
            chunks = []

            if chunker is not None:
                try:
                    # Use Docling's document-aware chunking
                    chunk_iter = chunker.chunk(doc)
                    for chunk in chunk_iter:
                        # Get contextualized text (includes metadata)
                        chunk_text = chunker.contextualize(chunk)
                        if chunk_text and chunk_text.strip():
                            chunks.append(chunk_text)

                    logger.info(
                        "docling_chunking_complete",
                        path=str(file_path),
                        chunk_count=len(chunks),
                        chunker_type=type(chunker).__name__,
                    )
                except Exception as e:
                    logger.warning(
                        "docling_chunking_failed",
                        path=str(file_path),
                        error=str(e),
                        message="Falling back to simple chunking"
                    )
                    chunks = self._fallback_chunk_text(full_text)
            else:
                # Fallback to simple chunking
                chunks = self._fallback_chunk_text(full_text)

            if not chunks:
                logger.warning(
                    "no_chunks_generated",
                    path=str(file_path),
                    text_length=len(full_text),
                )
                raise ValueError(
                    f"No text chunks could be generated from {file_path.name}. "
                    "The document may be empty or contain only whitespace."
                )

            # Build metadata
            metadata = {
                "filename": file_path.name,
                "extension": suffix,
                "page_count": page_count,
                "processor": "docling",
                "file_size_bytes": file_size,
            }

            # Add table count if available
            if hasattr(doc, 'tables') and doc.tables:
                metadata["table_count"] = len(doc.tables)

            logger.info(
                "file_processed_docling",
                path=str(file_path),
                chunk_count=len(chunks),
                total_chars=len(full_text),
                pages=page_count,
                tables=metadata.get("table_count", 0),
            )

            return {
                "chunks": chunks,
                "metadata": metadata,
                "full_text": full_text,
            }

        except ImportError:
            raise
        except ValueError:
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "docling_processing_failed",
                path=str(file_path),
                error_type=error_type,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise ValueError(
                f"Failed to process document with Docling ({error_type}): {e}"
            ) from e

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

        Raises:
            ValueError: If processing fails or file type is unsupported
        """
        import traceback

        if not content:
            logger.error("empty_bytes_content", filename=filename)
            raise ValueError(
                f"File {filename} has no content (0 bytes). "
                "Please ensure the file was uploaded correctly."
            )

        suffix = Path(filename).suffix
        logger.info(
            "processing_bytes_docling",
            filename=filename,
            size_bytes=len(content),
            extension=suffix,
        )

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)

            result = await self.process_file(tmp_path)
            return result

        except (ValueError, ImportError):
            raise
        except OSError as e:
            logger.error(
                "temp_file_creation_failed",
                filename=filename,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise ValueError(
                f"Failed to create temporary file for processing {filename}: {e}"
            ) from e
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "process_bytes_failed",
                filename=filename,
                error_type=error_type,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise ValueError(
                f"Failed to process uploaded file {filename} ({error_type}): {e}"
            ) from e
        finally:
            # Clean up temporary file
            if tmp_path and tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception as e:
                    logger.warning(
                        "temp_file_cleanup_failed",
                        path=str(tmp_path),
                        error=str(e),
                    )

    async def process_text(self, text: str, source_name: str = "text") -> dict[str, Any]:
        """
        Process plain text directly (no Docling conversion needed).

        Args:
            text: Text content
            source_name: Name for the source

        Returns:
            Dictionary with chunks and metadata
        """
        chunks = self._fallback_chunk_text(text)

        return {
            "chunks": chunks,
            "metadata": {
                "filename": source_name,
                "extension": ".txt",
                "page_count": None,
                "processor": "docling-text",
            },
            "full_text": text,
        }

    async def process_url(self, url: str) -> dict[str, Any]:
        """
        Process a document from URL using Docling.

        Docling supports direct URL processing for web documents.

        Args:
            url: URL of the document to process

        Returns:
            Dictionary with chunks, metadata, and full text

        Raises:
            ValueError: If processing fails
        """
        import traceback

        logger.info("processing_url_docling", url=url)

        if not self._check_docling_available():
            raise ImportError(
                "Docling is required for URL processing. "
                "Install with: pip install docling"
            )

        try:
            converter = self._get_converter()
            result = converter.convert(url)
            doc = result.document

            full_text = doc.export_to_markdown()

            if not full_text or not full_text.strip():
                raise ValueError(f"No text could be extracted from URL: {url}")

            # Chunk the document
            chunker = self._get_chunker()
            chunks = []

            if chunker is not None:
                try:
                    chunk_iter = chunker.chunk(doc)
                    for chunk in chunk_iter:
                        chunk_text = chunker.contextualize(chunk)
                        if chunk_text and chunk_text.strip():
                            chunks.append(chunk_text)
                except Exception:
                    chunks = self._fallback_chunk_text(full_text)
            else:
                chunks = self._fallback_chunk_text(full_text)

            if not chunks:
                raise ValueError(f"No chunks could be generated from URL: {url}")

            metadata = {
                "filename": url.split("/")[-1] or "web_document",
                "extension": ".html",
                "source_url": url,
                "processor": "docling",
            }

            logger.info(
                "url_processed_docling",
                url=url,
                chunk_count=len(chunks),
                total_chars=len(full_text),
            )

            return {
                "chunks": chunks,
                "metadata": metadata,
                "full_text": full_text,
            }

        except ImportError:
            raise
        except ValueError:
            raise
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "docling_url_processing_failed",
                url=url,
                error_type=error_type,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise ValueError(
                f"Failed to process URL with Docling ({error_type}): {e}"
            ) from e


# Factory function to get the appropriate processor
def get_document_processor(
    use_docling: bool = True,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    **kwargs,
):
    """
    Get the appropriate document processor.

    Args:
        use_docling: Whether to use Docling (falls back to legacy if unavailable)
        chunk_size: Target chunk size
        chunk_overlap: Chunk overlap
        **kwargs: Additional arguments for the processor

    Returns:
        Document processor instance
    """
    if use_docling:
        processor = DoclingDocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            **kwargs,
        )
        # Check if Docling is actually available
        if processor._check_docling_available():
            return processor
        logger.warning(
            "docling_fallback",
            message="Docling not available, falling back to legacy processor"
        )

    # Fall back to legacy processor
    from src.rag.document_processor import DocumentProcessor
    return DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
