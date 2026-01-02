"""
JWT Token Utilities
Phase 4.5: Security & Authentication

Handles JWT token creation, validation, and refresh.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import structlog

logger = structlog.get_logger()

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenError(Exception):
    """Base exception for token-related errors."""

    pass


class TokenExpiredError(TokenError):
    """Token has expired."""

    pass


class TokenInvalidError(TokenError):
    """Token is invalid."""

    pass


def create_access_token(
    user_id: int,
    email: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a new JWT access token.

    Args:
        user_id: User's database ID
        email: User's email address
        extra_claims: Additional claims to include in token

    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "type": "access",
        "iat": now,  # Issued at
        "exp": expires,  # Expiration
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug("access_token_created", user_id=user_id, expires=expires.isoformat())
    return token


def create_refresh_token(user_id: int, email: str) -> str:
    """
    Create a new JWT refresh token.

    Refresh tokens are longer-lived and used to obtain new access tokens.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        Encoded JWT refresh token string
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "refresh",
        "iat": now,
        "exp": expires,
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug("refresh_token_created", user_id=user_id, expires=expires.isoformat())
    return token


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        TokenExpiredError: If token has expired
        TokenInvalidError: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise TokenInvalidError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> dict[str, Any]:
    """
    Verify an access token is valid.

    Args:
        token: Access token to verify

    Returns:
        Decoded token payload

    Raises:
        TokenInvalidError: If not an access token
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise TokenInvalidError("Not an access token")
    return payload


def verify_refresh_token(token: str) -> dict[str, Any]:
    """
    Verify a refresh token is valid.

    Args:
        token: Refresh token to verify

    Returns:
        Decoded token payload

    Raises:
        TokenInvalidError: If not a refresh token
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise TokenInvalidError("Not a refresh token")
    return payload


def get_token_expiry(token: str) -> datetime | None:
    """
    Get the expiry time of a token without full validation.

    Args:
        token: JWT token

    Returns:
        Expiry datetime or None if not decodable
    """
    try:
        # Decode without verification to get expiry
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except jwt.InvalidTokenError:
        return None
