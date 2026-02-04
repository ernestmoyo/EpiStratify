import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.models.user import User
from app.schemas.stratification import (
    GeoJSONFeatureCollection,
    StratificationConfigCreate,
    StratificationConfigResponse,
    StratificationConfigUpdate,
    StratificationResultResponse,
    StratificationSummaryResponse,
)
from app.services.stratification_service import StratificationService

router = APIRouter()


@router.get("/configs", response_model=list[StratificationConfigResponse])
async def list_configs(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    return await service.list_configs(project_id)


@router.post(
    "/configs",
    response_model=StratificationConfigResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_config(
    project_id: uuid.UUID,
    data: StratificationConfigCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    return await service.create_config(project_id, data, current_user)


@router.patch(
    "/configs/{config_id}",
    response_model=StratificationConfigResponse,
)
async def update_config(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    data: StratificationConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    try:
        return await service.update_config(config_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post(
    "/configs/{config_id}/calculate",
    response_model=list[StratificationResultResponse],
)
async def calculate_stratification(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    data: list[dict[str, Any]] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate stratification from provided data.

    Each item should have: admin_unit_name, metric_value,
    and optionally: admin_unit_code, population, cases_annual, deaths_annual.
    """
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    try:
        return await service.calculate_stratification(config_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get(
    "/configs/{config_id}/results",
    response_model=list[StratificationResultResponse],
)
async def get_results(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    return await service.get_results(config_id)


@router.get(
    "/configs/{config_id}/geojson",
    response_model=GeoJSONFeatureCollection,
)
async def get_geojson(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    return await service.get_geojson(config_id)


@router.get(
    "/configs/{config_id}/summary",
    response_model=StratificationSummaryResponse,
)
async def get_summary(
    project_id: uuid.UUID,
    config_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = StratificationService(db)
    try:
        return await service.get_summary(config_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
