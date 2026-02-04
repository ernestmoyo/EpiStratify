<template>
  <div class="content-container">
    <div class="page-header">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h1>Budget Scenarios</h1>
          <p>Create and compare intervention scenario packages with cost estimation</p>
        </div>
        <a-space>
          <a-button @click="handleCompare" :loading="scenarioStore.loading">
            Compare All
          </a-button>
          <a-button type="primary" @click="showCreateModal = true">
            New Scenario
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- Scenario cards -->
    <a-spin :spinning="scenarioStore.loading">
      <a-row :gutter="[16, 16]">
        <a-col
          v-for="scenario in scenarioStore.scenarios"
          :key="scenario.id"
          :xs="24"
          :sm="12"
          :lg="8"
        >
          <a-card hoverable @click="selectScenario(scenario.id)">
            <template #title>
              <a-space>
                {{ scenario.name }}
                <a-tag v-if="scenario.is_selected" color="blue">Selected</a-tag>
              </a-space>
            </template>
            <template #extra>
              <a-tag>{{ scenario.scenario_type.replace('_', ' ') }}</a-tag>
            </template>

            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="Total Cost">
                {{ scenario.total_cost ? `$${formatNumber(scenario.total_cost)}` : 'Not costed' }}
              </a-descriptions-item>
              <a-descriptions-item label="Population">
                {{ scenario.population_covered ? formatNumber(scenario.population_covered) : '-' }}
              </a-descriptions-item>
              <a-descriptions-item label="Cases Averted">
                {{ scenario.estimated_cases_averted ? formatNumber(scenario.estimated_cases_averted) : '-' }}
              </a-descriptions-item>
            </a-descriptions>

            <template #actions>
              <a-popconfirm
                title="Delete this scenario?"
                @confirm.stop="handleDelete(scenario.id)"
              >
                <a style="color: #ff4d4f" @click.stop>Delete</a>
              </a-popconfirm>
            </template>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- Scenario detail -->
    <a-card
      v-if="scenarioStore.currentScenario"
      :title="`Detail: ${scenarioStore.currentScenario.name}`"
      style="margin-top: 24px"
    >
      <a-tabs>
        <a-tab-pane key="interventions" tab="Interventions">
          <a-table
            :columns="interventionColumns"
            :data-source="interventionRows"
            row-key="key"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'interventions'">
                <a-tag
                  v-for="code in record.interventions"
                  :key="code"
                  color="blue"
                  style="margin-bottom: 4px"
                >
                  {{ code.toUpperCase() }}
                </a-tag>
              </template>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="costs" tab="Cost Breakdown">
          <a-table
            :columns="costColumns"
            :data-source="scenarioStore.currentScenario.cost_items"
            row-key="id"
            size="small"
          />
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- Comparison -->
    <a-card
      v-if="scenarioStore.comparison"
      title="Scenario Comparison"
      style="margin-top: 24px"
    >
      <a-table
        :columns="comparisonColumns"
        :data-source="scenarioStore.comparison.scenarios"
        row-key="id"
        size="small"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'total_cost'">
            {{ record.total_cost ? `$${formatNumber(record.total_cost)}` : '-' }}
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Create Scenario Modal -->
    <a-modal
      v-model:open="showCreateModal"
      title="Create Scenario"
      @ok="handleCreate"
      :confirm-loading="creating"
      width="700px"
    >
      <a-form layout="vertical">
        <a-form-item label="Name" required>
          <a-input v-model:value="createForm.name" placeholder="e.g. Full Package Scenario" />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea v-model:value="createForm.description" :rows="2" />
        </a-form-item>
        <a-form-item label="Scenario Type">
          <a-select v-model:value="createForm.scenario_type">
            <a-select-option value="ideal">Ideal (all recommended)</a-select-option>
            <a-select-option value="prioritized">Prioritized</a-select-option>
            <a-select-option value="budget_constrained">Budget Constrained</a-select-option>
            <a-select-option value="custom">Custom</a-select-option>
          </a-select>
        </a-form-item>
        <a-divider>Interventions by Unit</a-divider>
        <div v-for="(entry, idx) in unitEntries" :key="idx" style="margin-bottom: 12px">
          <a-row :gutter="8">
            <a-col :span="8">
              <a-input v-model:value="entry.unit" placeholder="Unit code" />
            </a-col>
            <a-col :span="14">
              <a-select
                v-model:value="entry.interventions"
                mode="multiple"
                placeholder="Select interventions"
                style="width: 100%"
              >
                <a-select-option value="itn">ITN</a-select-option>
                <a-select-option value="irs">IRS</a-select-option>
                <a-select-option value="smc">SMC</a-select-option>
                <a-select-option value="iptp">IPTp</a-select-option>
                <a-select-option value="vaccine">Vaccine</a-select-option>
                <a-select-option value="cm">CM</a-select-option>
                <a-select-option value="pmc">PMC</a-select-option>
                <a-select-option value="lsm">LSM</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="2">
              <a-button danger size="small" @click="unitEntries.splice(idx, 1)">X</a-button>
            </a-col>
          </a-row>
        </div>
        <a-button type="dashed" block @click="addUnitEntry">+ Add Unit</a-button>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useScenarioStore } from '@/stores/scenario'

