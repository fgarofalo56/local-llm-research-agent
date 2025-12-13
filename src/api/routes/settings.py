"""
Settings Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline
Phase 2.4: Enhanced provider and model configuration

Endpoints for application settings, themes, and LLM provider configuration.
"""

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


class ProviderModelsResponse(BaseModel):
    """Response model for provider models."""

    provider: str
    models: list[ModelInfo]
    error: str | None = None


class ConnectionTestResult(BaseModel):
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
    except Exception as e:
        foundry_info.error = str(e)[:100]
    providers.append(foundry_info)

    return providers


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
                    models.append(
                        ModelInfo(
                            name=model.get("name", ""),
                            size=_format_size(model.get("size", 0)),
                            modified_at=model.get("modified_at"),
                            family=model.get("details", {}).get("family"),
                            parameter_size=model.get("details", {}).get("parameter_size"),
                            quantization_level=model.get("details", {}).get("quantization_level"),
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
                    models.append(
                        ModelInfo(
                            name=model.get("id", ""),
                            family=model.get("owned_by"),
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


@router.post("/providers/test", response_model=ConnectionTestResult)
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
                return ConnectionTestResult(
                    success=True,
                    provider=request.provider,
                    model=request.model,
                    message=f"Connected to Ollama{f' with model {request.model}' if request.model else ''}",
                    latency_ms=round(latency, 2),
                    version=version,
                )
        except Exception as e:
            return ConnectionTestResult(
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
                return ConnectionTestResult(
                    success=True,
                    provider=request.provider,
                    model=request.model,
                    message="Connected to Foundry Local",
                    latency_ms=round(latency, 2),
                )
        except Exception as e:
            return ConnectionTestResult(
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
