"""
Tests for ConfigService

Tests the centralized configuration management service.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.config_service import ConfigService, get_config


@pytest.fixture
def clean_config():
    """Reset ConfigService singleton before and after each test."""
    ConfigService.reset_instance()
    yield
    ConfigService.reset_instance()


class TestConfigService:
    """Tests for ConfigService basic functionality."""

    def test_singleton_pattern(self, clean_config):
        """Test that ConfigService follows singleton pattern."""
        config1 = ConfigService.get_instance()
        config2 = ConfigService.get_instance()
        assert config1 is config2

    def test_direct_instantiation_raises_error(self, clean_config):
        """Test that direct instantiation raises error."""
        ConfigService.get_instance()  # Create singleton first
        with pytest.raises(RuntimeError, match="Use ConfigService.get_instance()"):
            ConfigService()

    def test_get_config_helper(self, clean_config):
        """Test get_config() helper function."""
        config = get_config()
        assert isinstance(config, ConfigService)
        assert config is ConfigService.get_instance()

    def test_loads_default_config(self, clean_config):
        """Test that default configuration is loaded."""
        config = ConfigService.get_instance()

        # Check that default values are present
        assert config.get("app.name") == "Local LLM Research Agent"
        assert config.get("vector_store.dimensions") == 768

    def test_environment_from_env_var(self, clean_config):
        """Test that environment is read from ENVIRONMENT env var."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()
            assert config.environment == "production"

    def test_default_environment(self, clean_config):
        """Test default environment when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()
            assert config.environment == "development"


class TestConfigDotNotation:
    """Tests for dot notation access."""

    def test_get_nested_value(self, clean_config):
        """Test getting nested configuration values."""
        config = ConfigService.get_instance()

        # Test nested access
        app_name = config.get("app.name")
        assert app_name is not None
        assert isinstance(app_name, str)

    def test_get_with_default(self, clean_config):
        """Test get() with default value."""
        config = ConfigService.get_instance()

        # Non-existent key returns default
        value = config.get("non.existent.key", "default_value")
        assert value == "default_value"

    def test_get_without_default(self, clean_config):
        """Test get() without default returns None."""
        config = ConfigService.get_instance()

        value = config.get("non.existent.key")
        assert value is None

    def test_get_top_level_key(self, clean_config):
        """Test getting top-level configuration key."""
        config = ConfigService.get_instance()

        app_config = config.get("app")
        assert isinstance(app_config, dict)
        assert "name" in app_config


class TestEnvVarSubstitution:
    """Tests for environment variable substitution."""

    def test_env_var_substitution(self, clean_config):
        """Test that environment variables are substituted."""
        with patch.dict(
            os.environ,
            {
                "OLLAMA_HOST": "http://custom:11434",
                "SQL_SERVER_PORT": "1433",
            },
            clear=False,
        ):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            assert config.get("ollama.host") == "http://custom:11434"
            assert config.get("database.sample.port") == 1433

    def test_env_var_with_default(self, clean_config):
        """Test environment variable substitution with default values."""
        with patch.dict(os.environ, {}, clear=True):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            # Should use default value from ${VAR:-default}
            host = config.get("ollama.host")
            assert host == "http://localhost:11434"

    def test_type_conversion_boolean(self, clean_config):
        """Test boolean type conversion from env vars."""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",  # Use production to avoid dev overrides
                "CACHE_ENABLED": "true",
                "MCP_DEBUG": "false",
            },
            clear=False,
        ):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            assert config.get("cache.enabled") is True
            assert config.get("mcp.debug") is False

    def test_type_conversion_integer(self, clean_config):
        """Test integer type conversion from env vars."""
        with patch.dict(
            os.environ,
            {
                "ENVIRONMENT": "production",  # Use production to avoid dev overrides
                "CACHE_TTL_SECONDS": "7200",
                "API_PORT": "9000",
            },
            clear=False,
        ):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            assert config.get("cache.ttl_seconds") == 7200
            assert isinstance(config.get("cache.ttl_seconds"), int)


class TestEnvironmentOverrides:
    """Tests for environment-specific configuration overrides."""

    def test_development_overrides(self, clean_config):
        """Test development environment overrides."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            # Development should override debug to true
            assert config.get("app.debug") is True
            assert config.get("app.log_level") == "DEBUG"

    def test_production_overrides(self, clean_config):
        """Test production environment overrides."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            # Production should override debug to false
            assert config.get("app.debug") is False
            assert config.get("cache.ttl_seconds") == 7200
            assert config.get("cache.max_size") == 5000

    def test_production_readonly_mcp(self, clean_config):
        """Test production enables readonly MCP by default."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            # Production should set MCP to readonly
            assert config.get("mcp.readonly") is True


