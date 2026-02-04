import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  forecastsApi,
  type ForecastRequest,
  type ForecastResultResponse,
  type ForecastComparisonResponse,
  type BaselineData,
} from '@/api/forecasts'

export const useForecastStore = defineStore('forecast', () => {
  const forecasts = ref<ForecastResultResponse[]>([])
  const currentForecast = ref<ForecastResultResponse | null>(null)
  const comparison = ref<ForecastComparisonResponse | null>(null)
  const loading = ref(false)

  async function runForecast(
    projectId: string,
    scenarioId: string,
    request: ForecastRequest,
    baselineData?: BaselineData,
  ) {
    loading.value = true
    try {
      const response = await forecastsApi.run(
        projectId,
        scenarioId,
        request,
        baselineData,
      )
      currentForecast.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchForecasts(projectId: string, scenarioId: string) {
    loading.value = true
    try {
      const response = await forecastsApi.list(projectId, scenarioId)
      forecasts.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchForecast(projectId: string, forecastId: string) {
    loading.value = true
    try {
      const response = await forecastsApi.get(projectId, forecastId)
      currentForecast.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function compareForecasts(projectId: string) {
    loading.value = true
    try {
      const response = await forecastsApi.compare(projectId)
      comparison.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  return {
    forecasts,
    currentForecast,
    comparison,
    loading,
    runForecast,
    fetchForecasts,
    fetchForecast,
    compareForecasts,
  }
})
