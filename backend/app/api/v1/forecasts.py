"""Impact forecasting API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.models.user import User
from app.schemas.forecast import (
    ForecastComparisonResponse,
    ForecastRequest,
    ForecastResultResponse,
)
from app.services.forecast_service import ForecastService

router = APIRouter()


@router.post(
    "/scenarios/{scenario_id}/run",
    response_model=ForecastResultResponse,
    status_code=status.HTTP_201_CREATED,
)
async def run_forecast(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    request: ForecastRequest,
    baseline_data: dict[str, Any] | None = Body(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Run impact forecast for a scenario.

    Optional baseline_data:
    - baseline_cases: int (annual baseline cases)
    - baseline_deaths: int (annual baseline deaths)
    - baseline_prevalence: float (PfPR %)
    - population: int
    """
    await get_project_member(project_id, current_user, db)
    service = ForecastService(db)
    try:
        return await service.run_forecast(scenario_id, request, baseline_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get(
    "/scenarios/{scenario_id}/forecasts",
    response_model=list[ForecastResultResponse],
)
async def list_forecasts(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all forecasts for a scenario."""
    await get_project_member(project_id, current_user, db)
    service = ForecastService(db)
    return await service.list_forecasts(scenario_id)


@router.get(
    "/forecasts/{forecast_id}",
    response_model=ForecastResultResponse,
)
async def get_forecast(
    project_id: uuid.UUID,
    forecast_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific forecast result."""
    await get_project_member(project_id, current_user, db)
    service = ForecastService(db)
    try:
        return await service.get_forecast(forecast_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get(
    "/compare",
    response_model=ForecastComparisonResponse,
)
async def compare_forecasts(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare forecasts across all scenarios in a project."""
    await get_project_member(project_id, current_user, db)
    service = ForecastService(db)
    return await service.compare_forecasts(project_id)
