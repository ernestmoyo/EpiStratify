<template>
  <div class="content-container">
    <div class="page-header">
      <div
        style="
          display: flex;
          justify-content: space-between;
          align-items: center;
        "
      >
        <div>
          <h1>Stratification</h1>
          <p>Configure thresholds and classify operational units by risk level</p>
        </div>
        <a-button type="primary" @click="showConfigModal = true">
          New Configuration
        </a-button>
      </div>
    </div>

    <!-- Configs -->
    <a-row :gutter="[16, 16]">
      <a-col
        v-for="config in configs"
        :key="config.id"
        :xs="24"
        :sm="12"
        :lg="8"
      >
        <a-card hoverable @click="selectConfig(config)">
          <template #title>{{ config.name }}</template>
          <template #extra>
            <a-tag :color="config.is_active ? 'green' : 'default'">
              {{ config.is_active ? 'Active' : 'Inactive' }}
            </a-tag>
          </template>
          <p>Metric: <strong>{{ config.metric.toUpperCase() }}</strong></p>
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item
              v-for="(range, level) in config.thresholds"
              :key="level"
              :label="String(level).replace('_', ' ')"
            >
              {{ range.min_value }} &ndash; {{ range.max_value }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
    </a-row>

    <!-- Results table -->
    <a-card
      v-if="selectedConfig && results.length > 0"
      :title="`Results: ${selectedConfig.name}`"
      style="margin-top: 24px"
    >
      <a-table
        :columns="resultColumns"
        :data-source="results"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'risk_level'">
            <a-tag :color="riskColor(record.risk_level)">
              {{ record.risk_level.replace('_', ' ') }}
            </a-tag>
          </template>
          <template v-if="column.key === 'eligible_interventions'">
            <a-tag
              v-for="int_code in record.eligible_interventions?.interventions || []"
              :key="int_code"
              size="small"
              style="margin: 2px"
            >
              {{ int_code }}
            </a-tag>
          </template>
        </template>
      </a-table>

      <!-- Summary -->
      <a-row :gutter="16" style="margin-top: 16px">
        <a-col :span="6">
          <a-statistic
            title="Total Units"
            :value="results.length"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="High Risk"
            :value="results.filter((r) => r.risk_level === 'high').length"
            value-style="color: #ff4d4f"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="Moderate Risk"
            :value="results.filter((r) => r.risk_level === 'moderate').length"
            value-style="color: #faad14"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="Low/Very Low"
            :value="
              results.filter(
                (r) =>
                  r.risk_level === 'low' || r.risk_level === 'very_low',
              ).length
            "
            value-style="color: #52c41a"
          />
        </a-col>
      </a-row>
    </a-card>

    <!-- Create config modal -->
    <a-modal
      v-model:open="showConfigModal"
      title="New Stratification Configuration"
      @ok="handleCreateConfig"
      :confirm-loading="creating"
      width="600px"
    >
      <a-form layout="vertical">
        <a-form-item label="Name" required>
          <a-input
            v-model:value="configForm.name"
            placeholder="e.g. PfPR Stratification 2025"
          />
        </a-form-item>
        <a-form-item label="Metric" required>
          <a-select v-model:value="configForm.metric">
            <a-select-option value="pfpr">PfPR (Prevalence)</a-select-option>
            <a-select-option value="incidence">
              Incidence (per 1000/year)
            </a-select-option>
            <a-select-option value="eir">
              EIR (Entomological Inoculation Rate)
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-divider>Thresholds</a-divider>

        <a-row :gutter="16" v-for="level in riskLevels" :key="level.key">
          <a-col :span="8">
            <strong>{{ level.label }}</strong>
          </a-col>
          <a-col :span="8">
            <a-input-number
              v-model:value="configForm.thresholds[level.key].min_value"
              placeholder="Min"
              :min="0"
              style="width: 100%"
            />
          </a-col>
          <a-col :span="8">
            <a-input-number
              v-model:value="configForm.thresholds[level.key].max_value"
              placeholder="Max"
              :min="0"
              style="width: 100%"
            />
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  stratificationApi,
  type StratificationConfigResponse,
  type StratificationResultResponse,
} from '@/api/stratification'

const props = defineProps<{ projectId: string }>()

const loading = ref(false)
const creating = ref(false)
const showConfigModal = ref(false)
const configs = ref<StratificationConfigResponse[]>([])
const selectedConfig = ref<StratificationConfigResponse | null>(null)
const results = ref<StratificationResultResponse[]>([])

const riskLevels = [
  { key: 'very_low', label: 'Very Low' },
  { key: 'low', label: 'Low' },
  { key: 'moderate', label: 'Moderate' },
  { key: 'high', label: 'High' },
]

const configForm = reactive({
  name: '',
  metric: 'pfpr',
  thresholds: {
    very_low: { min_value: 0, max_value: 1 },
    low: { min_value: 1, max_value: 5 },
    moderate: { min_value: 5, max_value: 25 },
    high: { min_value: 25, max_value: 100 },
  } as Record<string, { min_value: number; max_value: number }>,
})

const resultColumns = [
  { title: 'Admin Unit', dataIndex: 'admin_unit_name', key: 'admin_unit_name' },
  { title: 'Metric Value', dataIndex: 'metric_value', key: 'metric_value' },
  { title: 'Risk Level', key: 'risk_level' },
  { title: 'Population', dataIndex: 'population', key: 'population' },
  { title: 'Annual Cases', dataIndex: 'cases_annual', key: 'cases_annual' },
  { title: 'Eligible Interventions', key: 'eligible_interventions' },
]

onMounted(fetchConfigs)

async function fetchConfigs() {
  loading.value = true
  try {
    const response = await stratificationApi.listConfigs(props.projectId)
    configs.value = response.data
  } finally {
    loading.value = false
  }
}

async function selectConfig(config: StratificationConfigResponse) {
  selectedConfig.value = config
  try {
    const response = await stratificationApi.getResults(
      props.projectId,
      config.id,
    )
    results.value = response.data
  } catch {
    results.value = []
  }
}

async function handleCreateConfig() {
  creating.value = true
  try {
    await stratificationApi.createConfig(props.projectId, {
      name: configForm.name,
      metric: configForm.metric,
      thresholds: configForm.thresholds,
    })
    showConfigModal.value = false
    message.success('Configuration created')
    await fetchConfigs()
  } catch {
    message.error('Could not create configuration')
  } finally {
    creating.value = false
  }
}

function riskColor(level: string): string {
  const colors: Record<string, string> = {
    very_low: 'green',
    low: 'lime',
    moderate: 'orange',
    high: 'red',
  }
  return colors[level] || 'default'
}
</script>
