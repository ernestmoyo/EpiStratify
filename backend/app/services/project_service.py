import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import ProjectRole, ProjectStatus
from app.models.project import Project, ProjectMember
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.workflow_service import WorkflowService


class ProjectService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self, data: ProjectCreate, user: User
    ) -> ProjectResponse:
        project = Project(
            name=data.name,
            description=data.description,
            country=data.country,
            admin_level=data.admin_level,
            year=data.year,
            status=ProjectStatus.DRAFT.value,
        )
        self.db.add(project)
        await self.db.flush()

        # Add creator as owner
        member = ProjectMember(
            project_id=project.id,
            user_id=user.id,
            role=ProjectRole.OWNER.value,
        )
        self.db.add(member)

        # Initialize workflow states
        workflow_service = WorkflowService(self.db)
        await workflow_service.initialize_workflow(project.id)

        await self.db.flush()
        return ProjectResponse.model_validate(project)

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id, Project.is_archived == False
            )
        )
        return result.scalar_one_or_none()

    async def list_user_projects(self, user_id: uuid.UUID) -> list[ProjectResponse]:
        result = await self.db.execute(
            select(Project)
            .join(ProjectMember)
            .where(
                ProjectMember.user_id == user_id,
                Project.is_archived == False,
            )
            .order_by(Project.updated_at.desc())
        )
        projects = result.scalars().all()
        return [ProjectResponse.model_validate(p) for p in projects]

    async def update_project(
        self, project_id: uuid.UUID, data: ProjectUpdate
    ) -> ProjectResponse:
        project = await self.get_project(project_id)
        if project is None:
            raise ValueError("Project not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)

        await self.db.flush()
        return ProjectResponse.model_validate(project)

    async def archive_project(self, project_id: uuid.UUID) -> None:
        project = await self.get_project(project_id)
        if project is None:
            raise ValueError("Project not found")

        project.is_archived = True
        await self.db.flush()
