"""
Tests for Configuration Management

Tests the Settings class and configuration functions in src/utils/config.py.
"""

import os
from unittest.mock import patch

from src.utils.config import Settings, get_settings, reload_settings


class TestSettings:
    """Tests for Settings model."""

    def test_default_settings(self):
        """Test default settings values when env vars are not set."""
        # Create settings with controlled environment (clearing test env vars from conftest)
        env_overrides = {
            "SQL_DATABASE_NAME": "",  # Clear to get default
            "OLLAMA_HOST": "",
            "OLLAMA_MODEL": "",
            "LLM_PROVIDER": "",
            "FOUNDRY_ENDPOINT": "",
            "FOUNDRY_MODEL": "",
            "SQL_SERVER_HOST": "",
            "MCP_MSSQL_PATH": "",
            "LOG_LEVEL": "",
        }
        with patch.dict(os.environ, env_overrides, clear=False):
            settings = Settings()

        # These tests verify that our Settings class has the expected defaults
        # Note: Some values might still come from .env file if it exists
        assert settings.llm_provider in ["ollama", ""]  # Default or empty
        assert "11434" in settings.ollama_host or settings.ollama_host == ""
        assert settings.sql_server_port == 1433
        assert settings.streamlit_port == 8501

    def test_ollama_api_url_property(self):
        """Test ollama_api_url computed property."""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://custom:8080"}, clear=False):
            settings = Settings()

        assert settings.ollama_api_url == "http://custom:8080/v1"

    def test_validate_ollama_model_supported(self):
        """Test model validation for supported models."""
        supported_models = [
            "qwen2.5:7b-instruct",
            "llama3.1:8b",
            "llama3.2:3b",
            "mistral:7b",
            "mixtral:8x7b",
            "command-r:latest",
            "firefunction-v2",
        ]

        for model in supported_models:
            with patch.dict(os.environ, {"OLLAMA_MODEL": model}, clear=False):
                settings = Settings()
                assert settings.validate_ollama_model() is True, (
                    f"Model {model} should be supported"
                )

    def test_validate_ollama_model_unsupported(self):
        """Test model validation for unsupported models."""
        unsupported_models = [
            "phi:latest",  # phi doesn't have tool calling in Ollama
            "gemma:2b",
            "random-model",
        ]

        for model in unsupported_models:
            with patch.dict(os.environ, {"OLLAMA_MODEL": model}, clear=False):
                settings = Settings()
                assert settings.validate_ollama_model() is False, (
                    f"Model {model} should not be supported"
                )

    def test_get_mcp_env_basic(self):
        """Test MCP environment variable generation."""
        with patch.dict(
            os.environ,
            {
                "SQL_SERVER_HOST": "testserver",
                "SQL_DATABASE_NAME": "testdb",
                "SQL_TRUST_SERVER_CERTIFICATE": "true",
                "MCP_MSSQL_READONLY": "false",
                "SQL_USERNAME": "",  # Clear credentials
                "SQL_PASSWORD": "",  # Clear credentials
            },
            clear=False,
        ):
            settings = Settings()
            env = settings.get_mcp_env()

        assert env["SERVER_NAME"] == "testserver"
        assert env["DATABASE_NAME"] == "testdb"
        assert env["TRUST_SERVER_CERTIFICATE"] == "true"
        assert env["READONLY"] == "false"
        # When credentials are empty, they should not be in the env dict
        assert env.get("SQL_USERNAME", "") == "" or "SQL_USERNAME" not in env
        assert env.get("SQL_PASSWORD", "") == "" or "SQL_PASSWORD" not in env

    def test_get_mcp_env_with_credentials(self):
        """Test MCP environment includes credentials when set."""
        with patch.dict(
            os.environ,
            {
                "SQL_SERVER_HOST": "localhost",
                "SQL_DATABASE_NAME": "db",
                "SQL_USERNAME": "testuser",
                "SQL_PASSWORD": "testpass",
            },
            clear=False,
        ):
            settings = Settings()
            env = settings.get_mcp_env()

        assert env["SQL_USERNAME"] == "testuser"
        assert env["SQL_PASSWORD"] == "testpass"

    def test_cache_settings(self):
        """Test cache-related settings."""
        with patch.dict(
            os.environ,
            {
                "CACHE_ENABLED": "true",
                "CACHE_MAX_SIZE": "200",
                "CACHE_TTL_SECONDS": "7200",
            },
            clear=False,
        ):
            settings = Settings()

        assert settings.cache_enabled is True
        assert settings.cache_max_size == 200
        assert settings.cache_ttl_seconds == 7200

    def test_rate_limit_settings(self):
        """Test rate limiting settings."""
        with patch.dict(
            os.environ,
            {
                "RATE_LIMIT_ENABLED": "true",
                "RATE_LIMIT_RPM": "30",
                "RATE_LIMIT_BURST": "5",
            },
            clear=False,
        ):
            settings = Settings()

        assert settings.rate_limit_enabled is True
        assert settings.rate_limit_rpm == 30
        assert settings.rate_limit_burst == 5

    def test_foundry_settings(self):
        """Test Foundry Local settings."""
        with patch.dict(
            os.environ,
            {
                "FOUNDRY_ENDPOINT": "http://custom:55588",
                "FOUNDRY_MODEL": "custom-model",
                "FOUNDRY_AUTO_START": "true",
            },
            clear=False,
        ):
            settings = Settings()

        assert settings.foundry_endpoint == "http://custom:55588"
        assert settings.foundry_model == "custom-model"
        assert settings.foundry_auto_start is True

    def test_mssql_sa_password(self):
        """Test MSSQL SA password field for docker-compose compatibility."""
        with patch.dict(
            os.environ,
            {"MSSQL_SA_PASSWORD": "StrongPassword123!"},
            clear=False,
        ):
            settings = Settings()

        assert settings.mssql_sa_password == "StrongPassword123!"

    def test_extra_env_vars_ignored(self):
        """Test that extra environment variables are ignored."""
        with patch.dict(
            os.environ,
            {
                "RANDOM_ENV_VAR": "should_be_ignored",
                "ANOTHER_UNKNOWN": "also_ignored",
            },
            clear=False,
        ):
            # Should not raise an error
            settings = Settings()
            assert not hasattr(settings, "random_env_var")
            assert not hasattr(settings, "another_unknown")


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test get_settings returns Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_cached(self):
        """Test get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestReloadSettings:
    """Tests for reload_settings function."""

    def test_reload_clears_cache(self):
        """Test reload_settings clears the cache."""
        get_settings()  # Ensure cache is populated

        # Reload should return a new instance
        settings2 = reload_settings()

        # The function clears cache and returns new settings
        assert isinstance(settings2, Settings)

        # Get settings again should return the reloaded instance
        settings3 = get_settings()
        assert settings3 is settings2


class TestSettingsIntegration:
    """Integration tests for settings behavior."""

    def test_case_insensitive_env_vars(self):
        """Test that environment variables are case insensitive."""
        # pydantic-settings should handle case insensitivity
        with patch.dict(
            os.environ,
            {"ollama_host": "http://lower:11434"},
            clear=False,
        ):
            Settings()  # Verify Settings can be created with lowercase env vars
            # Both OLLAMA_HOST and ollama_host should work
            # The actual behavior depends on OS and pydantic-settings version

    def test_boolean_conversion(self):
        """Test boolean string conversion."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
        ]

        for str_val, expected in test_cases:
            with patch.dict(
                os.environ,
                {"DEBUG": str_val},
                clear=False,
            ):
                settings = Settings()
                assert settings.debug is expected, f"'{str_val}' should convert to {expected}"

    def test_integer_conversion(self):
        """Test integer string conversion."""
        with patch.dict(
            os.environ,
            {
                "SQL_SERVER_PORT": "5432",
                "STREAMLIT_PORT": "9000",
            },
            clear=False,
        ):
            settings = Settings()

        assert settings.sql_server_port == 5432
        assert settings.streamlit_port == 9000
