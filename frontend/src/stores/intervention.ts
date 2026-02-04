import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  interventionsApi,
  type InterventionDecisionTree,
  type InterventionPlanCreate,
  type InterventionPlanResponse,
  type InterventionRecommendation,
} from '@/api/interventions'

export const useInterventionStore = defineStore('intervention', () => {
  const decisionTrees = ref<InterventionDecisionTree[]>([])
  const recommendations = ref<InterventionRecommendation[]>([])
  const plans = ref<InterventionPlanResponse[]>([])
  const loading = ref(false)

  async function fetchDecisionTrees(projectId: string) {
    loading.value = true
    try {
      const response = await interventionsApi.getDecisionTrees(projectId)
      decisionTrees.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchRecommendations(
    projectId: string,
    riskLevel: string,
    context: Record<string, unknown> = {},
  ) {
    loading.value = true
    try {
      const response = await interventionsApi.getRecommendations(
        projectId,
        riskLevel,
        context,
      )
      recommendations.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchPlans(projectId: string) {
    loading.value = true
    try {
      const response = await interventionsApi.listPlans(projectId)
      plans.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function createPlan(projectId: string, data: InterventionPlanCreate) {
    const response = await interventionsApi.createPlan(projectId, data)
    plans.value.push(response.data)
    return response.data
  }

  async function deletePlan(projectId: string, planId: string) {
    await interventionsApi.deletePlan(projectId, planId)
    plans.value = plans.value.filter((p) => p.id !== planId)
  }

  return {
    decisionTrees,
    recommendations,
    plans,
    loading,
    fetchDecisionTrees,
    fetchRecommendations,
    fetchPlans,
    createPlan,
    deletePlan,
  }
})
