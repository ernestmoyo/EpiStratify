"""Intervention tailoring API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.core.enums import InterventionCode, RiskLevel
from app.models.user import User
from app.schemas.intervention import (
    InterventionDecisionTree,
    InterventionPlanCreate,
    InterventionPlanResponse,
    InterventionRecommendation,
)
from app.services.intervention_service import InterventionService

router = APIRouter()


@router.get("/decision-trees", response_model=list[InterventionDecisionTree])
async def list_decision_trees(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all WHO intervention decision trees."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    return service.get_all_decision_trees()


@router.get(
    "/decision-trees/{intervention_code}",
    response_model=InterventionDecisionTree,
)
async def get_decision_tree(
    project_id: uuid.UUID,
    intervention_code: InterventionCode,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get decision tree for a specific intervention."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    try:
        return service.get_decision_tree(intervention_code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post(
    "/recommendations",
    response_model=list[InterventionRecommendation],
)
async def get_recommendations(
    project_id: uuid.UUID,
    risk_level: RiskLevel = Query(...),
    context: dict[str, Any] = Body(default={}),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tailored recommendations for all interventions given a risk level and context."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    recommendations = []
    for code in InterventionCode:
        rec = service.get_recommendation(code, risk_level, context)
        recommendations.append(rec)
    return recommendations


@router.post(
    "/recommendations/{intervention_code}",
    response_model=InterventionRecommendation,
)
async def get_recommendation(
    project_id: uuid.UUID,
    intervention_code: InterventionCode,
    risk_level: RiskLevel = Query(...),
    context: dict[str, Any] = Body(default={}),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recommendation for a specific intervention."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    try:
        return service.get_recommendation(intervention_code, risk_level, context)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.get("/plans", response_model=list[InterventionPlanResponse])
async def list_plans(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all intervention plans for a project."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    return await service.list_intervention_plans(project_id)


@router.post(
    "/plans",
    response_model=InterventionPlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    project_id: uuid.UUID,
    data: InterventionPlanCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an intervention plan for an operational unit."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    return await service.create_intervention_plan(project_id, data, current_user)


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    project_id: uuid.UUID,
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an intervention plan."""
    await get_project_member(project_id, current_user, db)
    service = InterventionService(db)
    try:
        await service.delete_intervention_plan(plan_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
