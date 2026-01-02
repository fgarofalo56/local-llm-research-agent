"""
ConfigService Usage Example

Demonstrates how to use the centralized ConfigService for managing application configuration.
"""

import os

from src.services.config_service import ConfigService, get_config


def example_basic_usage():
    """Example: Basic configuration access."""
    print("=== Basic Usage ===\n")

    # Get singleton instance
    config = get_config()

    # Access configuration using dot notation
    app_name = config.get("app.name")
    print(f"Application Name: {app_name}")

    db_host = config.get("database.sample.host")
    print(f"Database Host: {db_host}")

    ollama_host = config.get("ollama.host")
    print(f"Ollama Host: {ollama_host}")

    # Access with default values
    custom_value = config.get("custom.setting", default="default_value")
    print(f"Custom Setting: {custom_value}")

    print()


def example_environment_specific():
    """Example: Environment-specific configuration."""
    print("=== Environment-Specific Configuration ===\n")

    # Reset instance to demonstrate environment switching
    ConfigService.reset_instance()

    # Set environment via env var
    os.environ["ENVIRONMENT"] = "production"

    # Get new instance with production config
    config = ConfigService.get_instance()

    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.get('app.debug')}")
    print(f"Cache TTL: {config.get('cache.ttl_seconds')} seconds")
    print(f"MCP Readonly: {config.get('mcp.readonly')}")

    # Switch back to development
    ConfigService.reset_instance()
    os.environ["ENVIRONMENT"] = "development"
    config = ConfigService.get_instance()

    print(f"\nEnvironment: {config.environment}")
    print(f"Debug Mode: {config.get('app.debug')}")
    print(f"Cache TTL: {config.get('cache.ttl_seconds')} seconds")

    print()


def example_validation():
    """Example: Configuration validation."""
    print("=== Configuration Validation ===\n")

    config = get_config()

    # Validate configuration
    errors = config.validate()

    if errors:
        print("Configuration Errors Found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")

    print()


def example_nested_config():
    """Example: Accessing nested configuration."""
    print("=== Nested Configuration Access ===\n")

    config = get_config()

    # Access nested database configuration
    sample_db = config.get("database.sample")
    if sample_db:
        print("Sample Database Configuration:")
        for key, value in sample_db.items():
            print(f"  {key}: {value}")

    print()


def example_hot_reload():
    """Example: Hot reload configuration (development)."""
    print("=== Hot Reload ===\n")

    config = get_config()

    # Initial value
    initial_debug = config.get("app.debug")
    print(f"Initial Debug Mode: {initial_debug}")

    # Simulate environment variable change
    os.environ["APP_DEBUG"] = "false"

    # Reload configuration
    config.reload()

    # Check updated value
    updated_debug = config.get("app.debug")
    print(f"Updated Debug Mode: {updated_debug}")

    print()


def example_complete_config():
    """Example: Get complete configuration."""
    print("=== Complete Configuration ===\n")

    config = get_config()

    # Get all configuration
    all_config = config.get_all()

    print("Configuration Sections:")
    for section in all_config.keys():
        print(f"  - {section}")

    print()


def example_type_conversion():
    """Example: Type conversion from environment variables."""
    print("=== Type Conversion ===\n")

    config = get_config()

    # Integer values
    cache_ttl = config.get("cache.ttl_seconds")
    print(f"Cache TTL: {cache_ttl} ({type(cache_ttl).__name__})")

    # Boolean values
    cache_enabled = config.get("cache.enabled")
    print(f"Cache Enabled: {cache_enabled} ({type(cache_enabled).__name__})")

    # String values
    ollama_model = config.get("ollama.model")
    print(f"Ollama Model: {ollama_model} ({type(ollama_model).__name__})")

    print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("ConfigService Usage Examples")
    print("=" * 70 + "\n")

    example_basic_usage()
    example_nested_config()
    example_environment_specific()
    example_type_conversion()
    example_validation()
    example_complete_config()
    example_hot_reload()

    print("=" * 70)
    print("Examples Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
