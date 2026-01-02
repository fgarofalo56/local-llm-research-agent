"""
Database Connections Routes
Phase 4.6: Multi-Database Support

API endpoints for managing database connection profiles.
Supports SQL Server, PostgreSQL, and MySQL databases.
"""

import base64
import json
import time
from datetime import datetime
from enum import Enum

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import DatabaseConnection

router = APIRouter()
logger = structlog.get_logger()


class DatabaseType(str, Enum):
    """Supported database types."""

    MSSQL = "mssql"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


# Default ports for each database type
DEFAULT_PORTS = {
    DatabaseType.MSSQL: 1433,
    DatabaseType.POSTGRESQL: 5432,
    DatabaseType.MYSQL: 3306,
}


class DatabaseConnectionCreate(BaseModel):
    """Request model for creating a database connection."""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str | None = None
    db_type: DatabaseType
    host: str = Field(..., min_length=1, max_length=255)
    port: int | None = None  # Will use default if not provided
    database: str = Field(..., min_length=1, max_length=255)
    username: str | None = None
    password: str | None = None
    ssl_enabled: bool = True
    trust_certificate: bool = False
    additional_options: dict | None = None
    is_default: bool = False


class DatabaseConnectionUpdate(BaseModel):
    """Request model for updating a database connection."""

    display_name: str | None = None
    host: str | None = None
    port: int | None = None
    database: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_enabled: bool | None = None
    trust_certificate: bool | None = None
    additional_options: dict | None = None
    is_default: bool | None = None
    is_active: bool | None = None


class DatabaseConnectionResponse(BaseModel):
    """Response model for a database connection."""

    id: int
    name: str
    display_name: str | None
    db_type: str
    host: str
    port: int
    database: str
    username: str | None
    has_password: bool
    ssl_enabled: bool
    trust_certificate: bool
    additional_options: dict | None
    is_default: bool
    is_active: bool
    last_tested_at: datetime | None
    last_test_success: bool | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatabaseConnectionTestRequest(BaseModel):
    """Request model for testing a connection."""

    db_type: DatabaseType
    host: str
    port: int | None = None
    database: str
    username: str | None = None
    password: str | None = None
    ssl_enabled: bool = True
    trust_certificate: bool = False


class DatabaseConnectionTestResult(BaseModel):
    """Result of a database connection test."""

    success: bool
    message: str
    latency_ms: float | None = None
    error: str | None = None
    server_version: str | None = None


def _encode_password(password: str) -> str:
    """Encode password for storage (simple base64 - use proper encryption in production)."""
    return base64.b64encode(password.encode()).decode()


def _decode_password(encoded: str) -> str:
    """Decode stored password."""
    return base64.b64decode(encoded.encode()).decode()


def _connection_to_response(conn: DatabaseConnection) -> DatabaseConnectionResponse:
    """Convert database model to response model."""
    additional_options = None
    if conn.additional_options:
        try:
            additional_options = json.loads(conn.additional_options)
        except json.JSONDecodeError:
            pass

    return DatabaseConnectionResponse(
        id=conn.id,
        name=conn.name,
        display_name=conn.display_name,
        db_type=conn.db_type,
        host=conn.host,
        port=conn.port,
        database=conn.database,
        username=conn.username,
        has_password=bool(conn.password_encrypted),
        ssl_enabled=conn.ssl_enabled or False,
        trust_certificate=conn.trust_certificate or False,
        additional_options=additional_options,
        is_default=conn.is_default or False,
        is_active=conn.is_active if conn.is_active is not None else True,
        last_tested_at=conn.last_tested_at,
        last_test_success=conn.last_test_success,
        created_at=conn.created_at,
        updated_at=conn.updated_at,
    )


@router.get("", response_model=list[DatabaseConnectionResponse])
async def list_database_connections(
    db: AsyncSession = Depends(get_db),
    db_type: DatabaseType | None = None,
    active_only: bool = False,
):
    """
    List all database connections.

    Optionally filter by database type or active status.
    """
    query = select(DatabaseConnection).order_by(
        DatabaseConnection.is_default.desc(),
        DatabaseConnection.name,
    )

    if db_type:
        query = query.where(DatabaseConnection.db_type == db_type.value)

    if active_only:
        query = query.where(DatabaseConnection.is_active == True)

    result = await db.execute(query)
    connections = result.scalars().all()

    return [_connection_to_response(conn) for conn in connections]


