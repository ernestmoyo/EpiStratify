"""Unit tests for the workflow service."""

import pytest

from app.core.enums import (
    PrerequisiteType,
    StepStatus,
    WorkflowStep,
    WORKFLOW_STEP_ORDER,
)
from app.services.workflow_service import PREREQUISITES


class TestWorkflowPrerequisites:
    """Test the prerequisite graph is correctly defined."""

    def test_all_steps_have_prerequisites_entry(self):
        for step in WorkflowStep:
            assert step in PREREQUISITES, f"Missing prerequisites for {step}"

    def test_first_step_has_no_blocking_prerequisites(self):
        first_step = WORKFLOW_STEP_ORDER[0]
        prereqs = PREREQUISITES[first_step]
        blocking = [
            p for p, t in prereqs if t == PrerequisiteType.BLOCKING
        ]
        assert len(blocking) == 0, "First step should have no blocking prerequisites"

    def test_step_order_has_10_steps(self):
        assert len(WORKFLOW_STEP_ORDER) == 10

    def test_data_assembly_requires_planning(self):
        prereqs = PREREQUISITES[WorkflowStep.DATA_ASSEMBLY]
        steps = [p for p, _ in prereqs]
        assert WorkflowStep.PLANNING_PREPAREDNESS in steps

    def test_stratification_requires_situation_analysis(self):
        prereqs = PREREQUISITES[WorkflowStep.STRATIFICATION]
        steps = [p for p, _ in prereqs]
        assert WorkflowStep.SITUATION_ANALYSIS in steps

    def test_intervention_tailoring_requires_stratification(self):
        prereqs = PREREQUISITES[WorkflowStep.INTERVENTION_TAILORING]
        steps = [p for p, _ in prereqs]
        assert WorkflowStep.STRATIFICATION in steps

    def test_monitoring_has_non_blocking_prerequisite(self):
        prereqs = PREREQUISITES[WorkflowStep.MONITORING_EVALUATION]
        for _, prereq_type in prereqs:
            assert prereq_type == PrerequisiteType.NON_BLOCKING

    def test_no_circular_dependencies(self):
        """Verify there are no cycles in the prerequisite graph."""
        visited = set()

        def visit(step: WorkflowStep, path: set):
            if step in path:
                raise AssertionError(f"Circular dependency detected at {step}")
            path.add(step)
            for prereq, _ in PREREQUISITES.get(step, []):
                visit(prereq, path.copy())
            visited.add(step)

        for step in WorkflowStep:
            visit(step, set())
