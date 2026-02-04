<template>
  <div class="content-container">
    <div class="page-header">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h1>Intervention Tailoring</h1>
          <p>Configure interventions based on WHO decision trees and local context</p>
        </div>
      </div>
    </div>

    <!-- Risk level selector -->
    <a-card title="Context" style="margin-bottom: 16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-form-item label="Risk Level">
            <a-select v-model:value="riskLevel" @change="fetchRecommendations">
              <a-select-option value="very_low">Very Low</a-select-option>
              <a-select-option value="low">Low</a-select-option>
              <a-select-option value="moderate">Moderate</a-select-option>
              <a-select-option value="high">High</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Seasonality">
            <a-select v-model:value="context.seasonality" @change="fetchRecommendations">
              <a-select-option value="perennial">Perennial</a-select-option>
              <a-select-option value="seasonal">Seasonal</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Setting">
            <a-select v-model:value="context.setting" @change="fetchRecommendations">
              <a-select-option value="rural">Rural</a-select-option>
              <a-select-option value="urban">Urban</a-select-option>
              <a-select-option value="peri_urban">Peri-urban</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Pyrethroid Resistance (%)">
            <a-input-number
              v-model:value="context.pyrethroid_resistance_pct"
              :min="0"
              :max="100"
              style="width: 100%"
              @change="fetchRecommendations"
            />
          </a-form-item>
        </a-col>
      </a-row>
    </a-card>

    <!-- Recommendations grid -->
    <a-spin :spinning="interventionStore.loading">
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="rec in interventionStore.recommendations"
          :key="rec.intervention_code"
          :xs="24"
          :sm="12"
          :lg="8"
          :xl="6"
        >
          <a-card
            :class="{ 'card-eligible': rec.is_eligible, 'card-ineligible': !rec.is_eligible }"
            hoverable
            @click="rec.is_eligible && openTailoringDrawer(rec)"
          >
            <template #title>
              <span>{{ rec.intervention_name }}</span>
            </template>
            <template #extra>
              <a-tag :color="rec.is_eligible ? 'green' : 'red'">
                {{ rec.is_eligible ? 'Eligible' : 'Ineligible' }}
              </a-tag>
            </template>

            <template v-if="rec.is_eligible">
              <p style="color: #666; margin-bottom: 8px">
                {{ rec.tailoring_questions?.length || 0 }} tailoring questions
              </p>
              <div v-if="rec.default_recommendations">
                <a-tag
                  v-for="(value, key) in rec.default_recommendations"
                  :key="key"
                  style="margin-bottom: 4px"
                >
                  {{ formatKey(String(key)) }}: {{ value }}
                </a-tag>
              </div>
            </template>
            <template v-else>
              <p
                v-for="reason in rec.ineligibility_reasons"
                :key="reason"
                style="color: #ff4d4f; font-size: 12px"
              >
                {{ reason }}
              </p>
            </template>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- Intervention Plans -->
    <a-card title="Saved Intervention Plans" style="margin-top: 24px">
      <template #extra>
        <a-button type="primary" size="small" @click="showPlanModal = true">
          Add Plan
        </a-button>
      </template>
      <a-table
        :columns="planColumns"
        :data-source="interventionStore.plans"
        row-key="id"
        size="small"
        :loading="interventionStore.loading"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-popconfirm title="Delete this plan?" @confirm="handleDeletePlan(record.id)">
              <a-button type="link" danger size="small">Delete</a-button>
            </a-popconfirm>
          </template>
          <template v-if="column.key === 'intervention_code'">
            <a-tag color="blue">{{ record.intervention_code.toUpperCase() }}</a-tag>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Tailoring Drawer -->
    <a-drawer
      v-model:open="showDrawer"
      :title="selectedRec?.intervention_name"
      width="500"
      placement="right"
    >
      <template v-if="selectedRec">
        <a-form layout="vertical">
          <a-form-item
            v-for="q in selectedRec.tailoring_questions"
            :key="q.id"
            :label="q.question"
            :help="q.help_text || undefined"
          >
            <a-select
              v-if="q.question_type === 'select' && q.options"
              v-model:value="tailoringAnswers[q.id]"
            >
              <a-select-option v-for="opt in q.options" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </a-select-option>
            </a-select>
            <a-input-number
              v-else-if="q.question_type === 'numeric'"
              v-model:value="tailoringAnswers[q.id]"
              :min="q.min_value ?? undefined"
              :max="q.max_value ?? undefined"
              style="width: 100%"
            />
            <a-switch
              v-else-if="q.question_type === 'boolean'"
              v-model:checked="tailoringAnswers[q.id]"
            />
          </a-form-item>
        </a-form>
      </template>
    </a-drawer>

    <!-- Plan Creation Modal -->
    <a-modal
      v-model:open="showPlanModal"
      title="Add Intervention Plan"
      @ok="handleCreatePlan"
      :confirm-loading="creatingPlan"
    >
      <a-form layout="vertical">
        <a-form-item label="Admin Unit Name" required>
          <a-input v-model:value="planForm.admin_unit_name" />
        </a-form-item>
        <a-form-item label="Admin Unit Code">
          <a-input v-model:value="planForm.admin_unit_code" />
        </a-form-item>
        <a-form-item label="Intervention" required>
          <a-select v-model:value="planForm.intervention_code">
            <a-select-option value="itn">ITN</a-select-option>
            <a-select-option value="irs">IRS</a-select-option>
            <a-select-option value="smc">SMC</a-select-option>
            <a-select-option value="iptp">IPTp</a-select-option>
            <a-select-option value="vaccine">Vaccine</a-select-option>
            <a-select-option value="cm">Case Management</a-select-option>
            <a-select-option value="pmc">PMC</a-select-option>
            <a-select-option value="lsm">LSM</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Coverage Target (%)">
          <a-input-number
            v-model:value="planForm.coverage_target"
            :min="0"
            :max="100"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="Target Population">
          <a-input-number
            v-model:value="planForm.target_population"
            :min="0"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="Notes">
          <a-textarea v-model:value="planForm.notes" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useInterventionStore } from '@/stores/intervention'
