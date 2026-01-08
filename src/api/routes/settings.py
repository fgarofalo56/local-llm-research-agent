"""
Settings Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline
Phase 2.4: Enhanced provider and model configuration

Endpoints for application settings, themes, and LLM provider configuration.
"""

import os
import time
from datetime import datetime

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import ThemeConfig
from src.providers.foundry import (
    FOUNDRY_NON_TOOL_MODELS,
    FOUNDRY_TOOL_CAPABLE_MODELS,
)
from src.providers.ollama import OLLAMA_TOOL_CAPABLE_MODELS
from src.utils.config import get_settings

router = APIRouter()
logger = structlog.get_logger()


class AppSettingsResponse(BaseModel):
    """Response model for application settings."""

    llm_provider: str
    ollama_model: str
    embedding_model: str
    sql_server_host: str
    sql_database_name: str
    chunk_size: int
    chunk_overlap: int
    rag_top_k: int
    max_upload_size_mb: int
    debug: bool


class ThemeCreate(BaseModel):
    """Request model for creating a theme."""

    name: str
    display_name: str
    config: str  # JSON theme configuration


class ThemeResponse(BaseModel):
    """Response model for a theme."""

    id: int
    name: str
    display_name: str
    is_preset: bool
    is_active: bool
    config: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThemeListResponse(BaseModel):
    """Response model for theme list."""

    themes: list[ThemeResponse]
    active_theme: str | None


# Application Settings Endpoints
@router.get("", response_model=AppSettingsResponse)
async def get_app_settings():
    """Get current application settings."""
    settings = get_settings()

    return AppSettingsResponse(
        llm_provider=settings.llm_provider,
        ollama_model=settings.ollama_model,
        embedding_model=settings.embedding_model,
        sql_server_host=settings.sql_server_host,
        sql_database_name=settings.sql_database_name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        rag_top_k=settings.rag_top_k,
        max_upload_size_mb=settings.max_upload_size_mb,
        debug=settings.debug,
    )


# Theme Endpoints
@router.get("/themes", response_model=ThemeListResponse)
async def list_themes(
    db: AsyncSession = Depends(get_db),
):
    """List all themes."""
    query = select(ThemeConfig).order_by(ThemeConfig.is_preset.desc(), ThemeConfig.name)
    result = await db.execute(query)
    themes = result.scalars().all()

    # Find active theme
    active_theme = None
    for theme in themes:
        if theme.is_active:
            active_theme = theme.name
            break

    return ThemeListResponse(
        themes=[ThemeResponse.model_validate(t) for t in themes],
        active_theme=active_theme,
    )


