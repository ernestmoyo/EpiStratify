import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type UserResponse } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserResponse | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const userName = computed(() => user.value?.full_name || '')

  async function login(email: string, password: string) {
    const response = await authApi.login({ email, password })
    accessToken.value = response.data.access_token
    localStorage.setItem('access_token', response.data.access_token)
    localStorage.setItem('refresh_token', response.data.refresh_token)
    await fetchUser()
  }

  async function register(data: {
    email: string
    password: string
    full_name: string
    organization?: string
  }) {
    await authApi.register(data)
  }

  async function fetchUser() {
    try {
      const response = await authApi.getMe()
      user.value = response.data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    accessToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    userName,
    login,
    register,
    fetchUser,
    logout,
  }
})