const props = defineProps<{ projectId: string }>()
const scenarioStore = useScenarioStore()

const showCreateModal = ref(false)
const creating = ref(false)

const createForm = reactive({
  name: '',
  description: '',
  scenario_type: 'custom',
})

const unitEntries = reactive<Array<{ unit: string; interventions: string[] }>>([
  { unit: '', interventions: [] },
])

const interventionColumns = [
  { title: 'Unit', dataIndex: 'unit', key: 'unit' },
  { title: 'Interventions', key: 'interventions' },
]

const costColumns = [
  { title: 'Unit', dataIndex: 'admin_unit_name', key: 'admin_unit_name' },
  { title: 'Intervention', dataIndex: 'intervention_code', key: 'intervention_code' },
  { title: 'Total Cost ($)', dataIndex: 'total_cost', key: 'total_cost' },
  { title: 'Years', dataIndex: 'years', key: 'years' },
]

const comparisonColumns = [
  { title: 'Scenario', dataIndex: 'name', key: 'name' },
  { title: 'Total Cost', key: 'total_cost' },
  { title: 'Population', dataIndex: 'population_covered', key: 'population_covered' },
  { title: 'Cases Averted', dataIndex: 'estimated_cases_averted', key: 'cases_averted' },
  { title: 'Deaths Averted', dataIndex: 'estimated_deaths_averted', key: 'deaths_averted' },
]

const interventionRows = computed(() => {
  const sc = scenarioStore.currentScenario
  if (!sc) return []
  return Object.entries(sc.interventions).map(([unit, interventions]) => ({
    key: unit,
    unit,
    interventions,
  }))
})

onMounted(() => {
  scenarioStore.fetchScenarios(props.projectId)
})

function addUnitEntry() {
  unitEntries.push({ unit: '', interventions: [] })
}

async function handleCreate() {
  const interventions: Record<string, string[]> = {}
  for (const entry of unitEntries) {
    if (entry.unit && entry.interventions.length > 0) {
      interventions[entry.unit] = entry.interventions
    }
  }

  if (Object.keys(interventions).length === 0) {
    message.warning('Add at least one unit with interventions')
    return
  }

  creating.value = true
  try {
    await scenarioStore.createScenario(props.projectId, {
      name: createForm.name,
      description: createForm.description || undefined,
      scenario_type: createForm.scenario_type,
      interventions,
    })
    showCreateModal.value = false
    message.success('Scenario created')
  } catch {
    message.error('Failed to create scenario')
  } finally {
    creating.value = false
  }
}

async function selectScenario(scenarioId: string) {
  await scenarioStore.fetchScenario(props.projectId, scenarioId)
}

async function handleDelete(scenarioId: string) {
  try {
    await scenarioStore.deleteScenario(props.projectId, scenarioId)
    message.success('Scenario deleted')
  } catch {
    message.error('Failed to delete scenario')
  }
}

async function handleCompare() {
  try {
    await scenarioStore.compareScenarios(props.projectId)
  } catch {
    message.error('Failed to compare scenarios')
  }
}

function formatNumber(n: number): string {
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
}
</script>
