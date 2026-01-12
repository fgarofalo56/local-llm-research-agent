"""
Test DoclingDocumentProcessor
Phase 2.1: Backend Infrastructure & RAG Pipeline

Dedicated tests for DoclingDocumentProcessor covering:
- All supported file formats (PDF, DOCX, PPTX, XLSX, HTML, MD, CSV, images, etc.)
- Plain text file handling (.txt, .log, .rst)
- OCR configuration
- Error handling and user-friendly error messages
- Chunking behavior
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.rag.docling_processor import DoclingDocumentProcessor, get_document_processor


class TestDoclingProcessorInitialization:
    """Test processor initialization and configuration."""

    def test_default_initialization(self):
        """Test processor initializes with default values."""
        processor = DoclingDocumentProcessor()

        assert processor.chunk_size == 500
        assert processor.chunk_overlap == 50
        assert processor.use_ocr is True  # Default: enabled
        assert processor._converter is None  # Lazy initialization
        assert processor._chunker is None

    def test_custom_initialization(self):
        """Test processor accepts custom parameters."""
        processor = DoclingDocumentProcessor(
            chunk_size=1000,
            chunk_overlap=100,
            use_ocr=False,
            max_tokens=512,
        )

        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 100
        assert processor.use_ocr is False
        assert processor.max_tokens == 512

    def test_ocr_disabled_via_env(self, monkeypatch):
        """Test OCR can be disabled via environment variable."""
        monkeypatch.setenv("DOCLING_OCR_ENABLED", "false")

        processor = DoclingDocumentProcessor()
        assert processor.use_ocr is False

    def test_ocr_enabled_via_env(self, monkeypatch):
        """Test OCR can be enabled via environment variable."""
        monkeypatch.setenv("DOCLING_OCR_ENABLED", "true")

        processor = DoclingDocumentProcessor()
        assert processor.use_ocr is True

    def test_supported_extensions_comprehensive(self):
        """Test all supported extensions are defined."""
        processor = DoclingDocumentProcessor()

        # PDF
        assert ".pdf" in processor.SUPPORTED_EXTENSIONS

        # Microsoft Office
        assert ".docx" in processor.SUPPORTED_EXTENSIONS
        assert ".pptx" in processor.SUPPORTED_EXTENSIONS
        assert ".xlsx" in processor.SUPPORTED_EXTENSIONS

        # Web formats
        assert ".html" in processor.SUPPORTED_EXTENSIONS
        assert ".htm" in processor.SUPPORTED_EXTENSIONS
        assert ".xhtml" in processor.SUPPORTED_EXTENSIONS

        # Markup formats
        assert ".md" in processor.SUPPORTED_EXTENSIONS
        assert ".markdown" in processor.SUPPORTED_EXTENSIONS
        assert ".adoc" in processor.SUPPORTED_EXTENSIONS
        assert ".asciidoc" in processor.SUPPORTED_EXTENSIONS

        # Data formats
        assert ".csv" in processor.SUPPORTED_EXTENSIONS

        # Image formats
        assert ".png" in processor.SUPPORTED_EXTENSIONS
        assert ".jpg" in processor.SUPPORTED_EXTENSIONS
        assert ".jpeg" in processor.SUPPORTED_EXTENSIONS
        assert ".tiff" in processor.SUPPORTED_EXTENSIONS
        assert ".tif" in processor.SUPPORTED_EXTENSIONS
        assert ".bmp" in processor.SUPPORTED_EXTENSIONS
        assert ".webp" in processor.SUPPORTED_EXTENSIONS
        assert ".gif" in processor.SUPPORTED_EXTENSIONS

        # Caption formats
        assert ".vtt" in processor.SUPPORTED_EXTENSIONS

        # Plain text
        assert ".txt" in processor.SUPPORTED_EXTENSIONS
        assert ".text" in processor.SUPPORTED_EXTENSIONS
        assert ".log" in processor.SUPPORTED_EXTENSIONS
        assert ".rst" in processor.SUPPORTED_EXTENSIONS

        # JSON
        assert ".json" in processor.SUPPORTED_EXTENSIONS

    def test_plain_text_extensions_defined(self):
        """Test plain text extensions requiring special handling are defined."""
        processor = DoclingDocumentProcessor()

        assert ".txt" in processor.PLAIN_TEXT_EXTENSIONS
        assert ".text" in processor.PLAIN_TEXT_EXTENSIONS
        assert ".log" in processor.PLAIN_TEXT_EXTENSIONS
        assert ".rst" in processor.PLAIN_TEXT_EXTENSIONS


class TestPlainTextProcessing:
    """Test plain text file processing (non-Docling formats)."""

    @pytest.mark.asyncio
    async def test_txt_file_processing(self, tmp_path):
        """Test .txt file processing."""
        processor = DoclingDocumentProcessor()

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is test content.\nLine 2.\nLine 3.", encoding="utf-8")

        result = await processor.process_file(txt_file)

        assert "chunks" in result
        assert len(result["chunks"]) > 0
        assert "metadata" in result
        assert result["metadata"]["processor"] == "docling-plaintext"
        assert result["metadata"]["filename"] == "test.txt"
        assert "full_text" in result
        assert "test content" in result["full_text"]

    @pytest.mark.asyncio
    async def test_log_file_processing(self, tmp_path):
        """Test .log file processing."""
        processor = DoclingDocumentProcessor()

        log_file = tmp_path / "app.log"
        log_file.write_text(
            "[2024-01-01] INFO: Application started\n"
            "[2024-01-01] DEBUG: Loading config\n"
            "[2024-01-01] INFO: Ready\n",
            encoding="utf-8",
        )

        result = await processor.process_file(log_file)

        assert result["metadata"]["processor"] == "docling-plaintext"
        assert result["metadata"]["extension"] == ".log"
        assert "Application started" in result["full_text"]

    @pytest.mark.asyncio
    async def test_rst_file_processing(self, tmp_path):
        """Test .rst (reStructuredText) file processing."""
        processor = DoclingDocumentProcessor()

        rst_file = tmp_path / "readme.rst"
        rst_file.write_text(
            "Title\n=====\n\nThis is a paragraph.\n\nSection\n-------\n\nMore content.",
            encoding="utf-8",
        )

        result = await processor.process_file(rst_file)

        assert result["metadata"]["processor"] == "docling-plaintext"
        assert result["metadata"]["extension"] == ".rst"

    @pytest.mark.asyncio
    async def test_empty_txt_file_raises_error(self, tmp_path):
        """Test empty text file raises appropriate error."""
        processor = DoclingDocumentProcessor()

        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("", encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            await processor.process_file(empty_file)

        assert "empty" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_whitespace_only_txt_file_raises_error(self, tmp_path):
        """Test whitespace-only file raises appropriate error."""
        processor = DoclingDocumentProcessor()

        ws_file = tmp_path / "whitespace.txt"
        ws_file.write_text("   \n\t\n   ", encoding="utf-8")

        with pytest.raises(ValueError) as exc_info:
            await processor.process_file(ws_file)

        assert "empty" in str(exc_info.value).lower() or "whitespace" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_utf8_encoding(self, tmp_path):
        """Test UTF-8 encoded files are processed correctly."""
        processor = DoclingDocumentProcessor()

        utf8_file = tmp_path / "utf8.txt"
        utf8_file.write_text("Hello World! Special chars: cafe, naive, resume", encoding="utf-8")

        result = await processor.process_file(utf8_file)

        assert "cafe" in result["full_text"]

    @pytest.mark.asyncio
    async def test_latin1_encoding_fallback(self, tmp_path):
        """Test latin-1 encoding fallback works."""
        processor = DoclingDocumentProcessor()

        latin1_file = tmp_path / "latin1.txt"
        latin1_file.write_bytes("Hello World with latin-1 char: \xe9".encode("latin-1"))

        result = await processor.process_file(latin1_file)

        assert "Hello World" in result["full_text"]


class TestDoclingFormatProcessing:
    """Test Docling-native format processing."""

    @pytest.mark.asyncio
    async def test_markdown_processing(self, tmp_path):
        """Test markdown file processing via Docling."""
        processor = DoclingDocumentProcessor()

        md_file = tmp_path / "test.md"
        md_file.write_text(
            "# Heading 1\n\nParagraph content here.\n\n## Heading 2\n\n- Item 1\n- Item 2\n",
            encoding="utf-8",
        )

        result = await processor.process_file(md_file)

        assert "chunks" in result
        assert result["metadata"]["processor"] == "docling"
        assert result["metadata"]["extension"] == ".md"

    @pytest.mark.asyncio
    async def test_csv_processing(self, tmp_path):
        """Test CSV file processing via Docling."""
        processor = DoclingDocumentProcessor()

        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age,city\nAlice,30,NYC\nBob,25,LA\n", encoding="utf-8")

        result = await processor.process_file(csv_file)

        assert "chunks" in result
        assert result["metadata"]["processor"] == "docling"
        assert result["metadata"]["extension"] == ".csv"
        # Docling should detect table structure
        assert result["metadata"].get("table_count", 0) >= 1

    @pytest.mark.asyncio
    async def test_html_processing(self, tmp_path):
        """Test HTML file processing via Docling."""
        processor = DoclingDocumentProcessor()

        html_file = tmp_path / "page.html"
        html_file.write_text(
            """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<h1>Title</h1>
