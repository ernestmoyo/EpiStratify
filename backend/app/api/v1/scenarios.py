"""Budget scenario planning API endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, get_project_member
from app.models.user import User
from app.schemas.intervention import (
    ScenarioComparisonResponse,
    ScenarioCostSummary,
    ScenarioCreate,
    ScenarioDetailResponse,
    ScenarioResponse,
    ScenarioUpdate,
)
from app.services.costing_service import CostingService

router = APIRouter()


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all scenarios for a project."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    return await service.list_scenarios(project_id)


@router.post(
    "",
    response_model=ScenarioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_scenario(
    project_id: uuid.UUID,
    data: ScenarioCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an intervention scenario."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    return await service.create_scenario(project_id, data, current_user)


@router.get("/compare/all", response_model=ScenarioComparisonResponse)
async def compare_scenarios(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare all scenarios in a project."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    return await service.compare_scenarios(project_id)


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
async def get_scenario(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scenario details including cost breakdown."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    try:
        return await service.get_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    data: ScenarioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a scenario."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    try:
        return await service.update_scenario(scenario_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a scenario and all associated cost items."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    try:
        await service.delete_scenario(scenario_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/{scenario_id}/calculate-cost", response_model=ScenarioCostSummary)
async def calculate_cost(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    population_data: list[dict[str, Any]] = Body(...),
    unit_costs: dict | None = Body(default=None),
    project_years: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate costs for a scenario.

    Requires population_data: list of
    {"admin_unit_name": str, "admin_unit_code": str, "population": int}
    """
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    try:
        return await service.calculate_scenario_cost(
            scenario_id, population_data, unit_costs, project_years
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post("/{scenario_id}/optimize", response_model=ScenarioResponse)
async def optimize_scenario(
    project_id: uuid.UUID,
    scenario_id: uuid.UUID,
    budget_constraint: float = Body(..., embed=True),
    population_data: list[dict] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Optimize a scenario under a budget constraint using cost-effectiveness."""
    await get_project_member(project_id, current_user, db)
    service = CostingService(db)
    try:
        return await service.optimize_scenario(
            scenario_id, budget_constraint, population_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
