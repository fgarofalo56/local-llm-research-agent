"""
Docling Document Processor
Phase 2.1+: Enhanced RAG Pipeline with Docling

Processes documents using Docling for comprehensive document handling.
Supports PDF, DOCX, PPTX, XLSX, HTML, images, CSV, AsciiDoc, and more
with advanced table extraction, layout understanding, and OCR.

https://github.com/DS4SD/docling
"""

import os
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
    - OCR support for scanned documents (configurable)
    - Multi-format support (PDF, DOCX, PPTX, XLSX, HTML, images, CSV, etc.)
    - Hierarchical and hybrid chunking for RAG
    """

    # Supported formats by Docling - comprehensive list
    # Maps file extensions to Docling InputFormat enum values
    SUPPORTED_EXTENSIONS = {
        # PDF documents
        ".pdf",
        # Microsoft Office formats
        ".docx",  # Word
        ".pptx",  # PowerPoint
        ".xlsx",  # Excel
        # Web formats
        ".html",
        ".htm",
        ".xhtml",
        # Markup formats
        ".md",
        ".markdown",
        ".adoc",  # AsciiDoc
        ".asciidoc",
        # Data formats
        ".csv",
        # Image formats (for OCR)
        ".png",
        ".jpg",
        ".jpeg",
        ".tiff",
        ".tif",
        ".bmp",
        ".webp",
        ".gif",
        # Caption/subtitle formats
        ".vtt",  # WebVTT
        # Plain text (handled specially - processed as markdown)
        ".txt",
        ".text",
        ".log",
        ".rst",  # reStructuredText
        ".json",  # JSON (Docling JSON format)
    }

    # Extensions that need special handling (not native Docling formats)
    # These will be converted to markdown before processing
    PLAIN_TEXT_EXTENSIONS = {".txt", ".text", ".log", ".rst"}

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        use_ocr: bool | None = None,
        max_tokens: int | None = None,
    ):
        """
        Initialize the Docling document processor.

        Args:
            chunk_size: Target size for text chunks (in characters, used for fallback)
            chunk_overlap: Overlap between consecutive chunks (used for fallback)
            use_ocr: Enable OCR for scanned documents. If None, reads from
                     DOCLING_OCR_ENABLED env var (default: True)
            max_tokens: Maximum tokens per chunk for HybridChunker (None = auto)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_tokens = max_tokens

        # OCR configuration - default to enabled, can be disabled via env var
        if use_ocr is None:
            self.use_ocr = os.getenv("DOCLING_OCR_ENABLED", "true").lower() in (
                "true",
                "1",
                "yes",
            )
        else:
            self.use_ocr = use_ocr

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
                message="Docling not installed. Install with: pip install docling",
            )
        return self._docling_available

    def _get_converter(self):
        """
        Get or create the Docling DocumentConverter.

        Configures the converter with all supported formats and optional OCR.
        """
        if self._converter is None:
            from docling.document_converter import (
                DocumentConverter,
                ImageFormatOption,
                PdfFormatOption,
            )
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import (
                PdfPipelineOptions,
                EasyOcrOptions,
            )

            # Configure PDF pipeline with OCR support
            pdf_pipeline_options = PdfPipelineOptions()
            pdf_pipeline_options.do_table_structure = True

            # Configure OCR based on settings
            if self.use_ocr:
                pdf_pipeline_options.do_ocr = True
                # Configure OCR with EasyOCR engine
                # Languages: en, fr, de, es, etc. (ISO 639-1 codes for EasyOCR)
                ocr_langs = os.getenv("DOCLING_OCR_LANGUAGES", "en").split(",")
                try:
                    # EasyOcrOptions has sensible defaults and works without GPU
                    pdf_pipeline_options.ocr_options = EasyOcrOptions(
                        lang=ocr_langs,
                        use_gpu=False,  # Disable GPU to avoid CUDA dependency issues
                        download_enabled=True,  # Allow downloading OCR models
                    )
                    logger.info("docling_ocr_enabled", engine="easyocr", languages=ocr_langs)
                except Exception as e:
                    logger.warning(
                        "docling_ocr_config_failed",
                        error=str(e),
                        message="OCR will be disabled",
                    )
                    pdf_pipeline_options.do_ocr = False
            else:
                pdf_pipeline_options.do_ocr = False
                logger.debug("docling_ocr_disabled")

            # Configure image pipeline (same OCR settings as PDF)
            image_pipeline_options = PdfPipelineOptions()
            image_pipeline_options.do_ocr = self.use_ocr
            if self.use_ocr:
                try:
                    ocr_langs = os.getenv("DOCLING_OCR_LANGUAGES", "en").split(",")
                    image_pipeline_options.ocr_options = EasyOcrOptions(
                        lang=ocr_langs,
                        use_gpu=False,
                        download_enabled=True,
                    )
                except Exception:
                    image_pipeline_options.do_ocr = False

            # Create converter with format-specific options
            # By specifying format_options, we enable those formats
            format_options = {
                InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options),
                InputFormat.IMAGE: ImageFormatOption(
                    pipeline_options=image_pipeline_options
                ),
                # Other formats use defaults (no special options needed)
            }

            # Create the converter - it will auto-detect and handle all formats
            self._converter = DocumentConverter(
                allowed_formats=[
                    InputFormat.PDF,
                    InputFormat.DOCX,
                    InputFormat.PPTX,
                    InputFormat.XLSX,
                    InputFormat.HTML,
                    InputFormat.IMAGE,
                    InputFormat.MD,
                    InputFormat.ASCIIDOC,
                    InputFormat.CSV,
                    InputFormat.JSON_DOCLING,
                    InputFormat.VTT,
                ],
                format_options=format_options,
            )

            logger.debug(
                "docling_converter_initialized",
                ocr_enabled=self.use_ocr,
                formats_count=11,
            )

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

    def _is_plain_text_file(self, suffix: str) -> bool:
        """Check if file is a plain text file that needs special handling."""
        return suffix.lower() in self.PLAIN_TEXT_EXTENSIONS

    async def _process_plain_text(self, file_path: Path) -> dict[str, Any]:
        """
        Process plain text files directly without Docling.

        Plain text files (.txt, .log, etc.) are not natively supported by Docling,
        so we handle them with simple text processing.

        Args:
            file_path: Path to the text file

        Returns:
            Dictionary with chunks, metadata, and full text
        """
        # Try multiple encodings
        encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                full_text = file_path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError(
                f"Could not decode {file_path.name} with any supported encoding "
                f"(tried: {', '.join(encodings)})"
            )

        if not full_text.strip():
            raise ValueError(f"File {file_path.name} is empty or contains only whitespace")

        # Chunk the text
        chunks = self._fallback_chunk_text(full_text)

        if not chunks:
            raise ValueError(f"No text chunks could be generated from {file_path.name}")

        metadata = {
            "filename": file_path.name,
            "extension": file_path.suffix.lower(),
            "page_count": None,
            "processor": "docling-plaintext",
            "file_size_bytes": file_path.stat().st_size,
        }

        logger.info(
            "plaintext_file_processed",
            path=str(file_path),
            chunk_count=len(chunks),
            total_chars=len(full_text),
        )

        return {
            "chunks": chunks,
            "metadata": metadata,
            "full_text": full_text,
        }

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

        # Handle plain text files specially (not native Docling format)
        if self._is_plain_text_file(suffix):
            return await self._process_plain_text(file_path)

        # Check if Docling is available
        if not self._check_docling_available():
            raise ImportError(
                "Docling is required for document processing. Install with: pip install docling"
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
                    message="Document may be empty or contain only images without OCR",
                )
                raise ValueError(
                    f"No text could be extracted from {file_path.name}. "
                    "The document may be empty or contain only scanned images. "
                    f"OCR is {'enabled' if self.use_ocr else 'disabled - enable with DOCLING_OCR_ENABLED=true'}."
                )

            # Get document metadata
            page_count = None
            if hasattr(doc, "pages") and doc.pages:
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
                        message="Falling back to simple chunking",
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
                "ocr_enabled": self.use_ocr,
            }

            # Add table count if available
            if hasattr(doc, "tables") and doc.tables:
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
            error_msg = str(e)

            # Provide helpful error messages for common issues
            if "format not allowed" in error_msg.lower():
                logger.error(
                    "docling_format_not_allowed",
                    path=str(file_path),
                    extension=suffix,
                    error=error_msg,
                )
                raise ValueError(
                    f"Docling could not process {suffix} file. "
                    f"This format may require additional configuration. Error: {error_msg}"
                ) from e

            logger.error(
                "docling_processing_failed",
                path=str(file_path),
                error_type=error_type,
                error=error_msg,
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
                "Docling is required for URL processing. Install with: pip install docling"
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
            "docling_fallback", message="Docling not available, falling back to legacy processor"
        )

    # Fall back to legacy processor
    from src.rag.document_processor import DocumentProcessor

    return DocumentProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