@router.post("", response_model=DatabaseConnectionResponse, status_code=201)
async def create_database_connection(
    data: DatabaseConnectionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new database connection profile."""
    # Check if name already exists
    existing = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Connection name already exists")

    # Use default port if not provided
    port = data.port or DEFAULT_PORTS.get(data.db_type, 1433)

    # If setting as default, clear other defaults of same type
    if data.is_default:
        await db.execute(
            select(DatabaseConnection)
            .where(DatabaseConnection.db_type == data.db_type.value)
            .where(DatabaseConnection.is_default == True)
        )
        result = await db.execute(
            select(DatabaseConnection)
            .where(DatabaseConnection.db_type == data.db_type.value)
            .where(DatabaseConnection.is_default == True)
        )
        for conn in result.scalars().all():
            conn.is_default = False

    # Create connection
    connection = DatabaseConnection(
        name=data.name,
        display_name=data.display_name or data.name,
        db_type=data.db_type.value,
        host=data.host,
        port=port,
        database=data.database,
        username=data.username,
        password_encrypted=_encode_password(data.password) if data.password else None,
        ssl_enabled=data.ssl_enabled,
        trust_certificate=data.trust_certificate,
        additional_options=json.dumps(data.additional_options) if data.additional_options else None,
        is_default=data.is_default,
        is_active=True,
    )

    db.add(connection)
    await db.commit()
    await db.refresh(connection)

    logger.info(
        "database_connection_created",
        id=connection.id,
        name=connection.name,
        db_type=connection.db_type,
    )

    return _connection_to_response(connection)


@router.get("/{connection_id}", response_model=DatabaseConnectionResponse)
async def get_database_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific database connection by ID."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return _connection_to_response(connection)


@router.put("/{connection_id}", response_model=DatabaseConnectionResponse)
async def update_database_connection(
    connection_id: int,
    data: DatabaseConnectionUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing database connection."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Update fields
    if data.display_name is not None:
        connection.display_name = data.display_name
    if data.host is not None:
        connection.host = data.host
    if data.port is not None:
        connection.port = data.port
    if data.database is not None:
        connection.database = data.database
    if data.username is not None:
        connection.username = data.username
    if data.password is not None:
        connection.password_encrypted = _encode_password(data.password)
    if data.ssl_enabled is not None:
        connection.ssl_enabled = data.ssl_enabled
    if data.trust_certificate is not None:
        connection.trust_certificate = data.trust_certificate
    if data.additional_options is not None:
        connection.additional_options = json.dumps(data.additional_options)
    if data.is_active is not None:
        connection.is_active = data.is_active

    # Handle default flag
    if data.is_default is not None:
        if data.is_default:
            # Clear other defaults of same type
            result = await db.execute(
                select(DatabaseConnection)
                .where(DatabaseConnection.db_type == connection.db_type)
                .where(DatabaseConnection.is_default == True)
                .where(DatabaseConnection.id != connection_id)
            )
            for conn in result.scalars().all():
                conn.is_default = False
        connection.is_default = data.is_default

    connection.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(connection)

    logger.info(
        "database_connection_updated",
        id=connection.id,
        name=connection.name,
    )

    return _connection_to_response(connection)


@router.delete("/{connection_id}")
async def delete_database_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a database connection."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    name = connection.name
    await db.delete(connection)
    await db.commit()

    logger.info("database_connection_deleted", id=connection_id, name=name)

    return {"status": "deleted", "id": connection_id}


@router.post("/{connection_id}/test", response_model=DatabaseConnectionTestResult)
async def test_existing_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Test an existing database connection."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Decode password if present
    password = None
    if connection.password_encrypted:
        password = _decode_password(connection.password_encrypted)

    # Test the connection
    test_result = await _test_database_connection(
        db_type=DatabaseType(connection.db_type),
        host=connection.host,
        port=connection.port,
        database=connection.database,
        username=connection.username,
        password=password,
        ssl_enabled=connection.ssl_enabled or False,
        trust_certificate=connection.trust_certificate or False,
    )

    # Update last test status
    connection.last_tested_at = datetime.utcnow()
    connection.last_test_success = test_result.success
    await db.commit()

    return test_result


@router.post("/test", response_model=DatabaseConnectionTestResult)
async def test_connection(data: DatabaseConnectionTestRequest):
    """Test a database connection without saving it."""
    port = data.port or DEFAULT_PORTS.get(data.db_type, 1433)

    return await _test_database_connection(
        db_type=data.db_type,
        host=data.host,
        port=port,
        database=data.database,
        username=data.username,
        password=data.password,
        ssl_enabled=data.ssl_enabled,
        trust_certificate=data.trust_certificate,
    )


@router.post("/{connection_id}/set-default")
async def set_default_connection(
    connection_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Set a connection as the default for its database type."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    # Clear other defaults of same type
    result = await db.execute(
        select(DatabaseConnection)
        .where(DatabaseConnection.db_type == connection.db_type)
        .where(DatabaseConnection.is_default == True)
    )
    for conn in result.scalars().all():
        conn.is_default = False

    # Set this one as default
    connection.is_default = True
    connection.updated_at = datetime.utcnow()

    await db.commit()

    logger.info(
        "database_connection_set_default",
        id=connection_id,
        db_type=connection.db_type,
    )

    return {"status": "ok", "default_connection_id": connection_id}


async def _test_database_connection(
    db_type: DatabaseType,
    host: str,
    port: int,
    database: str,
    username: str | None,
    password: str | None,
    ssl_enabled: bool,
    trust_certificate: bool,
) -> DatabaseConnectionTestResult:
    """Test a database connection."""
    start_time = time.time()

    try:
        if db_type == DatabaseType.MSSQL:
            return await _test_mssql_connection(
                host, port, database, username, password, ssl_enabled, trust_certificate
            )
        elif db_type == DatabaseType.POSTGRESQL:
            return await _test_postgres_connection(
                host, port, database, username, password, ssl_enabled
            )
        elif db_type == DatabaseType.MYSQL:
            return await _test_mysql_connection(
                host, port, database, username, password, ssl_enabled
            )
        else:
            return DatabaseConnectionTestResult(
                success=False,
                message="Unsupported database type",
                error=f"Database type '{db_type}' is not supported",
            )
    except Exception as e:
        logger.error("database_connection_test_error", error=str(e), db_type=db_type.value)
        return DatabaseConnectionTestResult(
            success=False,
            message="Connection test failed",
            error=str(e)[:300],
        )


async def _test_mssql_connection(
    host: str,
    port: int,
    database: str,
    username: str | None,
    password: str | None,
    ssl_enabled: bool,
    trust_certificate: bool,
) -> DatabaseConnectionTestResult:
    """Test SQL Server connection."""
    import aioodbc

    trust_cert = "yes" if trust_certificate else "no"
    encrypt = "yes" if ssl_enabled else "no"

    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={host},{port};"
        f"Database={database};"
        f"TrustServerCertificate={trust_cert};"
        f"Encrypt={encrypt};"
    )

    if username and password:
        connection_string += f"UID={username};PWD={password};"

    start_time = time.time()

    try:
        conn = await aioodbc.connect(dsn=connection_string, timeout=10)
        try:
            cursor = await conn.cursor()
            await cursor.execute("SELECT @@VERSION")
            result = await cursor.fetchone()
            await cursor.close()

            latency = (time.time() - start_time) * 1000
            version = result[0].split("\n")[0] if result else None

            return DatabaseConnectionTestResult(
                success=True,
                message=f"Connected to SQL Server at {host}:{port}",
                latency_ms=round(latency, 2),
                server_version=version,
            )
        finally:
            await conn.close()

    except Exception as e:
        error_msg = str(e)
        if "Login failed" in error_msg:
            message = "Authentication failed"
        elif "Cannot open database" in error_msg:
            message = f"Database '{database}' not found"
        elif "TCP Provider" in error_msg:
            message = f"Cannot connect to {host}:{port}"
        else:
            message = "Connection failed"

        return DatabaseConnectionTestResult(
            success=False,
            message=message,
            error=error_msg[:300],
        )


async def _test_postgres_connection(
    host: str,
    port: int,
    database: str,
    username: str | None,
    password: str | None,
    ssl_enabled: bool,
) -> DatabaseConnectionTestResult:
    """Test PostgreSQL connection."""
    try:
        import asyncpg
    except ImportError:
        return DatabaseConnectionTestResult(
            success=False,
            message="PostgreSQL driver not installed",
            error="Install asyncpg: pip install asyncpg",
        )

    start_time = time.time()

    try:
        ssl_mode = "require" if ssl_enabled else "disable"
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            ssl=ssl_mode,
            timeout=10,
        )

        try:
            version = await conn.fetchval("SELECT version()")
            latency = (time.time() - start_time) * 1000

            return DatabaseConnectionTestResult(
                success=True,
                message=f"Connected to PostgreSQL at {host}:{port}",
                latency_ms=round(latency, 2),
                server_version=version.split(",")[0] if version else None,
            )
        finally:
            await conn.close()

    except Exception as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg.lower():
            message = "Authentication failed"
        elif "does not exist" in error_msg:
            message = f"Database '{database}' not found"
        elif "could not connect" in error_msg.lower():
            message = f"Cannot connect to {host}:{port}"
        else:
            message = "Connection failed"

        return DatabaseConnectionTestResult(
            success=False,
            message=message,
            error=error_msg[:300],
        )


async def _test_mysql_connection(
    host: str,
    port: int,
    database: str,
    username: str | None,
    password: str | None,
    ssl_enabled: bool,
) -> DatabaseConnectionTestResult:
    """Test MySQL connection."""
    try:
        import aiomysql
    except ImportError:
        return DatabaseConnectionTestResult(
            success=False,
            message="MySQL driver not installed",
            error="Install aiomysql: pip install aiomysql",
        )

    start_time = time.time()

    try:
        conn = await aiomysql.connect(
            host=host,
            port=port,
            db=database,
            user=username or "",
            password=password or "",
            connect_timeout=10,
        )

        try:
            async with conn.cursor() as cursor:
                await cursor.execute("SELECT VERSION()")
                result = await cursor.fetchone()

            latency = (time.time() - start_time) * 1000

            return DatabaseConnectionTestResult(
                success=True,
                message=f"Connected to MySQL at {host}:{port}",
                latency_ms=round(latency, 2),
                server_version=result[0] if result else None,
            )
        finally:
            conn.close()

    except Exception as e:
        error_msg = str(e)
        if "Access denied" in error_msg:
            message = "Authentication failed"
        elif "Unknown database" in error_msg:
            message = f"Database '{database}' not found"
        elif "Can't connect" in error_msg:
            message = f"Cannot connect to {host}:{port}"
        else:
            message = "Connection failed"

        return DatabaseConnectionTestResult(
            success=False,
            message=message,
            error=error_msg[:300],
        )