@router.post("/themes", response_model=ThemeResponse)
async def create_theme(
    data: ThemeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a custom theme."""
    # Check if name exists
    existing = await db.execute(select(ThemeConfig).where(ThemeConfig.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Theme name already exists")

    theme = ThemeConfig(
        name=data.name,
        display_name=data.display_name,
        config=data.config,
        is_preset=False,
        is_active=False,
    )
    db.add(theme)
    await db.commit()
    await db.refresh(theme)

    return ThemeResponse.model_validate(theme)


@router.put("/themes/{theme_name}", response_model=ThemeResponse)
async def update_theme(
    theme_name: str,
    data: ThemeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Update a custom theme."""
    result = await db.execute(select(ThemeConfig).where(ThemeConfig.name == theme_name))
    theme = result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    if theme.is_preset:
        raise HTTPException(status_code=403, detail="Cannot modify preset theme")

    theme.display_name = data.display_name
    theme.config = data.config
    theme.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(theme)

    return ThemeResponse.model_validate(theme)


@router.post("/themes/{theme_name}/activate")
async def activate_theme(
    theme_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Activate a theme."""
    result = await db.execute(select(ThemeConfig).where(ThemeConfig.name == theme_name))
    theme = result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    # Deactivate all themes
    all_themes = await db.execute(select(ThemeConfig))
    for t in all_themes.scalars().all():
        t.is_active = False

    # Activate selected theme
    theme.is_active = True
    await db.commit()

    return {"status": "activated", "theme": theme_name}


@router.delete("/themes/{theme_name}")
async def delete_theme(
    theme_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom theme."""
    result = await db.execute(select(ThemeConfig).where(ThemeConfig.name == theme_name))
    theme = result.scalar_one_or_none()

    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")

    if theme.is_preset:
        raise HTTPException(status_code=403, detail="Cannot delete preset theme")

    await db.delete(theme)
    await db.commit()

    return {"status": "deleted", "theme": theme_name}


# ================= Provider & Model Endpoints =================


class ProviderInfo(BaseModel):
    """Information about an LLM provider."""

    id: str
    name: str
    display_name: str
    icon: str
    available: bool
    error: str | None = None
    version: str | None = None


class ModelInfo(BaseModel):
    """Information about an available model."""

    name: str
    size: str | None = None
    modified_at: str | None = None
    family: str | None = None
    parameter_size: str | None = None
    quantization_level: str | None = None
    supports_tools: bool = True  # Whether model supports function/tool calling
    tool_warning: str | None = None  # Warning message if model doesn't support tools


class ProviderModelsResponse(BaseModel):
    """Response model for provider models."""

    provider: str
    models: list[ModelInfo]
    error: str | None = None


class ProviderConnectionTestResult(BaseModel):
    """Result of a provider connection test."""

    success: bool
    provider: str
    model: str | None = None
    message: str
    latency_ms: float | None = None
    version: str | None = None
    error: str | None = None


@router.get("/providers", response_model=list[ProviderInfo])
async def list_providers():
    """List all available LLM providers with their status."""
    settings = get_settings()
    providers = []

    # Check Ollama
    ollama_info = ProviderInfo(
        id="ollama",
        name="ollama",
        display_name="Ollama",
        icon="🦙",
        available=False,
    )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_host}/api/version",
                timeout=5.0,
            )
            if response.status_code == 200:
                data = response.json()
                ollama_info.available = True
                ollama_info.version = data.get("version", "unknown")
    except Exception as e:
        ollama_info.error = str(e)[:100]
    providers.append(ollama_info)

    # Check Foundry Local
    foundry_info = ProviderInfo(
        id="foundry_local",
        name="foundry_local",
        display_name="Foundry Local",
        icon="🔧",
        available=False,
    )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.foundry_endpoint}/v1/models",
                timeout=5.0,
            )
            if response.status_code == 200:
                foundry_info.available = True
                foundry_info.version = "local"
    except httpx.ConnectError:
        foundry_info.error = (
            f"Not running at {settings.foundry_endpoint}. Start with: foundry model run phi-4"
        )
    except Exception as e:
        foundry_info.error = str(e)[:100]
    providers.append(foundry_info)

    return providers


def _check_ollama_tool_support(model_name: str) -> tuple[bool, str | None]:
    """
    Check if an Ollama model supports tool calling.

    Returns:
        Tuple of (supports_tools, warning_message)
    """
    model_lower = model_name.lower()
    supports = any(model in model_lower for model in OLLAMA_TOOL_CAPABLE_MODELS)

    if supports:
        return True, None

    # Provide helpful warning for common models
    if "qwq" in model_lower:
        return False, (
            f"Model '{model_name}' is a reasoning model optimized for thinking, not tool calling. "
            "Use qwen2.5 or qwen3 for MCP tools."
        )
    if "deepseek" in model_lower:
        return False, (
            f"Model '{model_name}' may not reliably support tool calling. "
            "Use qwen2.5, llama3.1, or mistral for better tool support."
        )
    if "phi" in model_lower:
        return False, (
            f"Model '{model_name}' may not support tool calling in Ollama. "
            "Use qwen2.5, llama3.1, or mistral for MCP tools."
        )

    return False, (
        f"Model '{model_name}' may not support tool calling. "
        "For MCP tools, use qwen2.5, llama3.1/3.2/3.3, or mistral."
    )


