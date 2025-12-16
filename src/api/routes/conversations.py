"""
Conversations Routes
Phase 2.1: Backend Infrastructure & RAG Pipeline

Endpoints for managing chat conversations and messages.
"""

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.api.models.database import Conversation, Message

router = APIRouter()
logger = structlog.get_logger()


class MessageCreate(BaseModel):
    """Request model for creating a message."""

    role: str
    content: str
    tool_calls: str | None = None
    tokens_used: int | None = None


class MessageResponse(BaseModel):
    """Response model for a message."""

    id: int
    conversation_id: int
    role: str
    content: str
    tool_calls: str | None
    tokens_used: int | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Request model for creating a conversation."""

    title: str | None = None


class ConversationResponse(BaseModel):
    """Response model for a conversation."""

    id: int
    title: str | None
    created_at: datetime
    updated_at: datetime
    is_archived: bool
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Response model for conversation with messages."""

    messages: list[MessageResponse] = []


class ConversationListResponse(BaseModel):
    """Response model for conversation list."""

    conversations: list[ConversationResponse]
    total: int


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """List all conversations."""
    # Build query
    query = select(Conversation)
    if not include_archived:
        query = query.where(Conversation.is_archived == False)  # noqa: E712

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results with message count
    query = (
        query.options(selectinload(Conversation.messages))
        .offset(skip)
        .limit(limit)
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(query)
    conversations = result.scalars().all()

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_archived=conv.is_archived,
                message_count=len(conv.messages),
            )
            for conv in conversations
        ],
        total=total,
    )


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    conversation = Conversation(
        title=data.title or "New Conversation",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        is_archived=conversation.is_archived,
        message_count=0,
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a conversation with all messages."""
    query = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    result = await db.execute(query)
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        is_archived=conversation.is_archived,
        message_count=len(conversation.messages),
        messages=[MessageResponse.model_validate(msg) for msg in conversation.messages],
    )


class MessagesListResponse(BaseModel):
    """Response model for messages list."""

    messages: list[MessageResponse]
    total: int


@router.get("/{conversation_id}/messages", response_model=MessagesListResponse)
async def list_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all messages for a conversation."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )

    # Get total count
    count_result = await db.execute(query)
    total = len(count_result.scalars().all())

    # Get paginated results
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    messages = result.scalars().all()

    return MessagesListResponse(
        messages=[MessageResponse.model_validate(msg) for msg in messages],
        total=total,
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(
    conversation_id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a message to a conversation."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message = Message(
        conversation_id=conversation_id,
        role=data.role,
        content=data.content,
        tool_calls=data.tool_calls,
        tokens_used=data.tokens_used,
    )
    db.add(message)

    # Update conversation timestamp
    conversation.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(message)

    return MessageResponse.model_validate(message)


@router.patch("/{conversation_id}")
async def update_conversation(
    conversation_id: int,
    title: str | None = None,
    is_archived: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update a conversation."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if title is not None:
        conversation.title = title
    if is_archived is not None:
        conversation.is_archived = is_archived

    conversation.updated_at = datetime.utcnow()
    await db.commit()

    return {"status": "updated", "conversation_id": conversation_id}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    conversation = await db.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()

    return {"status": "deleted", "conversation_id": conversation_id}
