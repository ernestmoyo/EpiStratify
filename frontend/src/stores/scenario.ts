import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  scenariosApi,
  type ScenarioCreate,
  type ScenarioResponse,
  type ScenarioDetailResponse,
  type ScenarioCostSummary,
  type ScenarioComparisonResponse,
  type PopulationDataItem,
} from '@/api/scenarios'

export const useScenarioStore = defineStore('scenario', () => {
  const scenarios = ref<ScenarioResponse[]>([])
  const currentScenario = ref<ScenarioDetailResponse | null>(null)
  const costSummary = ref<ScenarioCostSummary | null>(null)
  const comparison = ref<ScenarioComparisonResponse | null>(null)
  const loading = ref(false)

  const selectedScenario = computed(() =>
    scenarios.value.find((s) => s.is_selected) || null,
  )

  async function fetchScenarios(projectId: string) {
    loading.value = true
    try {
      const response = await scenariosApi.list(projectId)
      scenarios.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function createScenario(projectId: string, data: ScenarioCreate) {
    const response = await scenariosApi.create(projectId, data)
    scenarios.value.unshift(response.data)
    return response.data
  }

  async function fetchScenario(projectId: string, scenarioId: string) {
    loading.value = true
    try {
      const response = await scenariosApi.get(projectId, scenarioId)
      currentScenario.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function deleteScenario(projectId: string, scenarioId: string) {
    await scenariosApi.delete(projectId, scenarioId)
    scenarios.value = scenarios.value.filter((s) => s.id !== scenarioId)
    if (currentScenario.value?.id === scenarioId) {
      currentScenario.value = null
    }
  }

  async function calculateCost(
    projectId: string,
    scenarioId: string,
    populationData: PopulationDataItem[],
    projectYears = 5,
  ) {
    loading.value = true
    try {
      const response = await scenariosApi.calculateCost(
        projectId,
        scenarioId,
        populationData,
        undefined,
        projectYears,
      )
      costSummary.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function compareScenarios(projectId: string) {
    loading.value = true
    try {
      const response = await scenariosApi.compare(projectId)
      comparison.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  return {
    scenarios,
    currentScenario,
    costSummary,
    comparison,
    loading,
    selectedScenario,
    fetchScenarios,
    createScenario,
    fetchScenario,
    deleteScenario,
    calculateCost,
    compareScenarios,
  }
})
