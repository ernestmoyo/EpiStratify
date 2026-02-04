"""Seed data script for development."""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.enums import (
    ProjectRole,
    ProjectStatus,
    StepStatus,
    StratificationMetric,
    WorkflowStep,
    WORKFLOW_STEP_ORDER,
)
from app.core.security import hash_password
from app.db.base import Base
from app.models.project import Project, ProjectMember
from app.models.stratification import StratificationConfig
from app.models.user import User
from app.models.workflow import WorkflowState


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        # Create demo user
        demo_user = User(
            email="demo@epistratify.org",
            hashed_password=hash_password("demo1234"),
            full_name="Demo User",
            organization="WHO",
            is_active=True,
        )
        session.add(demo_user)
        await session.flush()

        print(f"Created demo user: demo@epistratify.org / demo1234")

        # Create sample project
        project = Project(
            name="Ghana SNT 2024",
            description="Sample SNT project for Ghana using 2024 data",
            country="Ghana",
            admin_level=1,
            year=2024,
            status=ProjectStatus.IN_PROGRESS.value,
        )
        session.add(project)
        await session.flush()

        print(f"Created project: {project.name}")

        # Add user as owner
        member = ProjectMember(
            project_id=project.id,
            user_id=demo_user.id,
            role=ProjectRole.OWNER.value,
        )
        session.add(member)

        # Initialize workflow states
        for step in WORKFLOW_STEP_ORDER:
            state = WorkflowState(
                project_id=project.id,
                step=step.value,
                status=StepStatus.NOT_STARTED.value,
                completion_percentage=0.0,
            )
            session.add(state)

        print("Initialized 10 workflow steps")

        # Create default stratification config (WHO PfPR thresholds)
        config = StratificationConfig(
            project_id=project.id,
            name="WHO PfPR Default Thresholds",
            metric=StratificationMetric.PFPR.value,
            thresholds={
                "very_low": {"min_value": 0, "max_value": 1},
                "low": {"min_value": 1, "max_value": 10},
                "moderate": {"min_value": 10, "max_value": 35},
                "high": {"min_value": 35, "max_value": 100},
            },
            created_by=demo_user.id,
            is_active=True,
        )
        session.add(config)

        # Create incidence-based config
        incidence_config = StratificationConfig(
            project_id=project.id,
            name="WHO Incidence Thresholds",
            metric=StratificationMetric.INCIDENCE.value,
            thresholds={
                "very_low": {"min_value": 0, "max_value": 100},
                "low": {"min_value": 100, "max_value": 250},
                "moderate": {"min_value": 250, "max_value": 450},
                "high": {"min_value": 450, "max_value": 10000},
            },
            created_by=demo_user.id,
            is_active=True,
        )
        session.add(incidence_config)

        print("Created default stratification configurations")

        await session.commit()
        print("\nSeed data created successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