def _check_foundry_tool_support(model_name: str) -> tuple[bool, str | None]:
    """
    Check if a Foundry Local model supports tool calling.

    Returns:
        Tuple of (supports_tools, warning_message)
    """
    model_lower = model_name.lower()

    # First check if it's explicitly a non-tool model
    for non_tool_model in FOUNDRY_NON_TOOL_MODELS:
        if non_tool_model.lower() in model_lower:
            # But make sure it's not actually a tool-capable variant
            is_tool_capable = any(
                tool_model.lower() in model_lower for tool_model in FOUNDRY_TOOL_CAPABLE_MODELS
            )
            if not is_tool_capable:
                # Provide specific warnings
                if "phi-4" in model_lower and "mini" not in model_lower:
                    return False, (
                        f"Model '{model_name}' does NOT support tool calling. "
                        "Use 'phi-4-mini' instead which supports function calling."
                    )
                if "phi-4-multimodal" in model_lower:
                    return False, (
                        f"Model '{model_name}' is for vision tasks, not function calling. "
                        "Use 'phi-4-mini' for MCP tools."
                    )
                return False, (
                    f"Model '{model_name}' does not support tool calling. "
                    "Use phi-4-mini, qwen2.5, or llama3.1 for MCP tools."
                )

    # Check if it matches a known tool-capable model
    supports = any(model.lower() in model_lower for model in FOUNDRY_TOOL_CAPABLE_MODELS)
    if supports:
        return True, None

    return False, (
        f"Model '{model_name}' may not support tool calling. "
        "For MCP tools, use phi-4-mini, qwen2.5, or llama3.1/3.2."
    )


@router.get("/providers/{provider_id}/models", response_model=ProviderModelsResponse)
async def list_provider_models(provider_id: str):
    """List available models for a specific provider."""
    settings = get_settings()
    models = []

    if provider_id == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ollama_host}/api/tags",
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                for model in data.get("models", []):
                    model_name = model.get("name", "")
                    supports_tools, tool_warning = _check_ollama_tool_support(model_name)
                    models.append(
                        ModelInfo(
                            name=model_name,
                            size=_format_size(model.get("size", 0)),
                            modified_at=model.get("modified_at"),
                            family=model.get("details", {}).get("family"),
                            parameter_size=model.get("details", {}).get("parameter_size"),
                            quantization_level=model.get("details", {}).get("quantization_level"),
                            supports_tools=supports_tools,
                            tool_warning=tool_warning,
                        )
                    )
        except Exception as e:
            return ProviderModelsResponse(
                provider=provider_id,
                models=[],
                error=str(e)[:200],
            )

    elif provider_id == "foundry_local":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.foundry_endpoint}/v1/models",
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()

                for model in data.get("data", []):
                    model_name = model.get("id", "")
                    supports_tools, tool_warning = _check_foundry_tool_support(model_name)
                    models.append(
                        ModelInfo(
                            name=model_name,
                            family=model.get("owned_by"),
                            supports_tools=supports_tools,
                            tool_warning=tool_warning,
                        )
                    )
        except Exception as e:
            return ProviderModelsResponse(
                provider=provider_id,
                models=[],
                error=str(e)[:200],
            )
    else:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider_id}")

    return ProviderModelsResponse(provider=provider_id, models=models)


class ConnectionTestRequest(BaseModel):
    """Request model for connection test."""

    provider: str
    model: str | None = None


class FoundryStartRequest(BaseModel):
    """Request model for starting Foundry Local."""

    model: str | None = None


class FoundryStartResponse(BaseModel):
    """Response model for Foundry start operation."""

    success: bool
    message: str
    endpoint: str | None = None
    model: str | None = None
    error: str | None = None
    is_docker: bool = False  # True when showing instructions instead of starting


class OllamaStartResponse(BaseModel):
    """Response model for Ollama start operation."""

    success: bool
    message: str
    endpoint: str | None = None
    error: str | None = None
    is_docker: bool = False  # True when showing instructions instead of starting


class FoundryModelListResponse(BaseModel):
    """Response model for Foundry model list from CLI."""

    success: bool
    models: list[dict]
    error: str | None = None


