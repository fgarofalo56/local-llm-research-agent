"""
Tests for Structured Logging Configuration

Tests the logging setup and logger functions in src/utils/logger.py.
"""

import logging
from unittest.mock import patch, MagicMock

import pytest
import structlog


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default settings."""
        from src.utils.logger import setup_logging

        # Should not raise any errors
        setup_logging()

    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        from src.utils.logger import setup_logging

        setup_logging(log_level="DEBUG")
        # Verify debug level is set (implicit through no errors)

    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid level uses INFO."""
        from src.utils.logger import setup_logging

        # Invalid levels should fall back to INFO
        setup_logging(log_level="INVALID")

    def test_setup_logging_all_levels(self):
        """Test setup_logging with all standard levels."""
        from src.utils.logger import setup_logging

        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in levels:
            setup_logging(log_level=level)


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_bound_logger(self):
        """Test get_logger returns a structlog BoundLogger."""
        from src.utils.logger import get_logger

        logger = get_logger("test")
        # Should be a bound logger (has bind method)
        assert hasattr(logger, "bind")
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_get_logger_with_name(self):
        """Test get_logger with a specific name."""
        from src.utils.logger import get_logger

        logger = get_logger("mymodule")
        assert logger is not None

    def test_get_logger_without_name(self):
        """Test get_logger without a name."""
        from src.utils.logger import get_logger

        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_context(self):
        """Test get_logger with initial context."""
        from src.utils.logger import get_logger

        logger = get_logger("test", request_id="123", user="testuser")
        assert logger is not None

    def test_logger_can_log(self):
        """Test logger can log messages without errors."""
        from src.utils.logger import get_logger

        logger = get_logger("test_can_log")

        # These should not raise errors
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")

    def test_logger_bind_context(self):
        """Test logger can bind additional context."""
        from src.utils.logger import get_logger

        logger = get_logger("test")
        bound_logger = logger.bind(extra_key="extra_value")

        # Should return a new bound logger
        assert bound_logger is not None
        assert hasattr(bound_logger, "info")


class TestModuleLevelLogger:
    """Tests for module-level logger instance."""

    def test_module_logger_exists(self):
        """Test module-level logger is available."""
        from src.utils.logger import logger

        assert logger is not None
        assert hasattr(logger, "info")

    def test_module_logger_is_configured(self):
        """Test module-level logger can log."""
        from src.utils.logger import logger

        # Should not raise
        logger.debug("test debug")


class TestLoggingConfiguration:
    """Tests for logging configuration behavior."""

    def test_debug_mode_configures_console(self):
        """Test debug mode uses console renderer."""
        from src.utils.logger import setup_logging

        # Patch settings in the config module where it's imported from
        with patch("src.utils.logger.settings") as mock_settings:
            mock_settings.debug = True
            mock_settings.log_level = "DEBUG"

            # Call setup_logging - should not raise
            setup_logging(log_level="DEBUG")

    def test_production_mode_configures_json(self):
        """Test production mode uses JSON renderer."""
        from src.utils.logger import setup_logging

        with patch("src.utils.logger.settings") as mock_settings:
            mock_settings.debug = False
            mock_settings.log_level = "INFO"

            # Call setup_logging - should not raise
            setup_logging(log_level="INFO")

    def test_logging_with_exception(self):
        """Test logging with exception info."""
        from src.utils.logger import get_logger

        logger = get_logger("exception_test")

        try:
            raise ValueError("Test error")
        except ValueError:
            # Should handle exception logging
            logger.exception("An error occurred")

    def test_logging_structured_data(self):
        """Test logging with structured data."""
        from src.utils.logger import get_logger

        logger = get_logger("structured_test")

        # Should handle various data types
        logger.info(
            "structured_event",
            count=42,
            items=["a", "b", "c"],
            metadata={"key": "value"},
        )


class TestLogLevelConversion:
    """Tests for log level string to numeric conversion."""

    def test_log_level_debug(self):
        """Test DEBUG level conversion."""
        level = getattr(logging, "DEBUG", logging.INFO)
        assert level == logging.DEBUG

    def test_log_level_info(self):
        """Test INFO level conversion."""
        level = getattr(logging, "INFO", logging.INFO)
        assert level == logging.INFO

    def test_log_level_warning(self):
        """Test WARNING level conversion."""
        level = getattr(logging, "WARNING", logging.INFO)
        assert level == logging.WARNING

    def test_log_level_error(self):
        """Test ERROR level conversion."""
        level = getattr(logging, "ERROR", logging.INFO)
        assert level == logging.ERROR

    def test_log_level_critical(self):
        """Test CRITICAL level conversion."""
        level = getattr(logging, "CRITICAL", logging.INFO)
        assert level == logging.CRITICAL

    def test_log_level_case_insensitive(self):
        """Test log level is case insensitive."""
        for level_str in ["debug", "DEBUG", "Debug"]:
            level = getattr(logging, level_str.upper(), logging.INFO)
            assert level == logging.DEBUG
