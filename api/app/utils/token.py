"""JWT token generation and verification utilities."""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from app.core.config import settings


class TokenType:
    """Token type constants."""

    ACCESS = "access"
    REFRESH = "refresh"


def generate_access_token(user_id: UUID, additional_claims: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate JWT access token.

    Args:
        user_id: User UUID
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT access token
    """
    payload = {
        "user_id": str(user_id),
        "type": TokenType.ACCESS,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": datetime.utcnow(),
    }

    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def generate_refresh_token(user_id: UUID) -> str:
    """
    Generate JWT refresh token.

    Args:
        user_id: User UUID

    Returns:
        Encoded JWT refresh token
    """
    payload = {
        "user_id": str(user_id),
        "type": TokenType.REFRESH,
        "exp": datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token


def verify_token(token: str, token_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token to verify
        token_type: Expected token type (access or refresh)

    Returns:
        Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])

        # Verify token type if specified
        if token_type and payload.get("type") != token_type:
            return None

        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token without verification (for debugging).

    Args:
        token: JWT token to decode

    Returns:
        Token payload if decodable, None otherwise
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except jwt.InvalidTokenError:
        return None
