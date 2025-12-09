"""
Tests for Health Check Utilities

Tests the health check functionality for system components.
"""

import pytest

from src.utils.health import (
    ComponentHealth,
    HealthStatus,
    SystemHealth,
    format_health_report,
)


class TestHealthStatus:
    """Tests for HealthStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNKNOWN.value == "unknown"


class TestComponentHealth:
    """Tests for ComponentHealth dataclass."""

    def test_basic_creation(self):
        """Test creating a ComponentHealth."""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="All good",
        )
        assert health.name == "test"
        assert health.status == HealthStatus.HEALTHY
        assert health.message == "All good"
        assert health.latency_ms is None
        assert health.details == {}

    def test_with_latency(self):
        """Test ComponentHealth with latency."""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=42.5,
        )
        assert health.latency_ms == 42.5

    def test_with_details(self):
        """Test ComponentHealth with details."""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            details={"host": "localhost", "port": 1433},
        )
        assert health.details["host"] == "localhost"
        assert health.details["port"] == 1433

    def test_to_dict(self):
        """Test conversion to dictionary."""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.HEALTHY,
            message="OK",
            latency_ms=100.5,
            details={"key": "value"},
        )
        result = health.to_dict()

        assert result["name"] == "test"
        assert result["status"] == "healthy"
        assert result["message"] == "OK"
        assert result["latency_ms"] == 100.5
        assert result["details"] == {"key": "value"}

    def test_to_dict_without_optional(self):
        """Test to_dict without optional fields."""
        health = ComponentHealth(
            name="test",
            status=HealthStatus.UNHEALTHY,
            message="Failed",
        )
        result = health.to_dict()

        assert "latency_ms" not in result
        assert "details" not in result


class TestSystemHealth:
    """Tests for SystemHealth dataclass."""

    def test_basic_creation(self):
        """Test creating SystemHealth."""
        health = SystemHealth(status=HealthStatus.HEALTHY)

        assert health.status == HealthStatus.HEALTHY
        assert health.components == []
        assert health.timestamp  # Auto-generated

    def test_with_components(self):
        """Test SystemHealth with components."""
        components = [
            ComponentHealth(name="a", status=HealthStatus.HEALTHY, message="OK"),
            ComponentHealth(name="b", status=HealthStatus.DEGRADED, message="Warn"),
        ]
        health = SystemHealth(status=HealthStatus.DEGRADED, components=components)

        assert len(health.components) == 2
        assert health.components[0].name == "a"

    def test_is_healthy(self):
        """Test is_healthy property."""
        healthy = SystemHealth(status=HealthStatus.HEALTHY)
        unhealthy = SystemHealth(status=HealthStatus.UNHEALTHY)
        degraded = SystemHealth(status=HealthStatus.DEGRADED)

        assert healthy.is_healthy is True
        assert unhealthy.is_healthy is False
        assert degraded.is_healthy is False

    def test_to_dict(self):
        """Test conversion to dictionary."""
        components = [
            ComponentHealth(name="test", status=HealthStatus.HEALTHY, message="OK"),
        ]
        health = SystemHealth(status=HealthStatus.HEALTHY, components=components)
        result = health.to_dict()

        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert len(result["components"]) == 1
        assert result["components"][0]["name"] == "test"


class TestFormatHealthReport:
    """Tests for format_health_report function."""

    def test_basic_format(self):
        """Test basic report formatting."""
        components = [
            ComponentHealth(name="ollama", status=HealthStatus.HEALTHY, message="OK"),
            ComponentHealth(name="mcp", status=HealthStatus.UNHEALTHY, message="Not found"),
        ]
        health = SystemHealth(status=HealthStatus.DEGRADED, components=components)

        report = format_health_report(health)

        assert "System Health Report" in report
        assert "DEGRADED" in report
        assert "ollama" in report
        assert "mcp" in report
        assert "[OK]" in report
        assert "[FAIL]" in report

    def test_verbose_format(self):
        """Test verbose report formatting."""
        components = [
            ComponentHealth(
                name="test",
                status=HealthStatus.HEALTHY,
                message="OK",
                latency_ms=50.0,
                details={"host": "localhost"},
            ),
        ]
        health = SystemHealth(status=HealthStatus.HEALTHY, components=components)

        report = format_health_report(health, verbose=True)

        assert "host: localhost" in report


class TestHealthCheckIntegration:
    """Integration tests for health checks."""

    @pytest.mark.asyncio
    async def test_ollama_check_offline(self):
        """Test Ollama check when service is offline."""
        # This test doesn't require Ollama to be running
        from src.utils.health import check_ollama_health

        # May succeed or fail depending on environment
        result = await check_ollama_health()
        assert result.name == "ollama"
        assert result.status in [
            HealthStatus.HEALTHY,
            HealthStatus.UNHEALTHY,
            HealthStatus.DEGRADED,
        ]

    @pytest.mark.asyncio
    async def test_mcp_server_check(self):
        """Test MCP server check."""
        from src.utils.health import check_mcp_server_health

        result = await check_mcp_server_health()
        assert result.name == "mcp_server"
        # Status depends on configuration
        assert result.status in HealthStatus

    @pytest.mark.asyncio
    async def test_run_health_checks(self):
        """Test running all health checks."""
        from src.utils.health import run_health_checks

        result = await run_health_checks(include_database=False)

        assert result.status in HealthStatus
        assert len(result.components) >= 2  # At least Ollama and MCP
        assert result.timestamp