<p>Content paragraph.</p>
<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>
</body>
</html>""",
            encoding="utf-8",
        )

        result = await processor.process_file(html_file)

        assert "chunks" in result
        assert result["metadata"]["processor"] == "docling"
        assert result["metadata"]["extension"] == ".html"


class TestErrorHandling:
    """Test error handling and user-friendly messages."""

    @pytest.mark.asyncio
    async def test_unsupported_extension_error(self, tmp_path):
        """Test unsupported file extension raises clear error."""
        processor = DoclingDocumentProcessor()

        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("content")

        with pytest.raises(ValueError) as exc_info:
            await processor.process_file(unsupported)

        error_msg = str(exc_info.value)
        assert "unsupported" in error_msg.lower()
        assert ".xyz" in error_msg.lower()
        assert "supported formats" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_file_not_found_error(self, tmp_path):
        """Test non-existent file raises clear error."""
        processor = DoclingDocumentProcessor()

        non_existent = tmp_path / "does_not_exist.pdf"

        with pytest.raises(ValueError) as exc_info:
            await processor.process_file(non_existent)

        error_msg = str(exc_info.value)
        assert "not found" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_empty_bytes_error(self):
        """Test empty bytes content raises clear error."""
        processor = DoclingDocumentProcessor()

        with pytest.raises(ValueError) as exc_info:
            await processor.process_bytes(b"", "test.pdf")

        error_msg = str(exc_info.value)
        assert "0 bytes" in error_msg.lower() or "no content" in error_msg.lower()


class TestProcessBytes:
    """Test process_bytes method."""

    @pytest.mark.asyncio
    async def test_process_bytes_txt(self):
        """Test processing bytes for text file."""
        processor = DoclingDocumentProcessor()

        content = b"This is test content from bytes."
        result = await processor.process_bytes(content, "test.txt")

        assert "chunks" in result
        assert len(result["chunks"]) > 0
        assert "test content" in result["full_text"]

    @pytest.mark.asyncio
    async def test_process_bytes_md(self):
        """Test processing bytes for markdown file."""
        processor = DoclingDocumentProcessor()

        content = b"# Test Heading\n\nParagraph content."
        result = await processor.process_bytes(content, "test.md")

        assert "chunks" in result
        assert result["metadata"]["extension"] == ".md"


class TestProcessText:
    """Test process_text method."""

    @pytest.mark.asyncio
    async def test_process_text_basic(self):
        """Test direct text processing."""
        processor = DoclingDocumentProcessor()

        text = "This is direct text content for processing."
        result = await processor.process_text(text, "direct_input")

        assert "chunks" in result
        assert result["metadata"]["processor"] == "docling-text"
        assert result["full_text"] == text

    @pytest.mark.asyncio
    async def test_process_text_empty(self):
        """Test processing empty text."""
        processor = DoclingDocumentProcessor()

        result = await processor.process_text("", "empty_input")

        assert result["chunks"] == []
        assert result["full_text"] == ""


class TestChunking:
    """Test chunking behavior."""

    @pytest.mark.asyncio
    async def test_fallback_chunking(self, tmp_path):
        """Test fallback chunking for text files."""
        processor = DoclingDocumentProcessor(chunk_size=100, chunk_overlap=10)

        # Create text longer than chunk_size
        txt_file = tmp_path / "long.txt"
        txt_file.write_text("Word " * 100, encoding="utf-8")  # ~500 chars

        result = await processor.process_file(txt_file)

        # Should create multiple chunks
        assert len(result["chunks"]) > 1

    def test_fallback_chunk_text_sentence_boundary(self):
        """Test fallback chunking respects sentence boundaries."""
        processor = DoclingDocumentProcessor(chunk_size=50, chunk_overlap=10)

        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = processor._fallback_chunk_text(text)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Chunks should end at sentence boundaries where possible
        for chunk in chunks[:-1]:  # Exclude last chunk
            # Most chunks should end with a sentence terminator
            assert chunk.rstrip().endswith((".", "!", "?")) or len(chunk) >= 40


class TestGetDocumentProcessor:
    """Test the factory function."""

    def test_get_processor_returns_docling(self):
        """Test factory returns DoclingDocumentProcessor when available."""
        processor = get_document_processor(use_docling=True)

        # Should return DoclingDocumentProcessor if docling is available
        assert processor is not None
        assert hasattr(processor, "SUPPORTED_EXTENSIONS")

    def test_get_processor_respects_parameters(self):
        """Test factory passes parameters correctly."""
        processor = get_document_processor(
            use_docling=True,
            chunk_size=1000,
            chunk_overlap=100,
        )

        assert processor.chunk_size == 1000
        assert processor.chunk_overlap == 100

    def test_get_processor_fallback_when_disabled(self):
        """Test factory returns legacy processor when docling disabled."""
        # Mock docling as unavailable
        with patch.object(
            DoclingDocumentProcessor, "_check_docling_available", return_value=False
        ):
            processor = get_document_processor(use_docling=True)

            # Should fall back to legacy processor
            from src.rag.document_processor import DocumentProcessor

            assert isinstance(processor, DocumentProcessor)


class TestIsPlainTextFile:
    """Test plain text file detection."""

    def test_txt_is_plain_text(self):
        """Test .txt is detected as plain text."""
        processor = DoclingDocumentProcessor()
        assert processor._is_plain_text_file(".txt") is True

    def test_log_is_plain_text(self):
        """Test .log is detected as plain text."""
        processor = DoclingDocumentProcessor()
        assert processor._is_plain_text_file(".log") is True

    def test_rst_is_plain_text(self):
        """Test .rst is detected as plain text."""
        processor = DoclingDocumentProcessor()
        assert processor._is_plain_text_file(".rst") is True

    def test_md_is_not_plain_text(self):
        """Test .md is NOT plain text (handled by Docling)."""
        processor = DoclingDocumentProcessor()
        assert processor._is_plain_text_file(".md") is False

    def test_pdf_is_not_plain_text(self):
        """Test .pdf is NOT plain text."""
        processor = DoclingDocumentProcessor()
        assert processor._is_plain_text_file(".pdf") is False


class TestOCRConfiguration:
    """Test OCR configuration options."""

    def test_ocr_enabled_by_default(self):
        """Test OCR is enabled by default."""
        processor = DoclingDocumentProcessor()
        assert processor.use_ocr is True

    def test_ocr_can_be_disabled(self):
        """Test OCR can be disabled via parameter."""
        processor = DoclingDocumentProcessor(use_ocr=False)
        assert processor.use_ocr is False

    def test_ocr_env_var_false_values(self, monkeypatch):
        """Test various false values for OCR env var."""
        for value in ["false", "0", "no", "FALSE", "NO"]:
            monkeypatch.setenv("DOCLING_OCR_ENABLED", value)
            processor = DoclingDocumentProcessor()
            assert processor.use_ocr is False, f"Failed for value: {value}"

    def test_ocr_env_var_true_values(self, monkeypatch):
        """Test various true values for OCR env var."""
        for value in ["true", "1", "yes", "TRUE", "YES"]:
            monkeypatch.setenv("DOCLING_OCR_ENABLED", value)
            processor = DoclingDocumentProcessor()
            assert processor.use_ocr is True, f"Failed for value: {value}"
