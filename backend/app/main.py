import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

logger = logging.getLogger(__name__)

# Ensure all models are imported so Base.metadata is complete
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create extensions and tables if they don't exist
    from sqlalchemy import text

    # Try to create extensions in a separate transaction (ok if it fails)
    try:
        async with engine.begin() as conn:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        logger.info("PostgreSQL extensions verified")
    except Exception as e:
        logger.warning("Could not create extensions (PostGIS may not be available): %s", e)

    # Create tables in a clean transaction
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified/created")
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="WHO Subnational Tailoring (SNT) Planning Toolkit for malaria programs",
    lifespan=lifespan,
)

cors_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://localhost:3000",
]
if settings.CORS_ORIGINS:
    cors_origins.extend(
        origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
