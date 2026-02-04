<template>
  <div class="content-container">
    <div class="page-header">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h1>Impact Forecasting</h1>
          <p>Run projections and compare intervention impact across scenarios</p>
        </div>
        <a-button @click="handleCompare" :loading="forecastStore.loading">
          Compare Forecasts
        </a-button>
      </div>
    </div>

    <!-- Run Forecast panel -->
    <a-card title="Run New Forecast" style="margin-bottom: 24px">
      <a-form layout="inline">
        <a-form-item label="Scenario">
          <a-select v-model:value="selectedScenarioId" style="width: 250px">
            <a-select-option
              v-for="s in scenarioStore.scenarios"
              :key="s.id"
              :value="s.id"
            >
              {{ s.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Projection Years">
          <a-input-number v-model:value="projectionYears" :min="1" :max="20" />
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            @click="handleRunForecast"
            :loading="forecastStore.loading"
            :disabled="!selectedScenarioId"
          >
            Run Forecast
          </a-button>
        </a-form-item>
      </a-form>

      <a-divider>Baseline Data</a-divider>
      <a-row :gutter="16">
        <a-col :span="6">
          <a-form-item label="Baseline Cases (annual)">
            <a-input-number v-model:value="baseline.baseline_cases" :min="0" style="width: 100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Baseline Deaths (annual)">
            <a-input-number v-model:value="baseline.baseline_deaths" :min="0" style="width: 100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Prevalence (PfPR %)">
            <a-input-number v-model:value="baseline.baseline_prevalence" :min="0" :max="100" style="width: 100%" />
          </a-form-item>
        </a-col>
        <a-col :span="6">
          <a-form-item label="Population">
            <a-input-number v-model:value="baseline.population" :min="0" style="width: 100%" />
          </a-form-item>
        </a-col>
      </a-row>
    </a-card>

    <!-- Current forecast result -->
    <a-card
      v-if="forecastStore.currentForecast"
      title="Forecast Result"
      style="margin-bottom: 24px"
    >
      <a-row :gutter="16" style="margin-bottom: 24px">
        <a-col :span="4">
          <a-statistic title="Status" :value="forecastStore.currentForecast.status" />
        </a-col>
        <a-col :span="5">
          <a-statistic
            title="Cases Averted"
            :value="forecastStore.currentForecast.cases_averted || 0"
          />
        </a-col>
        <a-col :span="5">
          <a-statistic
            title="Deaths Averted"
            :value="forecastStore.currentForecast.deaths_averted || 0"
          />
        </a-col>
        <a-col :span="5">
          <a-statistic
            title="DALYs Averted"
            :value="forecastStore.currentForecast.dalys_averted || 0"
            :precision="1"
          />
        </a-col>
        <a-col :span="5">
          <a-statistic
            title="Cost/Case Averted"
            :value="forecastStore.currentForecast.cost_per_case_averted || 0"
            :precision="2"
            prefix="$"
          />
        </a-col>
      </a-row>

      <!-- Projections table -->
      <a-table
        v-if="projectionData.length > 0"
        :columns="projectionColumns"
        :data-source="projectionData"
        row-key="year"
        size="small"
      />

      <!-- Uncertainty -->
      <div v-if="forecastStore.currentForecast.uncertainty_bounds" style="margin-top: 16px">
        <h4>Uncertainty Bounds</h4>
        <a-descriptions :column="2" size="small" bordered>
          <a-descriptions-item label="Cases Averted (Lower)">
            {{ forecastStore.currentForecast.uncertainty_bounds.cases_averted?.lower?.toLocaleString() }}
          </a-descriptions-item>
          <a-descriptions-item label="Cases Averted (Upper)">
            {{ forecastStore.currentForecast.uncertainty_bounds.cases_averted?.upper?.toLocaleString() }}
          </a-descriptions-item>
          <a-descriptions-item label="Deaths Averted (Lower)">
            {{ forecastStore.currentForecast.uncertainty_bounds.deaths_averted?.lower?.toLocaleString() }}
          </a-descriptions-item>
          <a-descriptions-item label="Deaths Averted (Upper)">
            {{ forecastStore.currentForecast.uncertainty_bounds.deaths_averted?.upper?.toLocaleString() }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-card>

    <!-- Comparison -->
    <a-card
      v-if="forecastStore.comparison"
      title="Forecast Comparison"
    >
      <a-table
        :columns="comparisonColumns"
        :data-source="forecastStore.comparison.scenarios"
        row-key="scenario_id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'scenario_name'">
            <strong>{{ record.scenario_name }}</strong>
            <a-tag
              v-if="record.scenario_id === forecastStore.comparison?.best_by_cases_averted"
              color="green"
              style="margin-left: 8px"
            >
              Best Impact
            </a-tag>
            <a-tag
              v-if="record.scenario_id === forecastStore.comparison?.best_by_cost_effectiveness"
              color="blue"
              style="margin-left: 4px"
            >
              Best Value
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useForecastStore } from '@/stores/forecast'
import { useScenarioStore } from '@/stores/scenario'

const props = defineProps<{ projectId: string }>()
const forecastStore = useForecastStore()
const scenarioStore = useScenarioStore()

const selectedScenarioId = ref<string | null>(null)
const projectionYears = ref(5)
const baseline = reactive({
  baseline_cases: 100000,
  baseline_deaths: 500,
  baseline_prevalence: 15.0,
  population: 1000000,
})

const projectionColumns = [
  { title: 'Year', dataIndex: 'year', key: 'year' },
  { title: 'Projected Cases', dataIndex: 'cases', key: 'cases' },
  { title: 'Projected Deaths', dataIndex: 'deaths', key: 'deaths' },
  { title: 'Prevalence (%)', dataIndex: 'prevalence', key: 'prevalence' },
]

const comparisonColumns = [
  { title: 'Scenario', key: 'scenario_name' },
  { title: 'Baseline Cases', dataIndex: 'baseline_cases', key: 'baseline_cases' },
  { title: 'Final Year Cases', dataIndex: 'projected_cases_final_year', key: 'final_cases' },
  { title: 'Cases Averted', dataIndex: 'total_cases_averted', key: 'cases_averted' },
  { title: 'Deaths Averted', dataIndex: 'total_deaths_averted', key: 'deaths_averted' },
]

const projectionData = computed(() => {
  const fc = forecastStore.currentForecast
  if (!fc?.projected_cases) return []

  return Object.keys(fc.projected_cases)
    .sort()
    .map((year) => ({
      year,
      cases: fc.projected_cases?.[year]?.toLocaleString() || '-',
      deaths: fc.projected_deaths?.[year]?.toLocaleString() || '-',
      prevalence: fc.projected_prevalence?.[year] || '-',
    }))
})

onMounted(() => {
  scenarioStore.fetchScenarios(props.projectId)
})

async function handleRunForecast() {
  if (!selectedScenarioId.value) return

  try {
    await forecastStore.runForecast(
      props.projectId,
      selectedScenarioId.value,
      { model_type: 'simple', projection_years: projectionYears.value },
      baseline,
    )
    message.success('Forecast completed')
  } catch {
    message.error('Failed to run forecast')
  }
}

async function handleCompare() {
  try {
    await forecastStore.compareForecasts(props.projectId)
  } catch {
    message.error('Failed to compare forecasts')
  }
}
</script>
