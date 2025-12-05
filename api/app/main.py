"""FastAPI application initialization."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.mongodb import mongodb_client
from app.core.redis import redis_client
from app.core.logging import configure_logging, get_logger
from app.core.sentry import init_sentry
from app.api.v1 import router as api_v1_router
# Configure logging
configure_logging()
logger = get_logger(__name__)

# Initialize Sentry
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting application", app_name=settings.app_name)

    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Connect to MongoDB
        await mongodb_client.connect()
        logger.info("MongoDB connected")

        # Connect to Redis
        await redis_client.connect()
        logger.info("Redis connected")

    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down application")

    try:
        await close_db()
        await mongodb_client.close()
        await redis_client.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Low-code platform backend with workflow orchestration and AI integration",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": "0.1.0",
        }
    )


@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint.

    Returns:
        Welcome message
    """
    return JSONResponse(
        content={
            "message": "Welcome to Low-Code Platform Backend API",
            "docs": "/docs",
            "health": "/health",
        }
    )

app.include_router(api_v1_router)  # prefix 已经在 v1/__init__.py 中定义了
# TODO: Register API routers here
# from app.api.v1 import api_router
# app.include_router(api_router, prefix=settings.api_v1_prefix)
