"""Authentication middleware for FastAPI."""

from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlmodel import Session

from app.models.user import User
from app.services.auth_service import AuthService
from app.core.database import get_session
from app.core.redis import get_redis


security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication."""

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and verify authentication.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from next handler
        """
        # Skip authentication for public endpoints
        public_paths = [
            '/docs',
            '/redoc',
            '/openapi.json',
            '/api/v1/auth/register',
            '/api/v1/auth/login',
            '/api/v1/auth/refresh',
            '/api/v1/auth/reset-password',
            '/api/v1/auth/confirm-reset-password',
        ]

        if request.url.path in public_paths:
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            # Allow request to proceed - individual endpoints can enforce auth
            return await call_next(request)

        # Extract token
        token = auth_header.replace('Bearer ', '')

        # Verify token and attach user to request state
        try:
            # Get dependencies
            db = next(get_session())
            redis = await get_redis()

            auth_service = AuthService(db, redis)
            user = await auth_service.verify_access_token(token)

            if user:
                request.state.user = user
                request.state.token = token
        except (ValueError, RuntimeError, ConnectionError):
            # If verification fails, continue without user
            pass

        response = await call_next(request)
        return response


async def get_current_user(request: Request) -> User:
    """
    Dependency to get current authenticated user.

    Args:
        request: FastAPI request

    Returns:
        Current user

    Raises:
        HTTPException: If user is not authenticated
    """
    user = getattr(request.state, 'user', None)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Not authenticated',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return user


async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Dependency to get current user if authenticated.

    Args:
        request: FastAPI request

    Returns:
        Current user or None
    """
    return getattr(request.state, 'user', None)


async def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = security,
    db: Session = None,
) -> User:
    """
    Dependency to verify token and return user.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Authenticated user

    Raises:
        HTTPException: If token is invalid
    """
    from app.core.redis import redis_client

    if not db:
        db = next(get_session())

    auth_service = AuthService(db, redis_client)

    user = await auth_service.verify_access_token(credentials.credentials)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid or expired token',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return user
