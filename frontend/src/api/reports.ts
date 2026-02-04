import apiClient from './client'

export interface ReportGenerateRequest {
  report_type?: string
  format?: string
  title?: string
  parameters?: Record<string, unknown>
}

export interface ReportRecordResponse {
  id: string
  title: string
  report_type: string
  format: string
  file_size_bytes: number | null
  created_at: string
}

export interface ReportListResponse {
  items: ReportRecordResponse[]
  total: number
}

export const reportsApi = {
  generate(projectId: string, request: ReportGenerateRequest) {
    return apiClient.post<ReportRecordResponse>(
      `/projects/${projectId}/reports`,
      request,
    )
  },

  list(projectId: string) {
    return apiClient.get<ReportListResponse>(
      `/projects/${projectId}/reports`,
    )
  },

  get(projectId: string, reportId: string) {
    return apiClient.get<ReportRecordResponse>(
      `/projects/${projectId}/reports/${reportId}`,
    )
  },

  download(projectId: string, reportId: string) {
    return apiClient.get(
      `/projects/${projectId}/reports/${reportId}/download`,
      { responseType: 'blob' },
    )
  },

  delete(projectId: string, reportId: string) {
    return apiClient.delete(`/projects/${projectId}/reports/${reportId}`)
  },
}