def _is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    # Check for .dockerenv file
    if os.path.exists("/.dockerenv"):
        return True
    # Check cgroup
    try:
        with open("/proc/1/cgroup") as f:
            return "docker" in f.read()
    except Exception as e:
        # Failed to read cgroup file - likely not in Docker or permission issue
        logger.debug("cgroup_check_failed", error=str(e))
    return False


async def _call_host_agent(
    endpoint: str, method: str = "POST", json_data: dict | None = None
) -> dict | None:
    """
    Call the host agent sidecar to start services on the host machine.

    Args:
        endpoint: The endpoint path (e.g., "/start/ollama")
        method: HTTP method (GET or POST)
        json_data: Optional JSON body for POST requests

    Returns:
        Response JSON dict or None if agent not available
    """
    settings = get_settings()
    host_agent_url = settings.host_agent_url

    try:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(
                    f"{host_agent_url}{endpoint}",
                    timeout=15.0,
                )
            else:
                response = await client.post(
                    f"{host_agent_url}{endpoint}",
                    json=json_data or {},
                    timeout=15.0,
                )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    "host_agent_error",
                    endpoint=endpoint,
                    status=response.status_code,
                    body=response.text[:200],
                )
                return None
    except httpx.ConnectError:
        logger.debug("host_agent_not_available", url=host_agent_url)
        return None
    except Exception as e:
        logger.warning("host_agent_call_failed", error=str(e))
        return None


@router.post("/providers/ollama/start", response_model=OllamaStartResponse)
async def start_ollama():
    """
    Start Ollama service.

    When running in Docker:
    - First tries to call the host agent sidecar
    - If host agent not available, returns instructions

    When running locally:
    - On Windows: Tries to start Ollama app or provides instructions
    - On Linux/Mac: Starts Ollama directly via CLI
    """
    import asyncio
    import platform
    import shutil
    import subprocess
    from pathlib import Path

    settings = get_settings()
    is_windows = platform.system() == "Windows"

    # First, check if Ollama is already running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.ollama_host}/api/version",
                timeout=5.0,
            )
            if response.status_code == 200:
                version = response.json().get("version", "unknown")
                return OllamaStartResponse(
                    success=True,
                    message=f"Ollama is already running (version {version})",
                    endpoint=settings.ollama_host,
                )
    except Exception as e:
        logger.debug("ollama_not_running", error=str(e))

    # If running in Docker, try host agent first
    if _is_running_in_docker():
        # Try to call host agent
        result = await _call_host_agent("/start/ollama")
        if result:
            if result.get("success"):
                return OllamaStartResponse(
                    success=True,
                    message=result.get("message", "Ollama started via host agent"),
                    endpoint=result.get("endpoint"),
                )
            else:
                return OllamaStartResponse(
                    success=False,
                    message=result.get("message", "Failed to start Ollama"),
                    error=result.get("error"),
                    is_docker=True,
                )

        # Host agent not available - provide instructions
        return OllamaStartResponse(
            success=False,
            message="Host agent not available",
            error=(
                "The API is running in Docker. To start Ollama:\n\n"
                "Option 1: Start the host agent sidecar:\n"
                "  python scripts/host_agent.py\n\n"
                "Option 2: Start Ollama manually on your host:\n"
                "  ollama serve"
            ),
            is_docker=True,
        )

    # Running locally - find Ollama executable
    ollama_path = shutil.which("ollama")

    # On Windows, check common install locations if not in PATH
    if not ollama_path and is_windows:
        common_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe",
            Path(os.environ.get("PROGRAMFILES", "")) / "Ollama" / "ollama.exe",
            Path(os.environ.get("USERPROFILE", ""))
            / "AppData"
            / "Local"
            / "Programs"
            / "Ollama"
            / "ollama.exe",
        ]
        for path in common_paths:
            if path.exists():
                ollama_path = str(path)
                logger.info("ollama_found_at", path=ollama_path)
                break

    if not ollama_path:
        install_url = "https://ollama.ai"
        if is_windows:
            return OllamaStartResponse(
                success=False,
                message="Ollama not found",
                error=(
                    f"Ollama is not installed or not in PATH.\n\n"
                    f"Install from: {install_url}\n\n"
                    f"After installing, start Ollama from the Start Menu."
                ),
            )
        return OllamaStartResponse(
            success=False,
            message="Ollama CLI not found",
            error=f"Ollama is not installed. Install from: {install_url}",
        )

    try:
        # Windows-specific flags for detached process
        # These constants only exist on Windows, so use getattr with defaults
        creation_flags = 0
        if is_windows:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) | getattr(
                subprocess, "DETACHED_PROCESS", 0x00000008
            )

        if is_windows:
            # On Windows, try to start the Ollama app
            # The app handles running the server automatically
            ollama_app_path = Path(ollama_path).parent / "Ollama.exe"
            if ollama_app_path.exists():
                # Start the Ollama GUI app (not ollama.exe CLI)
                process = await asyncio.create_subprocess_exec(
                    str(ollama_app_path),
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    creationflags=creation_flags,
                )
                logger.info("ollama_app_started", pid=process.pid)
            else:
                # Fall back to starting ollama serve
                process = await asyncio.create_subprocess_exec(
                    ollama_path,
                    "serve",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                    creationflags=creation_flags,
                )
        else:
            # On Linux/Mac, start ollama serve as background process
            process = await asyncio.create_subprocess_exec(
                ollama_path,
                "serve",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

        # Wait briefly for startup
        await asyncio.sleep(3)

        # Check if Ollama is now responding
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.ollama_host}/api/version",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    version = response.json().get("version", "unknown")
                    return OllamaStartResponse(
                        success=True,
                        message=f"Ollama started successfully (version {version})",
                        endpoint=settings.ollama_host,
                    )
        except Exception:
            pass

        # Service not responding yet
        if is_windows:
            return OllamaStartResponse(
                success=False,
                message="Ollama may be starting...",
                error=(
                    "Service not responding yet.\n\n"
                    "Try starting Ollama from the Start Menu, or wait a moment and try again."
                ),
            )
        return OllamaStartResponse(
            success=False,
            message="Ollama may be starting...",
            error="Service not responding yet. Please wait and try again.",
        )

    except Exception as e:
        logger.error("ollama_start_error", error=str(e))
        if is_windows:
            return OllamaStartResponse(
                success=False,
                message="Failed to start Ollama",
                error=(
                    f"Error: {str(e)[:150]}\n\nTry starting Ollama manually from the Start Menu."
                ),
            )
        return OllamaStartResponse(
            success=False,
            message="Failed to start Ollama",
            error=str(e)[:200],
        )


