import apiClient from './client'

export interface ForecastRequest {
  model_type?: string
  parameters?: Record<string, unknown>
  projection_years?: number
}

export interface ForecastResultResponse {
  id: string
  scenario_id: string
  status: string
  model_type: string | null
  projected_cases: Record<string, number> | null
  projected_deaths: Record<string, number> | null
  projected_prevalence: Record<string, number> | null
  cases_averted: number | null
  deaths_averted: number | null
  dalys_averted: number | null
  cost_per_case_averted: number | null
  cost_per_death_averted: number | null
  cost_per_daly_averted: number | null
  uncertainty_bounds: Record<string, unknown> | null
  created_at: string
}

export interface ForecastSummaryResponse {
  scenario_id: string
  scenario_name: string
  baseline_cases: number
  baseline_deaths: number
  projected_cases_final_year: number | null
  projected_deaths_final_year: number | null
  total_cases_averted: number | null
  total_deaths_averted: number | null
  cost_effectiveness: Record<string, number | null>
}

export interface ForecastComparisonResponse {
  scenarios: ForecastSummaryResponse[]
  best_by_cases_averted: string | null
  best_by_cost_effectiveness: string | null
}

export interface BaselineData {
  baseline_cases: number
  baseline_deaths: number
  baseline_prevalence: number
  population: number
}

export const forecastsApi = {
  run(
    projectId: string,
    scenarioId: string,
    request: ForecastRequest,
    baselineData?: BaselineData,
  ) {
    return apiClient.post<ForecastResultResponse>(
      `/projects/${projectId}/forecasts/scenarios/${scenarioId}/run`,
      { ...request, baseline_data: baselineData },
    )
  },

  list(projectId: string, scenarioId: string) {
    return apiClient.get<ForecastResultResponse[]>(
      `/projects/${projectId}/forecasts/scenarios/${scenarioId}/forecasts`,
    )
  },

  get(projectId: string, forecastId: string) {
    return apiClient.get<ForecastResultResponse>(
      `/projects/${projectId}/forecasts/forecasts/${forecastId}`,
    )
  },

  compare(projectId: string) {
    return apiClient.get<ForecastComparisonResponse>(
      `/projects/${projectId}/forecasts/compare`,
    )
  },
}
