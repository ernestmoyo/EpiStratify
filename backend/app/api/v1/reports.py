"""Report generation API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.models.user import User
from app.schemas.report import (
    ReportGenerateRequest,
    ReportListResponse,
    ReportRecordResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.post(
    "",
    response_model=ReportRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    project_id: uuid.UUID,
    request: ReportGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a report for the project."""
    await get_project_member(project_id, current_user, db)
    service = ReportService(db)
    try:
        return await service.generate_report(project_id, request, current_user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("", response_model=ReportListResponse)
async def list_reports(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all reports for a project."""
    await get_project_member(project_id, current_user, db)
    service = ReportService(db)
    return await service.list_reports(project_id)


@router.get("/{report_id}", response_model=ReportRecordResponse)
async def get_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get report metadata."""
    await get_project_member(project_id, current_user, db)
    service = ReportService(db)
    try:
        return await service.get_report(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/{report_id}/download")
async def download_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the report file."""
    await get_project_member(project_id, current_user, db)
    service = ReportService(db)
    try:
        file_path = await service.get_report_file_path(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a report and its file."""
    await get_project_member(project_id, current_user, db)
    service = ReportService(db)
    try:
        await service.delete_report(report_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
