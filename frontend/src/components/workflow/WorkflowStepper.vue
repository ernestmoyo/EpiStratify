<template>
  <a-card title="SNT Workflow Progress" style="margin-bottom: 24px">
    <a-progress
      :percent="Math.round(overallProgress)"
      :status="overallProgress === 100 ? 'success' : 'active'"
      style="margin-bottom: 16px"
    />

    <a-steps
      :current="currentStepIndex"
      direction="vertical"
      size="small"
    >
      <a-step
        v-for="step in steps"
        :key="step.step"
        :title="step.label"
        :status="stepDisplayStatus(step)"
        :description="stepDescription(step)"
        style="cursor: pointer"
        @click="$emit('selectStep', step.step)"
      />
    </a-steps>
  </a-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StepStatusResponse } from '@/api/workflow'

const props = defineProps<{
  steps: StepStatusResponse[]
  overallProgress: number
  currentStep: string | null
}>()

defineEmits<{
  selectStep: [step: string]
}>()

const currentStepIndex = computed(() => {
  if (!props.currentStep) return 0
  return props.steps.findIndex((s) => s.step === props.currentStep)
})

function stepDisplayStatus(
  step: StepStatusResponse,
): 'wait' | 'process' | 'finish' | 'error' {
  if (step.status === 'completed') return 'finish'
  if (step.status === 'in_progress') return 'process'
  if (step.status === 'blocked') return 'error'
  if (!step.is_accessible) return 'wait'
  return 'wait'
}

function stepDescription(step: StepStatusResponse): string {
  if (step.status === 'completed') return 'Completed'
  if (step.status === 'in_progress')
    return `${step.completion_percentage}% complete`
  if (!step.is_accessible && step.blocking_prerequisites.length > 0)
    return `Requires: ${step.blocking_prerequisites.join(', ')}`
  return 'Not started'
}
</script>
