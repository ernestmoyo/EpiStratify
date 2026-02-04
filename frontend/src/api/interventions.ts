import apiClient from './client'

export interface TailoringOption {
  value: string
  label: string
  conditions: Record<string, unknown> | null
  help_text: string | null
}

export interface TailoringQuestion {
  id: string
  question: string
  question_type: string
  options: TailoringOption[] | null
  default: unknown | null
  min_value: number | null
  max_value: number | null
  help_text: string | null
}

export interface InterventionDecisionTree {
  intervention_code: string
  intervention_name: string
  eligibility_criteria: Array<Record<string, unknown>>
  tailoring_questions: TailoringQuestion[]
}

export interface InterventionRecommendation {
  intervention_code: string
  intervention_name: string
  is_eligible: boolean
  ineligibility_reasons: string[] | null
  tailoring_questions: TailoringQuestion[] | null
  default_recommendations: Record<string, unknown> | null
  context_summary: Record<string, unknown> | null
}

export interface InterventionPlanCreate {
  admin_unit_name: string
  admin_unit_code?: string
  intervention_code: string
  tailoring_decisions?: Record<string, unknown>
  coverage_target?: number
  delivery_strategy?: string
  target_population?: number
  notes?: string
}

export interface InterventionPlanResponse {
  id: string
  admin_unit_name: string
  admin_unit_code: string | null
  intervention_code: string
  is_eligible: boolean
  tailoring_decisions: Record<string, unknown> | null
  coverage_target: number | null
  delivery_strategy: string | null
  target_population: number | null
  notes: string | null
  created_at: string
}

export const interventionsApi = {
  getDecisionTrees(projectId: string) {
    return apiClient.get<InterventionDecisionTree[]>(
      `/projects/${projectId}/interventions/decision-trees`,
    )
  },

  getDecisionTree(projectId: string, interventionCode: string) {
    return apiClient.get<InterventionDecisionTree>(
      `/projects/${projectId}/interventions/decision-trees/${interventionCode}`,
    )
  },

  getRecommendations(
    projectId: string,
    riskLevel: string,
    context: Record<string, unknown> = {},
  ) {
    return apiClient.post<InterventionRecommendation[]>(
      `/projects/${projectId}/interventions/recommendations?risk_level=${riskLevel}`,
      context,
    )
  },

  getRecommendation(
    projectId: string,
    interventionCode: string,
    riskLevel: string,
    context: Record<string, unknown> = {},
  ) {
    return apiClient.post<InterventionRecommendation>(
      `/projects/${projectId}/interventions/recommendations/${interventionCode}?risk_level=${riskLevel}`,
      context,
    )
  },

  listPlans(projectId: string) {
    return apiClient.get<InterventionPlanResponse[]>(
      `/projects/${projectId}/interventions/plans`,
    )
  },

  createPlan(projectId: string, data: InterventionPlanCreate) {
    return apiClient.post<InterventionPlanResponse>(
      `/projects/${projectId}/interventions/plans`,
      data,
    )
  },

  deletePlan(projectId: string, planId: string) {
    return apiClient.delete(`/projects/${projectId}/interventions/plans/${planId}`)
  },
}
