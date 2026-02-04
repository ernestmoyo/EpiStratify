from enum import Enum


class WorkflowStep(str, Enum):
    PLANNING_PREPAREDNESS = "planning_preparedness"
    DATA_ASSEMBLY = "data_assembly"
    SITUATION_ANALYSIS = "situation_analysis"
    STRATIFICATION = "stratification"
    INTERVENTION_TAILORING = "intervention_tailoring"
    IMPACT_FORECASTING = "impact_forecasting"
    SCENARIO_SELECTION = "scenario_selection"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    SERVICE_DELIVERY = "service_delivery"
    MONITORING_EVALUATION = "monitoring_evaluation"


# Ordered list for sequential navigation
WORKFLOW_STEP_ORDER = list(WorkflowStep)

WORKFLOW_STEP_LABELS = {
    WorkflowStep.PLANNING_PREPAREDNESS: "Planning and Preparedness",
    WorkflowStep.DATA_ASSEMBLY: "Data Assembly and Management",
    WorkflowStep.SITUATION_ANALYSIS: "Situation Analysis",
    WorkflowStep.STRATIFICATION: "Stratification",
    WorkflowStep.INTERVENTION_TAILORING: "Intervention Tailoring",
    WorkflowStep.IMPACT_FORECASTING: "Impact Forecasting",
    WorkflowStep.SCENARIO_SELECTION: "Strategic Scenario Selection",
    WorkflowStep.RESOURCE_OPTIMIZATION: "Resource Optimization",
    WorkflowStep.SERVICE_DELIVERY: "Service Delivery",
    WorkflowStep.MONITORING_EVALUATION: "Monitoring and Evaluation",
}


class StepStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class PrerequisiteType(str, Enum):
    BLOCKING = "blocking"
    NON_BLOCKING = "non_blocking"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ProjectRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class DataSourceType(str, Enum):
    EPIDEMIOLOGICAL = "epidemiological"
    INTERVENTION = "intervention"
    DEMOGRAPHIC = "demographic"
    GEOSPATIAL = "geospatial"
    ENTOMOLOGICAL = "entomological"
    COMMODITIES = "commodities"


class QualityCheckType(str, Enum):
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    TIMELINESS = "timeliness"
    OUTLIERS = "outliers"
    DISAGGREGATION = "disaggregation"
    DUPLICATES = "duplicates"


class QualityCheckStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class RiskLevel(str, Enum):
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class StratificationMetric(str, Enum):
    PFPR = "pfpr"
    INCIDENCE = "incidence"
    EIR = "eir"


# --- Phase 2 Enums ---


class InterventionCode(str, Enum):
    CM = "cm"           # Case Management
    ITN = "itn"         # Insecticide-Treated Nets
    IRS = "irs"         # Indoor Residual Spraying
    SMC = "smc"         # Seasonal Malaria Chemoprevention
    PMC = "pmc"         # Perennial Malaria Chemoprevention
    IPTP = "iptp"       # Intermittent Preventive Treatment in Pregnancy
    VACCINE = "vaccine"  # RTS,S / R21 Vaccine
    LSM = "lsm"         # Larval Source Management


INTERVENTION_LABELS = {
    InterventionCode.CM: "Case Management",
    InterventionCode.ITN: "Insecticide-Treated Nets",
    InterventionCode.IRS: "Indoor Residual Spraying",
    InterventionCode.SMC: "Seasonal Malaria Chemoprevention",
    InterventionCode.PMC: "Perennial Malaria Chemoprevention",
    InterventionCode.IPTP: "Intermittent Preventive Treatment in Pregnancy",
    InterventionCode.VACCINE: "Malaria Vaccine (RTS,S/R21)",
    InterventionCode.LSM: "Larval Source Management",
}


class ScenarioType(str, Enum):
    IDEAL = "ideal"
    PRIORITIZED = "prioritized"
    BUDGET_CONSTRAINED = "budget_constrained"
    CUSTOM = "custom"


class ForecastStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
