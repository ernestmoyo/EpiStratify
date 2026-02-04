from fastapi import APIRouter

from app.api.v1 import (
    auth,
    data_sources,
    forecasts,
    health,
    interventions,
    projects,
    reports,
    scenarios,
    stratification,
    workflow,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(
    workflow.router,
    prefix="/projects/{project_id}/workflow",
    tags=["workflow"],
)
api_router.include_router(
    data_sources.router,
    prefix="/projects/{project_id}/data-sources",
    tags=["data-sources"],
)
api_router.include_router(
    stratification.router,
    prefix="/projects/{project_id}/stratification",
    tags=["stratification"],
)
api_router.include_router(
    interventions.router,
    prefix="/projects/{project_id}/interventions",
    tags=["interventions"],
)
api_router.include_router(
    scenarios.router,
    prefix="/projects/{project_id}/scenarios",
    tags=["scenarios"],
)
api_router.include_router(
    forecasts.router,
    prefix="/projects/{project_id}/forecasts",
    tags=["forecasts"],
)
api_router.include_router(
    reports.router,
    prefix="/projects/{project_id}/reports",
    tags=["reports"],
)
