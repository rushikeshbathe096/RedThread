from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.exceptions import AppException, app_exception_handler
from backend.app.core.logging import get_logger, setup_logging
from backend.app.db.session import async_engine
import backend.app.db.all_models  # Ensure mapper registry has all models loaded
from backend.app.api.router import api_router

logger = get_logger("redthread.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    setup_logging(debug=settings.DEBUG)
    logger.info(
        "Starting RedThread API service",
        version=settings.VERSION,
        env=settings.APP_ENV,
    )
    yield
    logger.info("Shutting down RedThread API service")
    await async_engine.dispose()


def create_app() -> FastAPI:
    """FastAPI Application Factory adhering to clean architecture."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)

    # Health Check
    @app.get("/health", tags=["System"])
    async def health_check():
        """System health probe checking database connectivity."""
        db_healthy = False
        try:
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1;"))
                db_healthy = True
        except Exception as e:
            logger.error("Health check database failure", error=str(e))

        return {
            "status": "healthy" if db_healthy else "degraded",
            "version": settings.VERSION,
            "database": "connected" if db_healthy else "disconnected",
        }

    # Mount API v1 router
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
