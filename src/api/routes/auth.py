"""
Authentication Routes
Phase 4.5: Security & Authentication

Endpoints for user registration, login, logout, and token management.
"""

import hashlib
from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.api.models.database import RefreshToken, User
from src.auth import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    TokenError,
    TokenExpiredError,
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)

router = APIRouter()
logger = structlog.get_logger()

# Security scheme for bearer tokens
security = HTTPBearer(auto_error=False)


# ============================================================================
# Request/Response Models
# ============================================================================


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    display_name: str | None = None


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


class UserResponse(BaseModel):
    """User profile response."""

    id: int
    email: str
    username: str
    display_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


# ============================================================================
# Helper Functions
# ============================================================================


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def store_refresh_token(
    db: AsyncSession,
    user_id: int,
    token: str,
    expires_at: datetime,
) -> None:
    """Store a refresh token in the database."""
    token_record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.commit()


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    """Revoke a refresh token."""
    token_hash = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    token_record = result.scalar_one_or_none()
    if token_record:
        token_record.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        return True
    return False


async def is_refresh_token_valid(db: AsyncSession, token: str) -> bool:
    """Check if a refresh token is valid (not revoked)."""
    token_hash = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    return result.scalar_one_or_none() is not None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from the JWT token.

    This is a dependency that can be used to protect endpoints.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_access_token(credentials.credentials)
        user_id = int(payload["sub"])
        user = await get_user_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
            )

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get the current authenticated user if token is provided.

    Returns None if no token is provided (for optional auth).
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user account.

    Returns access and refresh tokens on successful registration.
    """
    # Validate password strength
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Check if email already exists
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if username already exists
    existing_username = await get_user_by_username(db, request.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    # Create user
    user = User(
        email=request.email,
        username=request.username,
        password_hash=hash_password(request.password),
        display_name=request.display_name or request.username,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("user_registered", user_id=user.id, email=user.email)

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    # Store refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    await store_refresh_token(db, user.id, refresh_token, expires_at)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user and return tokens.

    Returns access and refresh tokens on successful login.
    """
    # Find user by email
    user = await get_user_by_email(db, request.email)

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("user_logged_in", user_id=user.id, email=user.email)

    # Generate tokens
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    # Store refresh token
    expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    await store_refresh_token(db, user.id, refresh_token, expires_at)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using a refresh token.

    Returns new access and refresh tokens.
    """
    try:
        # Verify the refresh token
        payload = verify_refresh_token(request.refresh_token)

        # Check if token is still valid in database
        if not await is_refresh_token_valid(db, request.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user_id = int(payload["sub"])
        user = await get_user_by_id(db, user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Revoke old refresh token
        await revoke_refresh_token(db, request.refresh_token)

        # Generate new tokens
        access_token = create_access_token(user.id, user.email)
        new_refresh_token = create_refresh_token(user.id, user.email)

        # Store new refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await store_refresh_token(db, user.id, new_refresh_token, expires_at)

        logger.debug("tokens_refreshed", user_id=user.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout user by revoking the refresh token.
    """
    await revoke_refresh_token(db, request.refresh_token)
    logger.info("user_logged_out", user_id=current_user.id)
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get the current authenticated user's profile.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    display_name: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current user's profile.
    """
    if display_name is not None:
        current_user.display_name = display_name
        await db.commit()
        await db.refresh(current_user)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        display_name=current_user.display_name,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change the current user's password.
    """
    # Verify current password
    if not verify_password(current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password strength
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Update password
    current_user.password_hash = hash_password(new_password)
    await db.commit()

    logger.info("password_changed", user_id=current_user.id)

    return MessageResponse(message="Password changed successfully")
