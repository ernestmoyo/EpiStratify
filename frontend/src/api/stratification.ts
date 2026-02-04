import apiClient from './client'

export interface ThresholdRange {
  min_value: number
  max_value: number
}

export interface StratificationConfigCreate {
  name: string
  metric: string
  thresholds: Record<string, ThresholdRange>
}

export interface StratificationConfigResponse {
  id: string
  name: string
  metric: string
  thresholds: Record<string, ThresholdRange>
  is_active: boolean
  created_at: string
}

export interface StratificationResultResponse {
  id: string
  admin_unit_name: string
  admin_unit_code: string | null
  metric_value: number
  risk_level: string
  eligible_interventions: Record<string, unknown> | null
  population: number | null
  cases_annual: number | null
  deaths_annual: number | null
}

export interface GeoJSONFeatureCollection {
  type: string
  features: Array<{
    type: string
    geometry: unknown
    properties: Record<string, unknown>
  }>
}

export const stratificationApi = {
  listConfigs(projectId: string) {
    return apiClient.get<StratificationConfigResponse[]>(
      `/projects/${projectId}/stratification/configs`,
    )
  },

  createConfig(projectId: string, data: StratificationConfigCreate) {
    return apiClient.post<StratificationConfigResponse>(
      `/projects/${projectId}/stratification/configs`,
      data,
    )
  },

  updateConfig(
    projectId: string,
    configId: string,
    data: Partial<StratificationConfigCreate>,
  ) {
    return apiClient.patch<StratificationConfigResponse>(
      `/projects/${projectId}/stratification/configs/${configId}`,
      data,
    )
  },

  calculate(
    projectId: string,
    configId: string,
    data: Array<Record<string, unknown>>,
  ) {
    return apiClient.post<StratificationResultResponse[]>(
      `/projects/${projectId}/stratification/configs/${configId}/calculate`,
      data,
    )
  },

  getResults(projectId: string, configId: string) {
    return apiClient.get<StratificationResultResponse[]>(
      `/projects/${projectId}/stratification/configs/${configId}/results`,
    )
  },

  getGeoJSON(projectId: string, configId: string) {
    return apiClient.get<GeoJSONFeatureCollection>(
      `/projects/${projectId}/stratification/configs/${configId}/geojson`,
    )
  },

  getSummary(projectId: string, configId: string) {
    return apiClient.get(
      `/projects/${projectId}/stratification/configs/${configId}/summary`,
    )
  },
}
