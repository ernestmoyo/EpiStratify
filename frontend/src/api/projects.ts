import apiClient from './client'

export interface ProjectCreate {
  name: string
  description?: string
  country: string
  admin_level?: number
  year: number
}

export interface ProjectResponse {
  id: string
  name: string
  description: string | null
  country: string
  admin_level: number
  year: number
  status: string
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: ProjectResponse[]
  total: number
}

export const projectsApi = {
  list() {
    return apiClient.get<ProjectListResponse>('/projects')
  },

  create(data: ProjectCreate) {
    return apiClient.post<ProjectResponse>('/projects', data)
  },

  get(projectId: string) {
    return apiClient.get<ProjectResponse>(`/projects/${projectId}`)
  },

  update(projectId: string, data: Partial<ProjectCreate>) {
    return apiClient.patch<ProjectResponse>(`/projects/${projectId}`, data)
  },

  archive(projectId: string) {
    return apiClient.delete(`/projects/${projectId}`)
  },
}