@router.post("/providers/foundry/start", response_model=FoundryStartResponse)
async def start_foundry_local(request: FoundryStartRequest):
    """
    Start Foundry Local with a specified model.

    Note: When running in Docker, Foundry must be started on the host machine.
    This endpoint will check if Foundry is accessible and provide instructions.
    """
    import asyncio
    import re
    import shutil

    settings = get_settings()
    model = request.model or "phi-4"

    # SECURITY: Validate model name to prevent command injection
    # Only allow alphanumeric, hyphens, underscores, and dots
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", model):
        return FoundryStartResponse(
            success=False,
            message="Invalid model name",
            error="Model name must contain only letters, numbers, hyphens, underscores, and dots",
        )

    # First, check if Foundry is already running on the host
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.foundry_endpoint}/v1/models",
                timeout=5.0,
            )
            if response.status_code == 200:
                data = response.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                return FoundryStartResponse(
                    success=True,
                    message=f"Foundry Local is already running with {len(models)} model(s)",
                    endpoint=settings.foundry_endpoint,
                    model=models[0] if models else None,
                )
        except Exception as e:
            # Ignore connection errors - Foundry may not be running yet, will attempt to start it next
            logger.debug("foundry_health_check_failed", error=str(e))

    # If running in Docker, try host agent first
    if _is_running_in_docker():
        # Try to call host agent
        result = await _call_host_agent("/start/foundry", json_data={"model": model})
        if result:
            if result.get("success"):
                return FoundryStartResponse(
                    success=True,
                    message=result.get("message", "Foundry started via host agent"),
                    endpoint=result.get("endpoint"),
                    model=model,
                )
            else:
                return FoundryStartResponse(
                    success=False,
                    message=result.get("message", "Failed to start Foundry"),
                    error=result.get("error"),
                    model=model,
                    is_docker=True,
                )

        # Host agent not available - provide instructions
        return FoundryStartResponse(
            success=False,
            message="Host agent not available",
            error=(
                "The API is running in Docker. To start Foundry:\n\n"
                "Option 1: Start the host agent sidecar:\n"
                "  python scripts/host_agent.py\n\n"
                f"Option 2: Start Foundry manually on your host:\n"
                f"  foundry model run {model}"
            ),
            model=model,
            is_docker=True,
        )

    # Check if foundry CLI is available (non-Docker environment)
    foundry_path = shutil.which("foundry")
    if not foundry_path:
        return FoundryStartResponse(
            success=False,
            message="Foundry CLI not found",
            error="Foundry Local is not installed. Install it from: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started",
        )

    try:
        # Start foundry with the model
        process = await asyncio.create_subprocess_exec(
            "foundry",
            "model",
            "run",
            model,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Check if process failed immediately
        try:
            await asyncio.wait_for(process.wait(), timeout=0.5)
            # If we get here, process exited immediately (failed)
            stderr = await process.stderr.read() if process.stderr else b""
            return FoundryStartResponse(
                success=False,
                message="Foundry failed to start",
                error=stderr.decode()[:200] if stderr else "Process exited immediately",
            )
        except TimeoutError:
            # Process is still running, which is good
            pass

        # Wait a bit for startup (don't wait for completion as it runs in background)
        await asyncio.sleep(3)

        # Check if Foundry is now responding
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{settings.foundry_endpoint}/v1/models",
                    timeout=5.0,
                )
                if response.status_code == 200:
                    return FoundryStartResponse(
                        success=True,
                        message=f"Foundry Local started with model: {model}",
                        endpoint=settings.foundry_endpoint,
                        model=model,
                    )
            except Exception as e:
                # Ignore connection errors after startup - service may still be initializing, will prompt retry below
                logger.debug("foundry_startup_check_failed", error=str(e))

        return FoundryStartResponse(
            success=False,
            message="Foundry Local may be starting...",
            error="Service not responding yet. Please wait and try again.",
            model=model,
        )

    except Exception as e:
        logger.error("foundry_start_error", error=str(e))
        return FoundryStartResponse(
            success=False,
            message="Failed to start Foundry Local",
            error=str(e)[:200],
        )


