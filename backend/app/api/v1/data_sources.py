import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.core.enums import DataSourceType
from app.models.user import User
from app.schemas.data_source import (
    DataSourceDetailResponse,
    DataSourceResponse,
    QualityReportResponse,
)
from app.services.data_source_service import DataSourceService
from app.schemas.data_source import DataSourceCreate

router = APIRouter()


@router.post(
    "",
    response_model=DataSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_data_source(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    name: str = Form(...),
    source_type: DataSourceType = Form(...),
    description: str | None = Form(None),
    year_start: int | None = Form(None),
    year_end: int | None = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)

    metadata = DataSourceCreate(
        name=name,
        description=description,
        source_type=source_type,
        year_start=year_start,
        year_end=year_end,
    )

    service = DataSourceService(db)
    return await service.upload_data_source(project_id, metadata, file, current_user)


@router.get("", response_model=list[DataSourceResponse])
async def list_data_sources(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = DataSourceService(db)
    return await service.list_data_sources(project_id)


@router.get("/{data_source_id}", response_model=DataSourceDetailResponse)
async def get_data_source(
    project_id: uuid.UUID,
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = DataSourceService(db)
    try:
        return await service.get_data_source(data_source_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{data_source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_source(
    project_id: uuid.UUID,
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = DataSourceService(db)
    try:
        await service.delete_data_source(data_source_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post(
    "/{data_source_id}/quality-check",
    response_model=QualityReportResponse,
)
async def run_quality_check(
    project_id: uuid.UUID,
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = DataSourceService(db)
    try:
        return await service.run_quality_checks(data_source_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get(
    "/{data_source_id}/quality-report",
    response_model=QualityReportResponse,
)
async def get_quality_report(
    project_id: uuid.UUID,
    data_source_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = DataSourceService(db)
    try:
        return await service.get_quality_report(data_source_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
