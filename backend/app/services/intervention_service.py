"""Intervention tailoring with WHO decision tree logic (Annex 6)."""

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    INTERVENTION_LABELS,
    InterventionCode,
    RiskLevel,
)
from app.models.intervention import InterventionPlan
from app.models.user import User
from app.schemas.intervention import (
    InterventionDecisionTree,
    InterventionPlanCreate,
    InterventionPlanResponse,
    InterventionRecommendation,
    TailoringOption,
    TailoringQuestion,
)

# WHO-aligned decision trees per intervention
DECISION_TREES: dict[InterventionCode, dict] = {
    InterventionCode.ITN: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["low", "moderate", "high"]},
        ],
        "questions": [
            {
                "id": "itn_type",
                "question": "What type of ITN is most appropriate?",
                "question_type": "select",
                "options": [
                    {
                        "value": "standard_llin",
                        "label": "Standard LLIN",
                        "conditions": {},
                    },
                    {
                        "value": "pbo_llin",
                        "label": "PBO LLIN",
                        "conditions": {"pyrethroid_resistance_pct": ">40"},
                    },
                    {
                        "value": "dual_ai_llin",
                        "label": "Dual Active-Ingredient LLIN",
                        "conditions": {"pyrethroid_resistance_pct": ">60"},
                    },
                ],
                "help_text": "Select based on local insecticide resistance data",
            },
            {
                "id": "distribution_strategy",
                "question": "What distribution strategy?",
                "question_type": "select",
                "options": [
                    {"value": "mass_campaign", "label": "Mass campaign (3-year cycle)"},
                    {"value": "continuous", "label": "Continuous distribution (ANC/EPI)"},
                    {"value": "hybrid", "label": "Hybrid (campaign + continuous top-up)"},
                ],
            },
            {
                "id": "coverage_target",
                "question": "Target coverage (%)?",
                "question_type": "numeric",
                "default": 80,
                "min_value": 50,
                "max_value": 100,
                "help_text": "WHO recommends universal coverage (1 net per 2 people)",
            },
        ],
    },
    InterventionCode.IRS: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["moderate", "high"]},
        ],
        "questions": [
            {
                "id": "insecticide_class",
                "question": "Insecticide class?",
                "question_type": "select",
                "options": [
                    {"value": "pyrethroid", "label": "Pyrethroid"},
                    {"value": "organophosphate", "label": "Organophosphate (Pirimiphos-methyl)"},
                    {"value": "carbamate", "label": "Carbamate (Bendiocarb)"},
                    {"value": "neonicotinoid", "label": "Neonicotinoid (Clothianidin)"},
                ],
                "help_text": "Based on local vector susceptibility testing",
            },
            {
                "id": "spray_rounds",
                "question": "Spray rounds per year?",
                "question_type": "numeric",
                "default": 1,
                "min_value": 1,
                "max_value": 2,
                "help_text": "Depends on insecticide residual duration and transmission season length",
            },
            {
                "id": "geographic_targeting",
                "question": "Geographic targeting approach?",
                "question_type": "select",
                "options": [
                    {"value": "universal", "label": "Universal (all structures)"},
                    {"value": "targeted_high_risk", "label": "High-risk areas only"},
                    {"value": "focal", "label": "Focal (outbreak/hotspot response)"},
                ],
            },
        ],
    },
    InterventionCode.SMC: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["moderate", "high"]},
            {"criterion": "seasonality", "value": "seasonal"},
        ],
        "questions": [
            {
                "id": "target_age",
                "question": "Target age group?",
                "question_type": "select",
                "options": [
                    {"value": "3_59_months", "label": "3-59 months (standard)"},
                    {"value": "3_10_years", "label": "3-10 years (extended)"},
                ],
                "help_text": "Extended age group if high burden in 5-10 year olds",
            },
            {
                "id": "num_cycles",
                "question": "Number of monthly cycles?",
                "question_type": "numeric",
                "default": 4,
                "min_value": 3,
                "max_value": 5,
                "help_text": "Based on length of high transmission season",
            },
            {
                "id": "delivery_strategy",
                "question": "Delivery approach?",
                "question_type": "select",
                "options": [
                    {"value": "door_to_door", "label": "Door-to-door"},
                    {"value": "fixed_point", "label": "Fixed distribution points"},
                    {"value": "school_based", "label": "School-based (if extended age)"},
                ],
            },
        ],
    },
    InterventionCode.IPTP: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["low", "moderate", "high"]},
        ],
        "questions": [
            {
                "id": "num_doses",
                "question": "Minimum IPTp-SP doses?",
                "question_type": "numeric",
                "default": 3,
                "min_value": 3,
                "max_value": 8,
                "help_text": "WHO recommends at least 3 doses at each ANC visit",
            },
            {
                "id": "delivery_platform",
                "question": "Delivery platform?",
                "question_type": "select",
                "options": [
                    {"value": "anc_facility", "label": "ANC at health facility"},
                    {"value": "community", "label": "Community-based delivery"},
                ],
            },
        ],
    },
    InterventionCode.VACCINE: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["moderate", "high"]},
        ],
        "questions": [
            {
                "id": "vaccine_product",
                "question": "Vaccine product?",
                "question_type": "select",
                "options": [
                    {"value": "rtss", "label": "RTS,S/AS01"},
                    {"value": "r21", "label": "R21/Matrix-M"},
                ],
            },
            {
                "id": "delivery_platform",
                "question": "Delivery platform?",
                "question_type": "select",
                "options": [
                    {"value": "epi_routine", "label": "Routine EPI (integrated)"},
                    {"value": "campaign", "label": "Catch-up campaign + routine"},
                ],
            },
            {
                "id": "age_first_dose",
                "question": "Age at first dose (months)?",
                "question_type": "numeric",
                "default": 5,
                "min_value": 5,
                "max_value": 17,
            },
        ],
    },
    InterventionCode.CM: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["very_low", "low", "moderate", "high"]},
        ],
        "questions": [
            {
                "id": "diagnostic_approach",
                "question": "Diagnostic approach?",
                "question_type": "select",
                "options": [
                    {"value": "microscopy", "label": "Microscopy"},
                    {"value": "rdt", "label": "Rapid Diagnostic Test (RDT)"},
                    {"value": "both", "label": "Both (microscopy + RDT)"},
                ],
            },
            {
                "id": "treatment_protocol",
                "question": "First-line treatment?",
                "question_type": "select",
                "options": [
                    {"value": "al", "label": "Artemether-Lumefantrine (AL)"},
                    {"value": "asaq", "label": "Artesunate-Amodiaquine (ASAQ)"},
                    {"value": "dha_ppq", "label": "DHA-Piperaquine"},
                ],
            },
            {
                "id": "community_case_mgmt",
                "question": "Include community case management (iCCM)?",
                "question_type": "boolean",
                "default": True,
                "help_text": "Community health workers diagnose and treat uncomplicated malaria",
            },
        ],
    },
    InterventionCode.PMC: {
        "eligibility": [
            {"criterion": "risk_level", "values": ["moderate", "high"]},
            {"criterion": "seasonality", "value": "perennial"},
        ],
        "questions": [
            {
                "id": "num_doses",
                "question": "Number of PMC doses?",
                "question_type": "numeric",
                "default": 3,
                "min_value": 3,
                "max_value": 6,
            },
            {
                "id": "drug_regimen",
                "question": "Drug regimen?",
                "question_type": "select",
                "options": [
                    {"value": "sp", "label": "Sulfadoxine-Pyrimethamine (SP)"},
                    {"value": "dha_ppq", "label": "DHA-Piperaquine"},
                ],
            },
        ],
    },
    InterventionCode.LSM: {
        "eligibility": [
            {"criterion": "setting", "values": ["urban", "peri_urban"]},
        ],
        "questions": [
            {
                "id": "lsm_type",
                "question": "LSM approach?",
                "question_type": "select",
                "options": [
                    {"value": "environmental", "label": "Environmental management"},
                    {"value": "biological", "label": "Biological control (Bti/Bs)"},
                    {"value": "combined", "label": "Combined approach"},
                ],
            },
            {
                "id": "targeting",
                "question": "Targeting approach?",
                "question_type": "select",
                "options": [
                    {"value": "all_sites", "label": "All identified breeding sites"},
                    {"value": "productive_sites", "label": "Most productive sites only"},
                ],
            },
        ],
    },
}