@router.get("/providers/foundry/models-cli", response_model=FoundryModelListResponse)
async def list_foundry_models_cli():
    """
    List available Foundry models using the CLI command.

    This executes 'foundry model list' to get all available models.
    """
    import asyncio
    import shutil

    # Check if foundry CLI is available
    foundry_path = shutil.which("foundry")
    if not foundry_path:
        return FoundryModelListResponse(
            success=False,
            models=[],
            error="Foundry CLI not found. Install from: https://learn.microsoft.com/en-us/azure/ai-foundry/foundry-local/get-started",
        )

    try:
        # Run foundry model list
        process = await asyncio.create_subprocess_exec(
            "foundry",
            "model",
            "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

        if process.returncode != 0:
            return FoundryModelListResponse(
                success=False,
                models=[],
                error=stderr.decode() if stderr else "Command failed",
            )

        # Parse the output - typically table format
        output = stdout.decode()
        models = []

        # Parse table output (skip header lines)
        lines = output.strip().split("\n")
        for line in lines:
            # Skip empty lines and separator lines
            if not line.strip() or line.startswith("-") or line.startswith("="):
                continue
            # Skip header
            if "Model" in line and ("Size" in line or "Status" in line):
                continue

            # Parse columns (space-separated)
            parts = line.split()
            if len(parts) >= 1:
                model_info = {
                    "name": parts[0],
                    "size": parts[1] if len(parts) > 1 else None,
                    "status": parts[2] if len(parts) > 2 else None,
                }
                models.append(model_info)

        return FoundryModelListResponse(
            success=True,
            models=models,
        )

    except TimeoutError:
        return FoundryModelListResponse(
            success=False,
            models=[],
            error="Command timed out",
        )
    except Exception as e:
        logger.error("foundry_list_models_cli_error", error=str(e))
        return FoundryModelListResponse(
            success=False,
            models=[],
            error=str(e)[:200],
        )


@router.post("/providers/test", response_model=ProviderConnectionTestResult)
async def test_provider_connection(request: ConnectionTestRequest):
    """Test connection to a provider with optional model."""
    settings = get_settings()
    start_time = time.time()

    if request.provider == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                # First check version
                version_response = await client.get(
                    f"{settings.ollama_host}/api/version",
                    timeout=5.0,
                )
                version = None
                if version_response.status_code == 200:
                    version = version_response.json().get("version")

                # If model specified, try a simple generation
                if request.model:
                    response = await client.post(
                        f"{settings.ollama_host}/api/generate",
                        json={
                            "model": request.model,
                            "prompt": "Hi",
                            "stream": False,
                            "options": {"num_predict": 1},
                        },
                        timeout=30.0,
                    )
                    response.raise_for_status()

                latency = (time.time() - start_time) * 1000
                return ProviderConnectionTestResult(
                    success=True,
                    provider=request.provider,
                    model=request.model,
                    message=f"Connected to Ollama{f' with model {request.model}' if request.model else ''}",
                    latency_ms=round(latency, 2),
                    version=version,
                )
        except Exception as e:
            return ProviderConnectionTestResult(
                success=False,
                provider=request.provider,
                model=request.model,
                message="Connection failed",
                error=str(e)[:200],
            )

    elif request.provider == "foundry_local":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.foundry_endpoint}/v1/models",
                    timeout=5.0,
                )
                response.raise_for_status()

                latency = (time.time() - start_time) * 1000
                return ProviderConnectionTestResult(
                    success=True,
                    provider=request.provider,
                    model=request.model,
                    message="Connected to Foundry Local",
                    latency_ms=round(latency, 2),
                )
        except Exception as e:
            return ProviderConnectionTestResult(
                success=False,
                provider=request.provider,
                model=request.model,
                message="Connection failed",
                error=str(e)[:200],
            )

    else:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {request.provider}")


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


