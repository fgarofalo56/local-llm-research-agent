"""Centralized configuration service with validation and hot reload."""

import os
import re
from pathlib import Path
from typing import Any

import structlog
import yaml

logger = structlog.get_logger(__name__)


class ConfigService:
    """
    Centralized configuration management with environment variable substitution.

    Supports:
    - Multi-environment configuration (default, development, production)
    - Environment variable substitution with defaults
    - Dot notation access (e.g., config.get('database.sample.host'))
    - Hot reload in development mode
    - Configuration validation
    """

    _instance: "ConfigService | None" = None
    _config: dict[str, Any] | None = None
    _environment: str = "development"
    _config_dir: Path | None = None

    def __init__(self) -> None:
        """Initialize ConfigService (use get_instance() instead)."""
        if ConfigService._instance is not None:
            raise RuntimeError("Use ConfigService.get_instance() instead of direct instantiation")
        self._config = {}
        self._environment = os.getenv("ENVIRONMENT", "development")
        # Set config directory relative to project root
        project_root = Path(__file__).parent.parent.parent
        self._config_dir = project_root / "config"

    @classmethod
    def get_instance(cls) -> "ConfigService":
        """Get singleton instance of ConfigService."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.load()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (primarily for testing)."""
        cls._instance = None

    def load(self, environment: str | None = None) -> None:
        """
        Load configuration for specified environment.

        Args:
            environment: Environment name (development, production, etc.)
                        If None, uses ENVIRONMENT env var or defaults to 'development'
        """
        if environment is not None:
            self._environment = environment
        else:
            self._environment = os.getenv("ENVIRONMENT", "development")

        logger.info(
            "Loading configuration",
            environment=self._environment,
            config_dir=str(self._config_dir),
        )

        # Load default configuration
        default_config = self._load_yaml_file("default.yaml")

        # Load environment-specific configuration
        env_config = self._load_yaml_file(f"{self._environment}.yaml")

        # Merge configurations (environment overrides default)
        self._config = self._deep_merge(default_config, env_config)

        # Substitute environment variables
        self._config = self._substitute_env_vars(self._config)

        logger.debug("Configuration loaded successfully", config_keys=list(self._config.keys()))

    def _load_yaml_file(self, filename: str) -> dict[str, Any]:
        """Load YAML configuration file."""
        if self._config_dir is None:
            return {}

        file_path = self._config_dir / filename
        if not file_path.exists():
            logger.warning("Configuration file not found", file=str(file_path))
            return {}

        try:
            with open(file_path, encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                logger.debug("Loaded configuration file", file=filename, keys=list(config.keys()))
                return config
        except Exception as e:
            logger.error("Failed to load configuration file", file=filename, error=str(e))
            return {}

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            Merged dictionary with override values taking precedence
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _substitute_env_vars(self, config: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.

        Supports formats:
        - ${VAR_NAME} - Required variable (raises error if not found)
        - ${VAR_NAME:-default} - Variable with default value

        Args:
            config: Configuration value (dict, list, str, or other)

        Returns:
            Configuration with environment variables substituted
        """
        if isinstance(config, dict):
            return {key: self._substitute_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._substitute_env_var_string(config)
        else:
            return config

    def _substitute_env_var_string(self, value: str) -> Any:
        """
        Substitute environment variables in a string.

        Args:
            value: String potentially containing ${VAR_NAME} or ${VAR_NAME:-default}

        Returns:
            Substituted value (converted to appropriate type)
        """
        # Pattern matches ${VAR_NAME} or ${VAR_NAME:-default}
        pattern = r"\$\{([^}:]+)(?::-(.*?))?\}"

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_value = match.group(2)

            # Get environment variable
            env_value = os.getenv(var_name)

            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                logger.warning(
                    "Environment variable not found and no default provided",
                    variable=var_name,
                )
                return ""

        result = re.sub(pattern, replacer, value)

        # Convert to appropriate type
        return self._convert_type(result)

    def _convert_type(self, value: str) -> Any:
        """
        Convert string value to appropriate Python type.

        Args:
            value: String value to convert

        Returns:
            Converted value (bool, int, float, or str)
        """
        # Boolean conversion
        if value.lower() in ("true", "yes", "1"):
            return True
        elif value.lower() in ("false", "no", "0"):
            return False

        # Integer conversion
        try:
            if "." not in value:
                return int(value)
        except ValueError:
            pass

        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key: Configuration key with dot notation (e.g., 'database.sample.host')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            logger.warning("Configuration not loaded, loading now")
            self.load()

        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def reload(self) -> None:
        """
        Reload configuration from files.

        Useful in development mode for hot-reloading configuration changes.
        """
        logger.info("Reloading configuration", environment=self._environment)
        self.load(self._environment)

    def validate(self) -> list[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        # Required fields validation
        required_fields = [
            "ollama.host",
            "database.sample.host",
            "database.backend.host",
        ]

        for field in required_fields:
            value = self.get(field)
            if value is None or value == "":
                errors.append(f"Required configuration missing: {field}")

        # Type validation
        int_fields = [
            ("database.sample.port", 1, 65535),
            ("database.backend.port", 1, 65535),
            ("api.port", 1, 65535),
            ("cache.ttl_seconds", 0, None),
            ("cache.max_size", 1, None),
        ]

        for field, min_val, max_val in int_fields:
            value = self.get(field)
            if value is not None:
                if not isinstance(value, int):
                    errors.append(f"Field must be integer: {field} (got {type(value).__name__})")
                elif min_val is not None and value < min_val:
                    errors.append(f"Field must be >= {min_val}: {field} (got {value})")
                elif max_val is not None and value > max_val:
                    errors.append(f"Field must be <= {max_val}: {field} (got {value})")

        # Enum validation
        vector_store_type = self.get("vector_store.type")
        if vector_store_type not in ("mssql", "redis"):
            errors.append(
                f"Invalid vector_store.type: {vector_store_type} (must be 'mssql' or 'redis')"
            )

        llm_provider = self.get("llm_provider")
        if llm_provider not in ("ollama", "foundry_local"):
            errors.append(
                f"Invalid llm_provider: {llm_provider} (must be 'ollama' or 'foundry_local')"
            )

        return errors

    def get_all(self) -> dict[str, Any]:
        """
        Get entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        if self._config is None:
            self.load()
        return self._config or {}

    @property
    def environment(self) -> str:
        """Get current environment name."""
        return self._environment


def get_config() -> ConfigService:
    """Get singleton ConfigService instance."""
    return ConfigService.get_instance()
