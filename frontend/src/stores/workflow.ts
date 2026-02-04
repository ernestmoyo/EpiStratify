import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  workflowApi,
  type WorkflowStateResponse,
  type StepStatusResponse,
  type StepUpdateRequest,
} from '@/api/workflow'

export const useWorkflowStore = defineStore('workflow', () => {
  const workflowState = ref<WorkflowStateResponse | null>(null)
  const loading = ref(false)

  const steps = computed(() => workflowState.value?.steps || [])
  const overallProgress = computed(() => workflowState.value?.overall_progress || 0)
  const currentStep = computed(() => workflowState.value?.current_step || null)

  async function fetchWorkflow(projectId: string) {
    loading.value = true
    try {
      const response = await workflowApi.getWorkflow(projectId)
      workflowState.value = response.data
    } finally {
      loading.value = false
    }
  }

  async function updateStep(
    projectId: string,
    step: string,
    data: StepUpdateRequest,
  ) {
    const response = await workflowApi.updateStep(projectId, step, data)
    updateStepInState(response.data)
    return response.data
  }

  async function validateStep(projectId: string, step: string) {
    const response = await workflowApi.validateStep(projectId, step)
    return response.data
  }

  async function completeStep(projectId: string, step: string) {
    const response = await workflowApi.completeStep(projectId, step)
    // Refresh full workflow to get updated accessibility flags
    await fetchWorkflow(projectId)
    return response.data
  }

  async function reopenStep(projectId: string, step: string) {
    const response = await workflowApi.reopenStep(projectId, step)
    await fetchWorkflow(projectId)
    return response.data
  }

  function updateStepInState(updatedStep: StepStatusResponse) {
    if (!workflowState.value) return
    const index = workflowState.value.steps.findIndex(
      (s) => s.step === updatedStep.step,
    )
    if (index !== -1) {
      workflowState.value.steps[index] = updatedStep
    }
  }

  return {
    workflowState,
    loading,
    steps,
    overallProgress,
    currentStep,
    fetchWorkflow,
    updateStep,
    validateStep,
    completeStep,
    reopenStep,
  }
})