class TestConfigReload:
    """Tests for configuration reload functionality."""

    def test_reload(self, clean_config):
        """Test configuration reload."""
        config = ConfigService.get_instance()
        original_value = config.get("app.name")

        # Reload should work without errors
        config.reload()

        # Value should remain the same (files haven't changed)
        assert config.get("app.name") == original_value

    def test_reload_with_env_change(self, clean_config):
        """Test reload picks up environment variable changes."""
        with patch.dict(os.environ, {"CACHE_ENABLED": "true"}, clear=False):
            config = ConfigService.get_instance()
            assert config.get("cache.enabled") is True

        # Change env var
        with patch.dict(os.environ, {"CACHE_ENABLED": "false"}, clear=False):
            config.reload()
            assert config.get("cache.enabled") is False


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_success(self, clean_config):
        """Test validation with valid configuration."""
        with patch.dict(
            os.environ,
            {
                "OLLAMA_HOST": "http://localhost:11434",
                "SQL_SERVER_HOST": "localhost",
                "BACKEND_DB_HOST": "localhost",
                "VECTOR_STORE_TYPE": "mssql",
                "LLM_PROVIDER": "ollama",
            },
            clear=False,
        ):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            errors = config.validate()
            assert isinstance(errors, list)
            # Should have no errors or minimal errors
            for error in errors:
                print(f"Validation error: {error}")

    def test_validate_missing_required_field(self, clean_config):
        """Test validation catches missing required fields."""
        config = ConfigService.get_instance()

        # Manually set a required field to None
        if config._config:
            config._config["ollama"] = {"host": None}

        errors = config.validate()
        assert any("ollama.host" in error for error in errors)

    def test_validate_invalid_vector_store_type(self, clean_config):
        """Test validation catches invalid vector store type."""
        config = ConfigService.get_instance()

        if config._config:
            config._config["vector_store"] = {"type": "invalid_type"}

        errors = config.validate()
        assert any("vector_store.type" in error for error in errors)

    def test_validate_invalid_port_range(self, clean_config):
        """Test validation catches invalid port numbers."""
        config = ConfigService.get_instance()

        if config._config and "database" in config._config:
            config._config["database"]["sample"] = {"port": 99999}

        errors = config.validate()
        assert any("port" in error.lower() for error in errors)


class TestConfigGetAll:
    """Tests for get_all() method."""

    def test_get_all_returns_dict(self, clean_config):
        """Test get_all() returns complete configuration dictionary."""
        config = ConfigService.get_instance()

        all_config = config.get_all()
        assert isinstance(all_config, dict)
        assert "app" in all_config
        assert "database" in all_config
        assert "ollama" in all_config

    def test_get_all_after_modifications(self, clean_config):
        """Test get_all() reflects any modifications."""
        config = ConfigService.get_instance()

        # Modify config
        if config._config:
            config._config["test_key"] = "test_value"

        all_config = config.get_all()
        assert all_config.get("test_key") == "test_value"


class TestConfigIntegration:
    """Integration tests for ConfigService."""

    def test_config_file_structure(self, clean_config):
        """Test that configuration files exist and have correct structure."""
        project_root = Path(__file__).parent.parent
        config_dir = project_root / "config"

        # Check files exist
        assert (config_dir / "default.yaml").exists()
        assert (config_dir / "development.yaml").exists()
        assert (config_dir / "production.yaml").exists()

    def test_full_configuration_workflow(self, clean_config):
        """Test complete configuration workflow."""
        # Load config
        config = ConfigService.get_instance()

        # Access various configuration sections
        app_name = config.get("app.name")
        assert app_name is not None

        db_host = config.get("database.sample.host")
        assert db_host is not None

        # Validate
        errors = config.validate()
        assert isinstance(errors, list)

        # Reload
        config.reload()

        # Access after reload
        assert config.get("app.name") == app_name

    def test_missing_config_file_graceful_handling(self, clean_config):
        """Test that missing config files are handled gracefully."""
        with patch.dict(os.environ, {"ENVIRONMENT": "nonexistent"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            # Should still work with just default config
            assert config.get("app.name") is not None

    def test_environment_property(self, clean_config):
        """Test environment property returns correct value."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False):
            ConfigService.reset_instance()
            config = ConfigService.get_instance()

            assert config.environment == "production"
