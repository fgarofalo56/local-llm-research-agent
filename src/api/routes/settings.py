"""
Settings Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for application settings and themes.
"""

from datetime import datetime

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
