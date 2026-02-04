<template>
  <div class="content-container">
    <div class="page-header">
      <h1>Workflow</h1>
      <p>10-step SNT planning process</p>
    </div>

    <a-spin :spinning="workflowStore.loading">
      <a-row :gutter="24">
        <a-col :span="8">
          <WorkflowStepper
            :steps="workflowStore.steps"
            :overall-progress="workflowStore.overallProgress"
            :current-step="workflowStore.currentStep"
            @select-step="navigateToStep"
          />
        </a-col>

        <a-col :span="16">
          <a-card v-if="selectedStep" :title="selectedStep.label">
            <template #extra>
              <a-tag :color="statusTagColor(selectedStep.status)">
                {{ selectedStep.status.replace('_', ' ') }}
              </a-tag>
            </template>

            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item label="Status">
                {{ selectedStep.status.replace('_', ' ') }}
              </a-descriptions-item>
              <a-descriptions-item label="Progress">
                <a-progress
                  :percent="selectedStep.completion_percentage"
                  size="small"
                />
              </a-descriptions-item>
              <a-descriptions-item label="Accessible">
                <a-tag :color="selectedStep.is_accessible ? 'green' : 'red'">
                  {{ selectedStep.is_accessible ? 'Yes' : 'No' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="Completed">
                {{ selectedStep.completed_at || 'Not yet' }}
              </a-descriptions-item>
            </a-descriptions>

            <div
              v-if="selectedStep.blocking_prerequisites.length > 0"
              style="margin-top: 16px"
            >
              <a-alert
                type="warning"
                :message="`Requires completion of: ${selectedStep.blocking_prerequisites.join(', ')}`"
                show-icon
              />
            </div>

            <div style="margin-top: 16px">
              <a-space>
                <a-button
                  v-if="
                    selectedStep.is_accessible &&
                    selectedStep.status !== 'completed'
                  "
                  type="primary"
                  @click="
                    router.push(
                      `/projects/${projectId}/workflow/${selectedStep.step}`,
                    )
                  "
                >
                  Open Step
                </a-button>
                <a-button
                  v-if="
                    selectedStep.status === 'in_progress' &&
                    selectedStep.is_accessible
                  "
                  @click="handleComplete(selectedStep.step)"
                  :loading="completing"
                >
                  Mark Complete
                </a-button>
                <a-button
                  v-if="selectedStep.status === 'completed'"
                  @click="handleReopen(selectedStep.step)"
                >
                  Reopen
                </a-button>
              </a-space>
            </div>
          </a-card>

          <a-empty v-else description="Select a step from the workflow" />
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { useProjectStore } from '@/stores/project'
import WorkflowStepper from '@/components/workflow/WorkflowStepper.vue'
import { message } from 'ant-design-vue'

const props = defineProps<{ projectId: string }>()

const router = useRouter()
const workflowStore = useWorkflowStore()
const projectStore = useProjectStore()

const selectedStepKey = ref<string | null>(null)
const completing = ref(false)

const selectedStep = computed(() => {
  if (!selectedStepKey.value) return null
  return workflowStore.steps.find((s) => s.step === selectedStepKey.value) || null
})

onMounted(async () => {
  await workflowStore.fetchWorkflow(props.projectId)
  if (!projectStore.currentProject) {
    await projectStore.fetchProject(props.projectId)
  }
  if (workflowStore.currentStep) {
    selectedStepKey.value = workflowStore.currentStep
  } else if (workflowStore.steps.length > 0) {
    selectedStepKey.value = workflowStore.steps[0].step
  }
})

function navigateToStep(step: string) {
  selectedStepKey.value = step
}

function statusTagColor(status: string) {
  const colors: Record<string, string> = {
    not_started: 'default',
    in_progress: 'processing',
    completed: 'success',
    blocked: 'error',
  }
  return colors[status] || 'default'
}

async function handleComplete(step: string) {
  completing.value = true
  try {
    await workflowStore.completeStep(props.projectId, step)
    message.success('Step completed')
  } catch (err: unknown) {
    const axiosError = err as { response?: { data?: { detail?: string } } }
    message.error(axiosError.response?.data?.detail || 'Could not complete step')
  } finally {
    completing.value = false
  }
}

async function handleReopen(step: string) {
  try {
    await workflowStore.reopenStep(props.projectId, step)
    message.info('Step reopened')
  } catch {
    message.error('Could not reopen step')
  }
}
</script>
