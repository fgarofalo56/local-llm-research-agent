"""
Tests for Database Manager

Tests the multi-database configuration functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.utils.database_manager import DatabaseConfig, DatabaseManager, get_database_manager


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""

    def test_create_config(self):
        """Test creating a database configuration."""
        config = DatabaseConfig(
            name="test_db",
            host="localhost",
            port=1433,
            database="TestDB",
            username="sa",
            password="password123",
        )

        assert config.name == "test_db"
        assert config.host == "localhost"
        assert config.port == 1433
        assert config.database == "TestDB"
        assert config.username == "sa"
        assert config.password == "password123"
        assert config.readonly is False
        assert config.trust_certificate is True

    def test_config_defaults(self):
        """Test default values."""
        config = DatabaseConfig(name="minimal", database="TestDB")

        assert config.host == "localhost"
        assert config.port == 1433
        assert config.username == ""
        assert config.password == ""
        assert config.readonly is False

    def test_connection_string_display_sql_auth(self):
        """Test display connection string with SQL auth."""
        config = DatabaseConfig(
            name="test",
            host="server.example.com",
            port=1433,
            database="MyDB",
            username="myuser",
        )

        display = config.connection_string_display
        assert "server.example.com" in display
        assert "MyDB" in display
        assert "User=myuser" in display

    def test_connection_string_display_windows_auth(self):
        """Test display connection string with Windows auth."""
        config = DatabaseConfig(
            name="test",
            host="localhost",
            database="MyDB",
        )

        display = config.connection_string_display
        assert "Windows Auth" in display

    def test_get_mcp_env(self):
        """Test MCP environment variables generation."""
        config = DatabaseConfig(
            name="test",
            host="dbserver",
            port=1433,
            database="Analytics",
            username="sa",
            password="secret",
            readonly=True,
        )

        env = config.get_mcp_env()

        assert env["SERVER_NAME"] == "dbserver"
        assert env["DATABASE_NAME"] == "Analytics"
        assert env["READONLY"] == "true"
        assert env["SQL_USERNAME"] == "sa"
        assert env["SQL_PASSWORD"] == "secret"


class TestDatabaseManager:
    """Tests for DatabaseManager."""

    def test_default_database_created(self):
        """Test that default database is created on init."""
        manager = DatabaseManager()

        databases = manager.list_databases()
        assert len(databases) >= 1
        assert any(db["name"] == "default" for db in databases)

    def test_default_is_active(self):
        """Test that default database is active."""
        manager = DatabaseManager()

        assert manager.active_name == "default"
        assert manager.active is not None

    def test_add_database(self):
        """Test adding a new database."""
        manager = DatabaseManager()
        config = DatabaseConfig(
            name="production",
            host="prod-server",
            database="ProdDB",
        )

        manager.add_database(config)

        assert manager.get_database("production") is not None
        databases = manager.list_databases()
        assert any(db["name"] == "production" for db in databases)

    def test_remove_database(self):
        """Test removing a database."""
        manager = DatabaseManager()
        config = DatabaseConfig(name="temp", database="TempDB")
        manager.add_database(config)

        assert manager.remove_database("temp") is True
        assert manager.get_database("temp") is None

    def test_cannot_remove_default(self):
        """Test that default database cannot be removed."""
        manager = DatabaseManager()

        assert manager.remove_database("default") is False
        assert manager.get_database("default") is not None

    def test_set_active(self):
        """Test setting active database."""
        manager = DatabaseManager()
        config = DatabaseConfig(name="other", database="OtherDB")
        manager.add_database(config)

        assert manager.set_active("other") is True
        assert manager.active_name == "other"

    def test_set_active_nonexistent(self):
        """Test setting nonexistent database as active."""
        manager = DatabaseManager()

        assert manager.set_active("nonexistent") is False
        assert manager.active_name == "default"

    def test_list_databases_shows_active(self):
        """Test that list shows which database is active."""
        manager = DatabaseManager()
        config = DatabaseConfig(name="secondary", database="SecondDB")
        manager.add_database(config)

        databases = manager.list_databases()
        default_db = next(db for db in databases if db["name"] == "default")
        assert default_db["active"] is True

    def test_save_and_load_file(self):
        """Test saving and loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "databases.json"

            # Create manager and add database
            manager1 = DatabaseManager()
            config = DatabaseConfig(
                name="saved",
                host="saved-host",
                database="SavedDB",
                description="A saved database",
            )
            manager1.add_database(config)
            manager1.save_to_file(filepath)

            # Load in new manager
            manager2 = DatabaseManager(config_file=filepath)

            saved_db = manager2.get_database("saved")
            assert saved_db is not None
            assert saved_db.host == "saved-host"
            assert saved_db.database == "SavedDB"

    def test_load_invalid_file(self):
        """Test loading from invalid file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.json"
            filepath.write_text("not valid json{")

            manager = DatabaseManager(config_file=filepath)

            # Should have default but not crash
            assert manager.get_database("default") is not None


class TestGetDatabaseManager:
    """Tests for get_database_manager helper."""

    def test_returns_manager(self):
        """Test that helper returns a manager."""
        manager = get_database_manager()

        assert isinstance(manager, DatabaseManager)
        assert manager.active is not None

    def test_with_nonexistent_file(self):
        """Test with nonexistent config file."""
        manager = get_database_manager(config_file=Path("/nonexistent/path/databases.json"))

        # Should work with defaults
        assert manager.get_database("default") is not None
