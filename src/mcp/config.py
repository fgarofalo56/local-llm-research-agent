"""
MCP Server Configuration Models

Pydantic models for managing MCP server configurations.
Supports multiple server types with validation and persistence.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class TransportType(str, Enum):
    """MCP transport types per MCP specification."""

    STDIO = "stdio"  # Subprocess-based (command + args)
    STREAMABLE_HTTP = "streamable_http"  # HTTP endpoint (production standard)
    SSE = "sse"  # Server-Sent Events (legacy/deprecated)


class MCPServerType(str, Enum):
    """Supported MCP server types (purpose/function, not transport)."""

    MSSQL = "mssql"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    BRAVE_SEARCH = "brave_search"
    CUSTOM = "custom"


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server supporting all MCP transport types."""

    name: str = Field(..., description="Unique server name/identifier")
    server_type: MCPServerType = Field(default=MCPServerType.CUSTOM, description="Type of MCP server")
    transport: TransportType = Field(default=TransportType.STDIO, description="MCP transport mechanism")
    
    # Stdio transport fields (required for stdio)
    command: str | None = Field(default=None, description="Command to execute for stdio transport")
    args: list[str] = Field(default_factory=list, description="Command line arguments for stdio")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables for stdio")
    
    # HTTP/SSE transport fields (required for streamable_http/sse)
    url: str | None = Field(default=None, description="HTTP endpoint URL for streamable_http/sse transport")
    headers: dict[str, str] = Field(default_factory=dict, description="HTTP headers for authentication")
    
    # Common fields
    enabled: bool = Field(default=True, description="Whether server is enabled")
    readonly: bool = Field(default=False, description="Read-only mode for data servers")
    timeout: int = Field(default=30, description="Server startup timeout in seconds")
    description: str = Field(default="", description="Human-readable description")

    @model_validator(mode="after")
    def validate_transport_fields(self) -> "MCPServerConfig":
        """Validate that required fields are present for each transport type."""
        if self.transport == TransportType.STDIO:
            if not self.command:
                raise ValueError(f"stdio transport requires 'command' field (server: {self.name})")
        elif self.transport in (TransportType.STREAMABLE_HTTP, TransportType.SSE):
            if not self.url:
                raise ValueError(f"{self.transport.value} transport requires 'url' field (server: {self.name})")
        return self

    @field_validator("command")
    @classmethod
    def validate_command(cls, v: str | None) -> str | None:
        """Validate command field."""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("Command cannot be empty string")
        return v.strip()
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """Validate URL field."""
        if v is None:
            return None
        if not v.strip():
            raise ValueError("URL cannot be empty string")
        # Basic URL validation
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is valid identifier."""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        # Replace spaces with underscores, lowercase
        return v.strip().lower().replace(" ", "_")

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        """Ensure timeout is reasonable."""
        if v < 1 or v > 300:
            raise ValueError("Timeout must be between 1 and 300 seconds")
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "server_type": self.server_type.value,
            "transport": self.transport.value,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "url": self.url,
            "headers": self.headers,
            "enabled": self.enabled,
            "readonly": self.readonly,
            "timeout": self.timeout,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPServerConfig":
        """Create from dictionary. Handles legacy configs and auto-detects transport."""
        # Auto-detect transport type if not specified (backward compatibility)
        if "transport" not in data:
            if data.get("command"):
                data["transport"] = TransportType.STDIO.value
            elif data.get("url"):
                data["transport"] = TransportType.STREAMABLE_HTTP.value
            else:
                # Default to stdio for legacy configs
                data["transport"] = TransportType.STDIO.value
        
        # Default server_type based on name if not provided
        if "server_type" not in data:
            name = data.get("name", "").lower()
            if "mssql" in name or "sql" in name:
                data["server_type"] = MCPServerType.MSSQL.value
            elif "mongo" in name:
                data["server_type"] = MCPServerType.MONGODB.value
            elif "postgres" in name or "pg" in name:
                data["server_type"] = MCPServerType.POSTGRESQL.value
            elif "brave" in name:
                data["server_type"] = MCPServerType.BRAVE_SEARCH.value
            else:
                data["server_type"] = MCPServerType.CUSTOM.value
        
        # Extract only known fields for Pydantic model
        known_fields = {
            'name', 'server_type', 'transport', 'command', 'args', 'env',
            'url', 'headers', 'enabled', 'readonly', 'timeout', 'description'
        }
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        
        return cls(**filtered_data)


class MCPConfigFile(BaseModel):
    """Root configuration file structure for multiple MCP servers."""

    mcpServers: dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="Map of server names to configurations"
    )

    def add_server(self, config: MCPServerConfig) -> None:
        """Add a new server configuration."""
        self.mcpServers[config.name] = config

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration. Returns True if removed."""
        if name in self.mcpServers:
            del self.mcpServers[name]
            return True
        return False

    def get_server(self, name: str) -> MCPServerConfig | None:
        """Get server configuration by name."""
        return self.mcpServers.get(name)

    def get_enabled_servers(self) -> list[MCPServerConfig]:
        """Get list of enabled server configurations."""
        return [cfg for cfg in self.mcpServers.values() if cfg.enabled]

    def list_server_names(self) -> list[str]:
        """Get list of all server names."""
        return list(self.mcpServers.keys())

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON persistence."""
        return {"mcpServers": {name: cfg.to_dict() for name, cfg in self.mcpServers.items()}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPConfigFile":
        """Load from dictionary."""
        servers = {}
        if "mcpServers" in data:
            for name, cfg_data in data["mcpServers"].items():
                # Ensure name matches key
                cfg_data["name"] = name
                servers[name] = MCPServerConfig.from_dict(cfg_data)
        return cls(mcpServers=servers)


# Predefined templates for common server types
MSSQL_SERVER_TEMPLATE = MCPServerConfig(
    name="mssql",
    server_type=MCPServerType.MSSQL,
    transport=TransportType.STDIO,
    command="node",
    args=["${MCP_MSSQL_PATH}"],
    env={
        "SERVER_NAME": "${SQL_SERVER_HOST}",
        "DATABASE_NAME": "${SQL_DATABASE_NAME}",
        "TRUST_SERVER_CERTIFICATE": "${SQL_TRUST_SERVER_CERTIFICATE}",
        "READONLY": "${MCP_MSSQL_READONLY}",
    },
    description="SQL Server MCP Server for database access",
)

BRAVE_SEARCH_TEMPLATE = MCPServerConfig(
    name="brave_search",
    server_type=MCPServerType.BRAVE_SEARCH,
    transport=TransportType.STDIO,
    command="npx",
    args=["-y", "@modelcontextprotocol/server-brave-search"],
    env={"BRAVE_API_KEY": "${BRAVE_API_KEY}"},
    description="Brave Search MCP Server for web search",
)
