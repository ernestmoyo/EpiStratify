from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        database=db_status,
    )
