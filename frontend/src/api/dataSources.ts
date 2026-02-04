import apiClient from './client'

export interface DataSourceResponse {
  id: string
  name: string
  description: string | null
  source_type: string
  file_format: string | null
  file_size_bytes: number | null
  record_count: number | null
  year_start: number | null
  year_end: number | null
  quality_score: number | null
  created_at: string
}

export interface QualityCheckResponse {
  id: string
  check_type: string
  status: string
  score: number | null
  issues_found: number
  message: string | null
  details: Record<string, unknown> | null
  created_at: string
}

export interface QualityReportResponse {
  data_source_id: string
  data_source_name: string
  overall_score: number | null
  checks: QualityCheckResponse[]
  recommendations: string[]
}

export const dataSourcesApi = {
  list(projectId: string) {
    return apiClient.get<DataSourceResponse[]>(
      `/projects/${projectId}/data-sources`,
    )
  },

  upload(projectId: string, formData: FormData) {
    return apiClient.post<DataSourceResponse>(
      `/projects/${projectId}/data-sources`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  get(projectId: string, dataSourceId: string) {
    return apiClient.get<DataSourceResponse>(
      `/projects/${projectId}/data-sources/${dataSourceId}`,
    )
  },

  delete(projectId: string, dataSourceId: string) {
    return apiClient.delete(
      `/projects/${projectId}/data-sources/${dataSourceId}`,
    )
  },

  runQualityCheck(projectId: string, dataSourceId: string) {
    return apiClient.post<QualityReportResponse>(
      `/projects/${projectId}/data-sources/${dataSourceId}/quality-check`,
    )
  },

  getQualityReport(projectId: string, dataSourceId: string) {
    return apiClient.get<QualityReportResponse>(
      `/projects/${projectId}/data-sources/${dataSourceId}/quality-report`,
    )
  },
}
