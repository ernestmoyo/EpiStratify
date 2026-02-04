import apiClient from './client'

export interface ScenarioCreate {
  name: string
  description?: string
  scenario_type?: string
  interventions: Record<string, string[]>
}

export interface ScenarioUpdate {
  name?: string
  description?: string
  interventions?: Record<string, string[]>
  is_selected?: boolean
}

export interface ScenarioCostItemResponse {
  id: string
  admin_unit_name: string
  admin_unit_code: string | null
  intervention_code: string
  unit_cost: number | null
  quantity: number | null
  total_cost: number
  cost_category: string | null
  years: number
}

export interface ScenarioResponse {
  id: string
  name: string
  description: string | null
  scenario_type: string
  is_selected: boolean
  interventions: Record<string, string[]>
  total_cost: number | null
  population_covered: number | null
  estimated_cases_averted: number | null
  estimated_deaths_averted: number | null
  created_at: string
}

export interface ScenarioDetailResponse extends ScenarioResponse {
  cost_items: ScenarioCostItemResponse[]
}

export interface ScenarioCostSummary {
  scenario_id: string
  scenario_name: string
  total_cost: number
  cost_by_intervention: Record<string, number>
  cost_by_unit: Record<string, number>
  cost_per_capita: number | null
  total_population: number
}

export interface ScenarioComparisonResponse {
  scenarios: ScenarioResponse[]
  comparison_metrics: Record<string, Record<string, unknown>>
}

export interface PopulationDataItem {
  admin_unit_name: string
  admin_unit_code: string
  population: number
}

export const scenariosApi = {
  list(projectId: string) {
    return apiClient.get<ScenarioResponse[]>(
      `/projects/${projectId}/scenarios`,
    )
  },

  create(projectId: string, data: ScenarioCreate) {
    return apiClient.post<ScenarioResponse>(
      `/projects/${projectId}/scenarios`,
      data,
    )
  },

  get(projectId: string, scenarioId: string) {
    return apiClient.get<ScenarioDetailResponse>(
      `/projects/${projectId}/scenarios/${scenarioId}`,
    )
  },

  update(projectId: string, scenarioId: string, data: ScenarioUpdate) {
    return apiClient.patch<ScenarioResponse>(
      `/projects/${projectId}/scenarios/${scenarioId}`,
      data,
    )
  },

  delete(projectId: string, scenarioId: string) {
    return apiClient.delete(`/projects/${projectId}/scenarios/${scenarioId}`)
  },

  calculateCost(
    projectId: string,
    scenarioId: string,
    populationData: PopulationDataItem[],
    unitCosts?: Record<string, unknown>,
    projectYears = 5,
  ) {
    return apiClient.post<ScenarioCostSummary>(
      `/projects/${projectId}/scenarios/${scenarioId}/calculate-cost?project_years=${projectYears}`,
      { population_data: populationData, unit_costs: unitCosts },
    )
  },

  optimize(
    projectId: string,
    scenarioId: string,
    budgetConstraint: number,
    populationData: PopulationDataItem[],
  ) {
    return apiClient.post<ScenarioResponse>(
      `/projects/${projectId}/scenarios/${scenarioId}/optimize`,
      { budget_constraint: budgetConstraint, population_data: populationData },
    )
  },

  compare(projectId: string) {
    return apiClient.get<ScenarioComparisonResponse>(
      `/projects/${projectId}/scenarios/compare/all`,
    )
  },
}
