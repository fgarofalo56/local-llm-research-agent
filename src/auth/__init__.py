"""
Authentication Module
Phase 4.5: Security & Authentication

JWT-based authentication with password hashing.
"""

from src.auth.jwt import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry,
    verify_access_token,
    verify_refresh_token,
)
from src.auth.password import (
    generate_password,
    hash_password,
    validate_password_strength,
    verify_password,
)

__all__ = [
    # JWT
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "verify_access_token",
    "verify_refresh_token",
    "get_token_expiry",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    # Password
    "hash_password",
    "verify_password",
    "generate_password",
    "validate_password_strength",
]
