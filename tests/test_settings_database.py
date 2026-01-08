"""
Tests for Database Settings API Routes
Phase 2+ Database Settings Management

Tests for:
- GET /api/settings/database
- PUT /api/settings/database
- POST /api/settings/database/test
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestDatabaseSettingsModels:
    """Tests for database settings models."""

    def test_database_settings_model(self):
        """Test DatabaseSettings model with default values."""
        from src.api.routes.settings import DatabaseSettings

        settings = DatabaseSettings()
        assert settings.host == "localhost"
        assert settings.port == 1434
        assert settings.database == "LLM_BackEnd"
        assert settings.username == ""
        assert settings.password == ""
        assert settings.trust_certificate is True

    def test_database_settings_response_model(self):
        """Test DatabaseSettingsResponse model."""
        from src.api.routes.settings import DatabaseSettingsResponse

        response = DatabaseSettingsResponse(
            host="localhost",
            port=1434,
            database="LLM_BackEnd",
            username="sa",
            password_set=True,
            trust_certificate=True,
        )
        assert response.host == "localhost"
        assert response.port == 1434
        assert response.database == "LLM_BackEnd"
        assert response.username == "sa"
        assert response.password_set is True
        assert response.trust_certificate is True

    def test_database_connection_test_result_success(self):
        """Test DatabaseConnectionTestResult for successful connection."""
        from src.api.routes.settings import DatabaseConnectionTestResult

        result = DatabaseConnectionTestResult(
            success=True,
            message="Successfully connected",
            latency_ms=45.23,
        )
        assert result.success is True
        assert result.message == "Successfully connected"
        assert result.latency_ms == 45.23
        assert result.error is None

    def test_database_connection_test_result_failure(self):
        """Test DatabaseConnectionTestResult for failed connection."""
        from src.api.routes.settings import DatabaseConnectionTestResult

        result = DatabaseConnectionTestResult(
            success=False,
            message="Connection failed",
            error="Login failed for user 'sa'",
        )
        assert result.success is False
        assert result.message == "Connection failed"
        assert result.latency_ms is None
        assert result.error == "Login failed for user 'sa'"


class TestGetDatabaseSettings:
    """Tests for GET /api/settings/database endpoint."""

    @pytest.mark.asyncio
    async def test_get_database_settings_from_env(self):
        """Test getting database settings from environment variables."""
        from src.api.routes.settings import get_database_settings

        with patch("src.api.routes.settings.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.backend_db_host = "testhost"
            mock_settings.backend_db_port = 1434
            mock_settings.backend_db_name = "TestDB"
            mock_settings.backend_db_username = "testuser"
            mock_settings.backend_db_password = "testpass"
            mock_settings.backend_db_trust_cert = True
            mock_settings.sql_username = "sa"
            mock_settings.sql_password = "fallback"
            mock_get_settings.return_value = mock_settings

            # Clear runtime settings
            import src.api.routes.settings as settings_module

            settings_module._runtime_db_settings = None

            response = await get_database_settings()

            assert response.host == "testhost"
            assert response.port == 1434
            assert response.database == "TestDB"
            assert response.username == "testuser"
            assert response.password_set is True
            assert response.trust_certificate is True

    @pytest.mark.asyncio
    async def test_get_database_settings_fallback_credentials(self):
        """Test getting database settings with fallback to sql_username/password."""
        from src.api.routes.settings import get_database_settings

        with patch("src.api.routes.settings.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.backend_db_host = "localhost"
            mock_settings.backend_db_port = 1434
            mock_settings.backend_db_name = "LLM_BackEnd"
            mock_settings.backend_db_username = ""  # Empty - should fallback
            mock_settings.backend_db_password = ""  # Empty - should fallback
            mock_settings.backend_db_trust_cert = True
            mock_settings.sql_username = "sa"
            mock_settings.sql_password = "fallback_password"
            mock_get_settings.return_value = mock_settings

            # Clear runtime settings
            import src.api.routes.settings as settings_module

            settings_module._runtime_db_settings = None

            response = await get_database_settings()

            assert response.username == "sa"
            assert response.password_set is True


class TestUpdateDatabaseSettings:
    """Tests for PUT /api/settings/database endpoint."""

    @pytest.mark.asyncio
    async def test_update_database_settings(self):
        """Test updating database settings."""
        # Clear runtime settings
        import src.api.routes.settings as settings_module
        from src.api.routes.settings import (
            DatabaseSettings,
            update_database_settings,
        )

        settings_module._runtime_db_settings = None

        new_settings = DatabaseSettings(
            host="newhost",
            port=1435,
            database="NewDB",
            username="newuser",
            password="newpass",
            trust_certificate=False,
        )

        response = await update_database_settings(new_settings)

        assert response.host == "newhost"
        assert response.port == 1435
        assert response.database == "NewDB"
        assert response.username == "newuser"
        assert response.password_set is True
        assert response.trust_certificate is False

        # Verify runtime settings were stored
        assert settings_module._runtime_db_settings is not None
        assert settings_module._runtime_db_settings.host == "newhost"


class TestDatabaseConnectionTest:
    """Tests for POST /api/settings/database/test endpoint."""

    @pytest.mark.asyncio
    async def test_connection_test_success(self):
        """Test successful database connection."""
        # Clear runtime settings
        import src.api.routes.settings as settings_module
        from src.api.routes.settings import (
            DatabaseSettings,
            test_database_connection,
        )

        settings_module._runtime_db_settings = None

        test_settings = DatabaseSettings(
            host="localhost",
            port=1434,
            database="LLM_BackEnd",
            username="sa",
            password="password",
            trust_certificate=True,
        )

        # Mock aioodbc connection
        mock_cursor = AsyncMock()
        mock_cursor.fetchone = AsyncMock(return_value=(1,))
        mock_cursor.execute = AsyncMock()
        mock_cursor.close = AsyncMock()

        mock_conn = AsyncMock()
        mock_conn.cursor = AsyncMock(return_value=mock_cursor)
        mock_conn.close = AsyncMock()

        with patch("aioodbc.connect", AsyncMock(return_value=mock_conn)):
            result = await test_database_connection(test_settings)

            assert result.success is True
            assert "Successfully connected" in result.message
            assert result.latency_ms is not None
            assert result.latency_ms >= 0  # May be 0.0 in mocked fast tests
            assert result.error is None

    @pytest.mark.asyncio
    async def test_connection_test_authentication_failure(self):
        """Test database connection with authentication failure."""
        from src.api.routes.settings import (
            DatabaseSettings,
            test_database_connection,
        )

        test_settings = DatabaseSettings(
            host="localhost",
            port=1434,
            database="LLM_BackEnd",
            username="baduser",
            password="badpass",
            trust_certificate=True,
        )

        # Mock aioodbc to raise authentication error
        with patch(
            "aioodbc.connect",
            AsyncMock(side_effect=Exception("Login failed for user 'baduser'")),
        ):
            result = await test_database_connection(test_settings)

            assert result.success is False
            assert "Authentication failed" in result.message
            assert result.error is not None
            assert "Login failed" in result.error

    @pytest.mark.asyncio
    async def test_connection_test_database_not_found(self):
        """Test database connection with non-existent database."""
        from src.api.routes.settings import (
            DatabaseSettings,
            test_database_connection,
        )

        test_settings = DatabaseSettings(
            host="localhost",
            port=1434,
            database="NonExistentDB",
            username="sa",
            password="password",
            trust_certificate=True,
        )

        # Mock aioodbc to raise database not found error
        with patch(
            "aioodbc.connect",
            AsyncMock(side_effect=Exception("Cannot open database 'NonExistentDB'")),
        ):
            result = await test_database_connection(test_settings)

            assert result.success is False
            assert "not found or not accessible" in result.message
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_connection_test_server_unreachable(self):
        """Test database connection with unreachable server."""
        from src.api.routes.settings import (
            DatabaseSettings,
            test_database_connection,
        )

        test_settings = DatabaseSettings(
            host="unreachable.server",
            port=1434,
            database="LLM_BackEnd",
            username="sa",
            password="password",
            trust_certificate=True,
        )

        # Mock aioodbc to raise connection error
        with patch(
            "aioodbc.connect",
            AsyncMock(
                side_effect=Exception("TCP Provider: Error code 0x2749 - Connection timeout")
            ),
        ):
            result = await test_database_connection(test_settings)

            assert result.success is False
            assert "Cannot connect to server" in result.message
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_connection_test_uses_current_settings_when_none_provided(self):
        """Test connection test uses current settings when none provided."""
        from src.api.routes.settings import test_database_connection

        with patch("src.api.routes.settings.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.backend_db_host = "localhost"
            mock_settings.backend_db_port = 1434
            mock_settings.backend_db_name = "LLM_BackEnd"
            mock_settings.backend_db_username = ""
            mock_settings.backend_db_password = ""
            mock_settings.backend_db_trust_cert = True
            mock_settings.sql_username = "sa"
            mock_settings.sql_password = "password"
            mock_get_settings.return_value = mock_settings

            # Clear runtime settings
            import src.api.routes.settings as settings_module

            settings_module._runtime_db_settings = None

            # Mock successful connection
            mock_cursor = AsyncMock()
            mock_cursor.fetchone = AsyncMock(return_value=(1,))
            mock_cursor.execute = AsyncMock()
            mock_cursor.close = AsyncMock()

            mock_conn = AsyncMock()
            mock_conn.cursor = AsyncMock(return_value=mock_cursor)
            mock_conn.close = AsyncMock()

            with patch("aioodbc.connect", AsyncMock(return_value=mock_conn)):
                result = await test_database_connection(None)

                assert result.success is True
                assert "LLM_BackEnd" in result.message