# ================= Database Settings Endpoints =================


class DatabaseSettings(BaseModel):
    """Request model for database settings."""

    host: str = "localhost"
    port: int = 1434
    database: str = "LLM_BackEnd"
    username: str = ""
    password: str = ""  # Will be masked in responses
    trust_certificate: bool = True


class DatabaseSettingsResponse(BaseModel):
    """Response model for database settings."""

    host: str
    port: int
    database: str
    username: str
    password_set: bool  # Don't return actual password
    trust_certificate: bool


class DatabaseConnectionTestResult(BaseModel):
    """Result of a database connection test."""

    success: bool
    message: str
    latency_ms: float | None = None
    error: str | None = None


# In-memory storage for runtime database settings
# Note: This is NOT persisted to .env for security reasons
_runtime_db_settings: DatabaseSettings | None = None


@router.get("/database", response_model=DatabaseSettingsResponse)
async def get_database_settings():
    """
    Get current backend database settings.

    Returns settings from runtime override if set, otherwise from environment variables.
    Password is never returned - only a boolean indicating if it's set.
    """
    settings = get_settings()

    # Use runtime settings if available, otherwise use env vars
    if _runtime_db_settings:
        db_config = _runtime_db_settings
    else:
        db_config = DatabaseSettings(
            host=settings.backend_db_host,
            port=settings.backend_db_port,
            database=settings.backend_db_name,
            username=settings.backend_db_username or settings.sql_username,
            password=settings.backend_db_password or settings.sql_password,
            trust_certificate=settings.backend_db_trust_cert,
        )

    return DatabaseSettingsResponse(
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        username=db_config.username,
        password_set=bool(db_config.password),
        trust_certificate=db_config.trust_certificate,
    )


