import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.core.enums import WorkflowStep
from app.models.user import User
from app.schemas.workflow import (
    StepStatusResponse,
    StepUpdateRequest,
    StepValidationResponse,
    WorkflowStateResponse,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("", response_model=WorkflowStateResponse)
async def get_workflow(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    return await service.get_workflow_state(project_id)


@router.get("/steps/{step}", response_model=StepStatusResponse)
async def get_step(
    project_id: uuid.UUID,
    step: WorkflowStep,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    try:
        return await service.get_step(project_id, step)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.patch("/steps/{step}", response_model=StepStatusResponse)
async def update_step(
    project_id: uuid.UUID,
    step: WorkflowStep,
    data: StepUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    try:
        return await service.update_step(project_id, step, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/steps/{step}/validate", response_model=StepValidationResponse)
async def validate_step(
    project_id: uuid.UUID,
    step: WorkflowStep,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    return await service.validate_step(project_id, step)


@router.post("/steps/{step}/complete", response_model=StepStatusResponse)
async def complete_step(
    project_id: uuid.UUID,
    step: WorkflowStep,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    try:
        return await service.complete_step(project_id, step, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/steps/{step}/reopen", response_model=StepStatusResponse)
async def reopen_step(
    project_id: uuid.UUID,
    step: WorkflowStep,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    await get_project_member(project_id, current_user, db)
    service = WorkflowService(db)
    try:
        return await service.reopen_step(project_id, step)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
