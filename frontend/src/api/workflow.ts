import apiClient from './client'

export interface StepStatusResponse {
  step: string
  label: string
  status: string
  completion_percentage: number
  is_accessible: boolean
  blocking_prerequisites: string[]
  non_blocking_prerequisites: string[]
  notes: string | null
  completed_at: string | null
  data: Record<string, unknown> | null
  validation_errors: Record<string, unknown> | null
}

export interface WorkflowStateResponse {
  project_id: string
  steps: StepStatusResponse[]
  overall_progress: number
  current_step: string | null
}

export interface StepUpdateRequest {
  notes?: string
  completion_percentage?: number
  data?: Record<string, unknown>
}

export interface StepValidationResponse {
  step: string
  is_valid: boolean
  errors: string[]
  warnings: string[]
}

export const workflowApi = {
  getWorkflow(projectId: string) {
    return apiClient.get<WorkflowStateResponse>(
      `/projects/${projectId}/workflow`,
    )
  },

  getStep(projectId: string, step: string) {
    return apiClient.get<StepStatusResponse>(
      `/projects/${projectId}/workflow/steps/${step}`,
    )
  },

  updateStep(projectId: string, step: string, data: StepUpdateRequest) {
    return apiClient.patch<StepStatusResponse>(
      `/projects/${projectId}/workflow/steps/${step}`,
      data,
    )
  },

  validateStep(projectId: string, step: string) {
    return apiClient.post<StepValidationResponse>(
      `/projects/${projectId}/workflow/steps/${step}/validate`,
    )
  },

  completeStep(projectId: string, step: string) {
    return apiClient.post<StepStatusResponse>(
      `/projects/${projectId}/workflow/steps/${step}/complete`,
    )
  },

  reopenStep(projectId: string, step: string) {
    return apiClient.post<StepStatusResponse>(
      `/projects/${projectId}/workflow/steps/${step}/reopen`,
    )
  },
}