import type { InterventionRecommendation } from '@/api/interventions'

const props = defineProps<{ projectId: string }>()
const interventionStore = useInterventionStore()

const riskLevel = ref('moderate')
const context = reactive<Record<string, unknown>>({
  seasonality: 'perennial',
  setting: 'rural',
  pyrethroid_resistance_pct: 30,
})

const showDrawer = ref(false)
const selectedRec = ref<InterventionRecommendation | null>(null)
const tailoringAnswers = reactive<Record<string, unknown>>({})

const showPlanModal = ref(false)
const creatingPlan = ref(false)
const planForm = reactive({
  admin_unit_name: '',
  admin_unit_code: '',
  intervention_code: 'itn',
  coverage_target: 80,
  target_population: 0,
  notes: '',
})

const planColumns = [
  { title: 'Admin Unit', dataIndex: 'admin_unit_name', key: 'admin_unit_name' },
  { title: 'Intervention', dataIndex: 'intervention_code', key: 'intervention_code' },
  { title: 'Coverage %', dataIndex: 'coverage_target', key: 'coverage_target' },
  { title: 'Target Pop.', dataIndex: 'target_population', key: 'target_population' },
  { title: 'Action', key: 'action', width: 100 },
]

onMounted(async () => {
  await Promise.all([
    fetchRecommendations(),
    interventionStore.fetchPlans(props.projectId),
  ])
})

async function fetchRecommendations() {
  await interventionStore.fetchRecommendations(props.projectId, riskLevel.value, context)
}

function openTailoringDrawer(rec: InterventionRecommendation) {
  selectedRec.value = rec
  // Pre-fill defaults
  if (rec.default_recommendations) {
    Object.assign(tailoringAnswers, rec.default_recommendations)
  }
  showDrawer.value = true
}

async function handleCreatePlan() {
  creatingPlan.value = true
  try {
    await interventionStore.createPlan(props.projectId, {
      admin_unit_name: planForm.admin_unit_name,
      admin_unit_code: planForm.admin_unit_code || undefined,
      intervention_code: planForm.intervention_code,
      coverage_target: planForm.coverage_target,
      target_population: planForm.target_population || undefined,
      notes: planForm.notes || undefined,
    })
    showPlanModal.value = false
    message.success('Plan created')
  } catch {
    message.error('Failed to create plan')
  } finally {
    creatingPlan.value = false
  }
}

async function handleDeletePlan(planId: string) {
  try {
    await interventionStore.deletePlan(props.projectId, planId)
    message.success('Plan deleted')
  } catch {
    message.error('Failed to delete plan')
  }
}

function formatKey(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
</script>

<style scoped>
.card-eligible {
  border-left: 3px solid #52c41a;
}
.card-ineligible {
  border-left: 3px solid #ff4d4f;
  opacity: 0.7;
}
</style>
