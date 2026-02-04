import apiClient from './client'

export interface UserCreate {
  email: string
  password: string
  full_name: string
  organization?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  full_name: string
  organization: string | null
  is_active: boolean
  created_at: string
}

export const authApi = {
  register(data: UserCreate) {
    return apiClient.post<UserResponse>('/auth/register', data)
  },

  login(data: LoginRequest) {
    return apiClient.post<TokenResponse>('/auth/login', data)
  },

  refresh(refreshToken: string) {
    return apiClient.post<TokenResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    })
  },

  getMe() {
    return apiClient.get<UserResponse>('/auth/me')
  },
}
