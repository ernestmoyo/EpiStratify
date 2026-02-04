<template>
  <div class="content-container">
    <a-page-header
      :title="stepData?.label || 'Step'"
      :sub-title="stepData?.status?.replace('_', ' ')"
      @back="router.push(`/projects/${projectId}/workflow`)"
    />

    <a-spin :spinning="loading">
      <a-row :gutter="24">
        <a-col :span="16">
          <a-card title="Step Details">
            <a-form layout="vertical">
              <a-form-item label="Notes">
                <a-textarea
                  v-model:value="notes"
                  :rows="4"
                  placeholder="Add notes for this step..."
                />
              </a-form-item>

              <a-form-item label="Completion">
                <a-slider
                  v-model:value="completionPct"
                  :min="0"
                  :max="100"
                  :marks="{ 0: '0%', 25: '25%', 50: '50%', 75: '75%', 100: '100%' }"
                />
              </a-form-item>

              <a-form-item>
                <a-space>
                  <a-button type="primary" @click="handleSave" :loading="saving">
                    Save Progress
                  </a-button>
                  <a-button @click="handleValidate" :loading="validating">
                    Validate
                  </a-button>
                </a-space>
              </a-form-item>
            </a-form>
          </a-card>

          <!-- Validation results -->
          <a-card
            v-if="validationResult"
            title="Validation Results"
            style="margin-top: 16px"
          >
            <a-result
              :status="validationResult.is_valid ? 'success' : 'warning'"
              :title="
                validationResult.is_valid
                  ? 'Step is ready for completion'
                  : 'Issues found'
              "
            />

            <a-list
              v-if="validationResult.errors.length > 0"
              header="Errors"
              bordered
              size="small"
              :data-source="validationResult.errors"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-tag color="error">Error</a-tag>
                  {{ item }}
                </a-list-item>
              </template>
            </a-list>

            <a-list
              v-if="validationResult.warnings.length > 0"
              header="Warnings"
              bordered
              size="small"
              :data-source="validationResult.warnings"
              style="margin-top: 8px"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-tag color="warning">Warning</a-tag>
                  {{ item }}
                </a-list-item>
              </template>
            </a-list>
          </a-card>
        </a-col>

        <a-col :span="8">
          <a-card title="Step Information">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="Step">
                {{ stepData?.label }}
              </a-descriptions-item>
              <a-descriptions-item label="Status">
                <a-tag>{{ stepData?.status?.replace('_', ' ') }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="Progress">
                <a-progress :percent="completionPct" size="small" />
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore } from '@/stores/workflow'
import { message } from 'ant-design-vue'
import type { StepValidationResponse } from '@/api/workflow'

const props = defineProps<{
  projectId: string
  step: string
}>()

const router = useRouter()
const workflowStore = useWorkflowStore()

const loading = ref(true)
const saving = ref(false)
const validating = ref(false)
const notes = ref('')
const completionPct = ref(0)
const stepData = ref<{
  label: string
  status: string
  completion_percentage: number
  notes: string | null
} | null>(null)
const validationResult = ref<StepValidationResponse | null>(null)

onMounted(async () => {
  if (workflowStore.steps.length === 0) {
    await workflowStore.fetchWorkflow(props.projectId)
  }
  const step = workflowStore.steps.find((s) => s.step === props.step)
  if (step) {
    stepData.value = step
    notes.value = step.notes || ''
    completionPct.value = step.completion_percentage
  }
  loading.value = false
})

async function handleSave() {
  saving.value = true
  try {
    const updated = await workflowStore.updateStep(props.projectId, props.step, {
      notes: notes.value,
      completion_percentage: completionPct.value,
    })
    stepData.value = updated
    message.success('Progress saved')
  } catch {
    message.error('Could not save progress')
  } finally {
    saving.value = false
  }
}

async function handleValidate() {
  validating.value = true
  try {
    validationResult.value = await workflowStore.validateStep(
      props.projectId,
      props.step,
    )
  } catch {
    message.error('Validation failed')
  } finally {
    validating.value = false
  }
}
</script>