@router.put("/database", response_model=DatabaseSettingsResponse)
async def update_database_settings(settings_update: DatabaseSettings):
    """
    Update backend database settings.

    Note: Settings are stored in memory only and NOT persisted to .env file.
    These settings will be lost when the API server restarts.

    For permanent changes, update the .env file manually.
    """
    global _runtime_db_settings

    logger.info(
        "updating_database_settings",
        host=settings_update.host,
        port=settings_update.port,
        database=settings_update.database,
        username=settings_update.username,
    )

    # Store in runtime settings
    _runtime_db_settings = settings_update

    return DatabaseSettingsResponse(
        host=settings_update.host,
        port=settings_update.port,
        database=settings_update.database,
        username=settings_update.username,
        password_set=bool(settings_update.password),
        trust_certificate=settings_update.trust_certificate,
    )


@router.post("/database/test", response_model=DatabaseConnectionTestResult)
async def test_database_connection(settings_test: DatabaseSettings | None = None):
    """
    Test connection to the backend database.

    If settings are provided in the request body, those will be tested.
    Otherwise, the current settings (runtime or env) will be tested.

    Returns success/failure with connection latency and meaningful error messages.
    """
    import aioodbc

    settings = get_settings()

    # Use provided settings, runtime settings, or env settings
    if settings_test:
        db_config = settings_test
    elif _runtime_db_settings:
        db_config = _runtime_db_settings
    else:
        db_config = DatabaseSettings(
            host=settings.backend_db_host,
            port=settings.backend_db_port,
            database=settings.backend_db_name,
            username=settings.backend_db_username or settings.sql_username,
            password=settings.backend_db_password or settings.sql_password,
            trust_certificate=settings.backend_db_trust_cert,
        )

    # Build connection string
    trust_cert = "yes" if db_config.trust_certificate else "no"
    connection_string = (
        f"Driver={{ODBC Driver 18 for SQL Server}};"
        f"Server={db_config.host},{db_config.port};"
        f"Database={db_config.database};"
        f"UID={db_config.username};"
        f"PWD={db_config.password};"
        f"TrustServerCertificate={trust_cert};"
        f"Encrypt=yes;"
    )

    logger.info(
        "testing_database_connection",
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        username=db_config.username,
    )

    try:
        start_time = time.time()

        # Attempt connection
        conn = await aioodbc.connect(dsn=connection_string, timeout=10)

        try:
            # Execute simple query
            cursor = await conn.cursor()
            await cursor.execute("SELECT 1 AS test")
            result = await cursor.fetchone()
            await cursor.close()

            latency = (time.time() - start_time) * 1000

            if result and result[0] == 1:
                logger.info(
                    "database_connection_success",
                    host=db_config.host,
                    port=db_config.port,
                    latency_ms=round(latency, 2),
                )
                return DatabaseConnectionTestResult(
                    success=True,
                    message=f"Successfully connected to {db_config.database} at {db_config.host}:{db_config.port}",
                    latency_ms=round(latency, 2),
                )
            else:
                return DatabaseConnectionTestResult(
                    success=False,
                    message="Query failed to return expected result",
                    error="SELECT 1 did not return 1",
                )
        finally:
            await conn.close()

    except Exception as e:
        # aioodbc can raise various exceptions including pyodbc.Error
        error_msg = str(e)
        logger.error(
            "database_connection_failed",
            host=db_config.host,
            port=db_config.port,
            error=error_msg,
        )

        # Provide helpful error messages
        if "Login failed" in error_msg or "Login timeout" in error_msg:
            message = "Authentication failed - check username and password"
        elif "Cannot open database" in error_msg:
            message = f"Database '{db_config.database}' not found or not accessible"
        elif "Named Pipes Provider" in error_msg or "TCP Provider" in error_msg:
            message = (
                f"Cannot connect to server {db_config.host}:{db_config.port} - check host and port"
            )
        elif "SSL Provider" in error_msg or "certificate" in error_msg.lower():
            message = "SSL/Certificate error - try enabling 'Trust Certificate'"
        else:
            message = "Connection failed"

        return DatabaseConnectionTestResult(
            success=False,
            message=message,
            error=error_msg[:300],  # Truncate long error messages
        )
