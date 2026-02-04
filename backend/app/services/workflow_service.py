import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    PrerequisiteType,
    StepStatus,
    WorkflowStep,
    WORKFLOW_STEP_LABELS,
    WORKFLOW_STEP_ORDER,
)
from app.models.workflow import WorkflowState
from app.schemas.workflow import (
    StepStatusResponse,
    StepUpdateRequest,
    StepValidationResponse,
    WorkflowStateResponse,
)

# Prerequisite graph: step -> list of (prerequisite_step, type)
PREREQUISITES: dict[WorkflowStep, list[tuple[WorkflowStep, PrerequisiteType]]] = {
    WorkflowStep.PLANNING_PREPAREDNESS: [],
    WorkflowStep.DATA_ASSEMBLY: [
        (WorkflowStep.PLANNING_PREPAREDNESS, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.SITUATION_ANALYSIS: [
        (WorkflowStep.DATA_ASSEMBLY, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.STRATIFICATION: [
        (WorkflowStep.SITUATION_ANALYSIS, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.INTERVENTION_TAILORING: [
        (WorkflowStep.STRATIFICATION, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.IMPACT_FORECASTING: [
        (WorkflowStep.INTERVENTION_TAILORING, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.SCENARIO_SELECTION: [
        (WorkflowStep.IMPACT_FORECASTING, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.RESOURCE_OPTIMIZATION: [
        (WorkflowStep.SCENARIO_SELECTION, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.SERVICE_DELIVERY: [
        (WorkflowStep.RESOURCE_OPTIMIZATION, PrerequisiteType.BLOCKING),
    ],
    WorkflowStep.MONITORING_EVALUATION: [
        (WorkflowStep.SERVICE_DELIVERY, PrerequisiteType.NON_BLOCKING),
    ],
}


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def initialize_workflow(self, project_id: uuid.UUID) -> None:
        """Create all 10 workflow state records for a new project."""
        for step in WORKFLOW_STEP_ORDER:
            state = WorkflowState(
                project_id=project_id,
                step=step.value,
                status=StepStatus.NOT_STARTED.value,
                completion_percentage=0.0,
            )
            self.db.add(state)

    async def get_workflow_state(
        self, project_id: uuid.UUID
    ) -> WorkflowStateResponse:
        """Get full workflow state with accessibility info."""
        states = await self._get_all_states(project_id)
        state_map = {s.step: s for s in states}

        steps = []
        completed_count = 0
        current_step = None

        for step in WORKFLOW_STEP_ORDER:
            state = state_map.get(step.value)
            if state is None:
                continue

            blocking, non_blocking = self._get_prerequisite_status(
                step, state_map
            )
            is_accessible = len(blocking) == 0

            if state.status == StepStatus.COMPLETED.value:
                completed_count += 1
            elif current_step is None and is_accessible:
                current_step = step

            steps.append(
                StepStatusResponse(
                    step=step,
                    label=WORKFLOW_STEP_LABELS[step],
                    status=StepStatus(state.status),
                    completion_percentage=state.completion_percentage,
                    is_accessible=is_accessible,
                    blocking_prerequisites=blocking,
                    non_blocking_prerequisites=non_blocking,
                    notes=state.notes,
                    completed_at=state.completed_at,
                    data=state.data,
                    validation_errors=state.validation_errors,
                )
            )

        overall_progress = (completed_count / len(WORKFLOW_STEP_ORDER)) * 100

        return WorkflowStateResponse(
            project_id=project_id,
            steps=steps,
            overall_progress=overall_progress,
            current_step=current_step,
        )

    async def get_step(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> StepStatusResponse:
        """Get single step status."""
        states = await self._get_all_states(project_id)
        state_map = {s.step: s for s in states}

        state = state_map.get(step.value)
        if state is None:
            raise ValueError(f"Step {step.value} not found")

        blocking, non_blocking = self._get_prerequisite_status(step, state_map)

        return StepStatusResponse(
            step=step,
            label=WORKFLOW_STEP_LABELS[step],
            status=StepStatus(state.status),
            completion_percentage=state.completion_percentage,
            is_accessible=len(blocking) == 0,
            blocking_prerequisites=blocking,
            non_blocking_prerequisites=non_blocking,
            notes=state.notes,
            completed_at=state.completed_at,
            data=state.data,
            validation_errors=state.validation_errors,
        )

    async def update_step(
        self, project_id: uuid.UUID, step: WorkflowStep, data: StepUpdateRequest
    ) -> StepStatusResponse:
        """Update step progress (notes, completion percentage, data)."""
        state = await self._get_state(project_id, step)

        if state.status == StepStatus.NOT_STARTED.value:
            state.status = StepStatus.IN_PROGRESS.value

        if data.notes is not None:
            state.notes = data.notes
        if data.completion_percentage is not None:
            state.completion_percentage = data.completion_percentage
        if data.data is not None:
            state.data = data.data

        await self.db.flush()
        return await self.get_step(project_id, step)

    async def validate_step(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> StepValidationResponse:
        """Run validation for a step."""
        validators = {
            WorkflowStep.PLANNING_PREPAREDNESS: self._validate_planning,
            WorkflowStep.DATA_ASSEMBLY: self._validate_data_assembly,
            WorkflowStep.SITUATION_ANALYSIS: self._validate_situation_analysis,
            WorkflowStep.STRATIFICATION: self._validate_stratification,
            WorkflowStep.INTERVENTION_TAILORING: self._validate_generic,
            WorkflowStep.IMPACT_FORECASTING: self._validate_generic,
            WorkflowStep.SCENARIO_SELECTION: self._validate_generic,
            WorkflowStep.RESOURCE_OPTIMIZATION: self._validate_generic,
            WorkflowStep.SERVICE_DELIVERY: self._validate_generic,
            WorkflowStep.MONITORING_EVALUATION: self._validate_generic,
        }

        validator = validators.get(step, self._validate_generic)
        errors, warnings = await validator(project_id, step)

        state = await self._get_state(project_id, step)
        state.validation_errors = {"errors": errors, "warnings": warnings}
        await self.db.flush()

        return StepValidationResponse(
            step=step,
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    async def complete_step(
        self,
        project_id: uuid.UUID,
        step: WorkflowStep,
        user_id: uuid.UUID,
    ) -> StepStatusResponse:
        """Mark step as completed after validation passes."""
        validation = await self.validate_step(project_id, step)
        if not validation.is_valid:
            raise ValueError(
                f"Step cannot be completed: {', '.join(validation.errors)}"
            )

        state = await self._get_state(project_id, step)
        state.status = StepStatus.COMPLETED.value
        state.completion_percentage = 100.0
        state.completed_at = datetime.now(timezone.utc)
        state.completed_by = user_id

        await self.db.flush()
        return await self.get_step(project_id, step)

    async def reopen_step(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> StepStatusResponse:
        """Reopen a completed step. Also reopens dependent steps."""
        state = await self._get_state(project_id, step)
        state.status = StepStatus.IN_PROGRESS.value
        state.completed_at = None
        state.completed_by = None

        # Cascade: reopen all downstream steps that depend on this one
        for downstream_step in WORKFLOW_STEP_ORDER:
            prereqs = PREREQUISITES.get(downstream_step, [])
            for prereq_step, prereq_type in prereqs:
                if prereq_step == step and prereq_type == PrerequisiteType.BLOCKING:
                    downstream_state = await self._get_state(
                        project_id, downstream_step
                    )
                    if downstream_state.status == StepStatus.COMPLETED.value:
                        downstream_state.status = StepStatus.IN_PROGRESS.value
                        downstream_state.completed_at = None
                        downstream_state.completed_by = None

        await self.db.flush()
        return await self.get_step(project_id, step)

    # --- Private helpers ---

    async def _get_all_states(
        self, project_id: uuid.UUID
    ) -> list[WorkflowState]:
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.project_id == project_id
            )
        )
        return list(result.scalars().all())

    async def _get_state(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> WorkflowState:
        result = await self.db.execute(
            select(WorkflowState).where(
                WorkflowState.project_id == project_id,
                WorkflowState.step == step.value,
            )
        )
        state = result.scalar_one_or_none()
        if state is None:
            raise ValueError(f"Workflow state for step {step.value} not found")
        return state

    def _get_prerequisite_status(
        self,
        step: WorkflowStep,
        state_map: dict[str, WorkflowState],
    ) -> tuple[list[str], list[str]]:
        """Return (blocking_incomplete, non_blocking_incomplete) prerequisite labels."""
        blocking = []
        non_blocking = []

        for prereq_step, prereq_type in PREREQUISITES.get(step, []):
            prereq_state = state_map.get(prereq_step.value)
            if prereq_state is None or prereq_state.status != StepStatus.COMPLETED.value:
                label = WORKFLOW_STEP_LABELS[prereq_step]
                if prereq_type == PrerequisiteType.BLOCKING:
                    blocking.append(label)
                else:
                    non_blocking.append(label)

        return blocking, non_blocking

    # --- Step validators ---

    async def _validate_planning(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        state = await self._get_state(project_id, step)
        data = state.data or {}

        if not data.get("scope_of_work"):
            errors.append("Scope of work not documented")
        if not data.get("operational_unit"):
            errors.append("Operational unit (district/region) not defined")
        if not data.get("timeline"):
            warnings.append("Timeline not yet created")

        return errors, warnings

    async def _validate_data_assembly(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> tuple[list[str], list[str]]:
        from app.models.data_source import DataSource

        errors = []
        warnings = []

        result = await self.db.execute(
            select(DataSource).where(DataSource.project_id == project_id)
        )
        data_sources = result.scalars().all()

        if len(data_sources) == 0:
            errors.append("No data sources uploaded")
            return errors, warnings

        source_types = {ds.source_type for ds in data_sources}
        required_types = {"epidemiological", "demographic"}
        missing = required_types - source_types
        if missing:
            errors.append(f"Missing required data types: {', '.join(missing)}")

        # Check quality scores
        for ds in data_sources:
            if ds.quality_score is not None and ds.quality_score < 0.5:
                warnings.append(
                    f"Low quality score for '{ds.name}': {ds.quality_score:.0%}"
                )

        return errors, warnings

    async def _validate_situation_analysis(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> tuple[list[str], list[str]]:
        errors = []
        warnings = []

        state = await self._get_state(project_id, step)
        data = state.data or {}

        if not data.get("analysis_completed"):
            errors.append("Situation analysis not marked as completed")

        return errors, warnings

    async def _validate_stratification(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> tuple[list[str], list[str]]:
        from app.models.stratification import StratificationConfig, StratificationResult

        errors = []
        warnings = []

        result = await self.db.execute(
            select(StratificationConfig).where(
                StratificationConfig.project_id == project_id,
                StratificationConfig.is_active == True,
            )
        )
        configs = result.scalars().all()

        if len(configs) == 0:
            errors.append("No active stratification configuration")
            return errors, warnings

        # Check if results exist
        for config in configs:
            result = await self.db.execute(
                select(StratificationResult).where(
                    StratificationResult.config_id == config.id
                )
            )
            results = result.scalars().all()
            if len(results) == 0:
                errors.append(
                    f"No stratification results for config '{config.name}'"
                )

        return errors, warnings

    async def _validate_generic(
        self, project_id: uuid.UUID, step: WorkflowStep
    ) -> tuple[list[str], list[str]]:
        """Generic validator that checks completion percentage."""
        state = await self._get_state(project_id, step)

        errors = []
        warnings = []

        if state.completion_percentage < 100:
            warnings.append(
                f"Step is {state.completion_percentage:.0f}% complete"
            )

        return errors, warnings