class InterventionService:
    """Implements WHO intervention tailoring decision trees."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_decision_tree(
        self, intervention_code: InterventionCode
    ) -> InterventionDecisionTree:
        """Get the full decision tree for an intervention."""
        tree_data = DECISION_TREES.get(intervention_code)
        if tree_data is None:
            raise ValueError(f"No decision tree for {intervention_code}")

        questions = []
        for q_data in tree_data["questions"]:
            options = None
            if "options" in q_data:
                options = [TailoringOption(**opt) for opt in q_data["options"]]
            questions.append(
                TailoringQuestion(
                    id=q_data["id"],
                    question=q_data["question"],
                    question_type=q_data.get("question_type", "select"),
                    options=options,
                    default=q_data.get("default"),
                    min_value=q_data.get("min_value"),
                    max_value=q_data.get("max_value"),
                    help_text=q_data.get("help_text"),
                )
            )

        return InterventionDecisionTree(
            intervention_code=intervention_code,
            intervention_name=INTERVENTION_LABELS[intervention_code],
            eligibility_criteria=tree_data["eligibility"],
            tailoring_questions=questions,
        )

    def get_all_decision_trees(self) -> list[InterventionDecisionTree]:
        """Get all available decision trees."""
        return [
            self.get_decision_tree(code) for code in InterventionCode
        ]

    def get_recommendation(
        self,
        intervention_code: InterventionCode,
        risk_level: RiskLevel,
        context: dict[str, Any] | None = None,
    ) -> InterventionRecommendation:
        """Generate a tailored recommendation for a specific unit."""
        context = context or {}
        tree_data = DECISION_TREES.get(intervention_code)
        if tree_data is None:
            raise ValueError(f"No decision tree for {intervention_code}")

        # Check eligibility
        is_eligible, reasons = self._check_eligibility(
            tree_data["eligibility"], risk_level, context
        )

        if not is_eligible:
            return InterventionRecommendation(
                intervention_code=intervention_code,
                intervention_name=INTERVENTION_LABELS[intervention_code],
                is_eligible=False,
                ineligibility_reasons=reasons,
            )

        # Build filtered questions
        tree = self.get_decision_tree(intervention_code)
        filtered_questions = self._filter_questions(
            tree.tailoring_questions, context
        )

        # Generate defaults
        defaults = self._generate_defaults(intervention_code, risk_level, context)

        return InterventionRecommendation(
            intervention_code=intervention_code,
            intervention_name=INTERVENTION_LABELS[intervention_code],
            is_eligible=True,
            tailoring_questions=filtered_questions,
            default_recommendations=defaults,
            context_summary=context,
        )

    async def create_intervention_plan(
        self,
        project_id: uuid.UUID,
        data: InterventionPlanCreate,
        user: User,
    ) -> InterventionPlanResponse:
        """Save an intervention plan for an operational unit."""
        plan = InterventionPlan(
            project_id=project_id,
            admin_unit_name=data.admin_unit_name,
            admin_unit_code=data.admin_unit_code,
            intervention_code=data.intervention_code.value,
            tailoring_decisions=data.tailoring_decisions,
            coverage_target=data.coverage_target,
            delivery_strategy=data.delivery_strategy,
            target_population=data.target_population,
            notes=data.notes,
            created_by=user.id,
        )
        self.db.add(plan)
        await self.db.flush()
        return InterventionPlanResponse.model_validate(plan)

    async def list_intervention_plans(
        self, project_id: uuid.UUID
    ) -> list[InterventionPlanResponse]:
        result = await self.db.execute(
            select(InterventionPlan)
            .where(InterventionPlan.project_id == project_id)
            .order_by(InterventionPlan.admin_unit_name, InterventionPlan.intervention_code)
        )
        plans = result.scalars().all()
        return [InterventionPlanResponse.model_validate(p) for p in plans]

    async def delete_intervention_plan(self, plan_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(InterventionPlan).where(InterventionPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        if plan is None:
            raise ValueError("Intervention plan not found")
        await self.db.delete(plan)

    # --- Private helpers ---

    def _check_eligibility(
        self,
        criteria: list[dict],
        risk_level: RiskLevel,
        context: dict,
    ) -> tuple[bool, list[str]]:
        reasons = []
        for criterion in criteria:
            key = criterion.get("criterion")

            if key == "risk_level":
                valid_levels = criterion.get("values", [])
                if risk_level.value not in valid_levels:
                    reasons.append(
                        f"Risk level '{risk_level.value}' not eligible "
                        f"(requires: {', '.join(valid_levels)})"
                    )

            elif key == "seasonality":
                required = criterion.get("value")
                actual = context.get("seasonality")
                if actual and actual != required:
                    reasons.append(
                        f"Requires {required} transmission (found: {actual})"
                    )

            elif key == "setting":
                valid_settings = criterion.get("values", [])
                actual = context.get("setting")
                if actual and actual not in valid_settings:
                    reasons.append(
                        f"Setting '{actual}' not eligible "
                        f"(requires: {', '.join(valid_settings)})"
                    )

        return len(reasons) == 0, reasons

    def _filter_questions(
        self,
        questions: list[TailoringQuestion],
        context: dict,
    ) -> list[TailoringQuestion]:
        """Filter question options based on context data."""
        filtered = []
        for q in questions:
            if q.options:
                available = []
                for opt in q.options:
                    if opt.conditions:
                        if self._check_option_conditions(opt.conditions, context):
                            available.append(opt)
                    else:
                        available.append(opt)
                q_copy = q.model_copy(update={"options": available if available else q.options})
                filtered.append(q_copy)
            else:
                filtered.append(q)
        return filtered

    def _check_option_conditions(
        self, conditions: dict, context: dict
    ) -> bool:
        for key, required in conditions.items():
            actual = context.get(key)
            if actual is None:
                continue  # Allow if context doesn't have the data
            if isinstance(required, str) and required.startswith(">"):
                threshold = float(required[1:])
                if float(actual) <= threshold:
                    return False
            elif isinstance(required, str) and required.startswith("<"):
                threshold = float(required[1:])
                if float(actual) >= threshold:
                    return False
            elif actual != required:
                return False
        return True

    def _generate_defaults(
        self,
        intervention_code: InterventionCode,
        risk_level: RiskLevel,
        context: dict,
    ) -> dict:
        """Generate default recommendations based on risk level and context."""
        defaults: dict[str, Any] = {}

        if intervention_code == InterventionCode.ITN:
            resistance = context.get("pyrethroid_resistance_pct", 0)
            if resistance > 60:
                defaults["itn_type"] = "dual_ai_llin"
            elif resistance > 40:
                defaults["itn_type"] = "pbo_llin"
            else:
                defaults["itn_type"] = "standard_llin"
            defaults["distribution_strategy"] = "hybrid"
            defaults["coverage_target"] = 80

        elif intervention_code == InterventionCode.IRS:
            defaults["spray_rounds"] = 1
            defaults["geographic_targeting"] = (
                "universal" if risk_level == RiskLevel.HIGH else "targeted_high_risk"
            )

        elif intervention_code == InterventionCode.SMC:
            defaults["target_age"] = "3_59_months"
            defaults["num_cycles"] = 4
            defaults["delivery_strategy"] = "door_to_door"

        elif intervention_code == InterventionCode.VACCINE:
            defaults["vaccine_product"] = "r21"
            defaults["delivery_platform"] = "epi_routine"
            defaults["age_first_dose"] = 5

        elif intervention_code == InterventionCode.CM:
            defaults["diagnostic_approach"] = "rdt"
            defaults["community_case_mgmt"] = True

        return defaults
