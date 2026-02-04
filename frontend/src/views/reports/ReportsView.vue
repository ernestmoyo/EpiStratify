<template>
  <div class="content-container">
    <div class="page-header">
      <div style="display: flex; justify-content: space-between; align-items: center">
        <div>
          <h1>Reports</h1>
          <p>Generate and download project reports</p>
        </div>
        <a-button type="primary" @click="showGenerateModal = true">
          Generate Report
        </a-button>
      </div>
    </div>

    <!-- Reports table -->
    <a-card>
      <a-table
        :columns="reportColumns"
        :data-source="reports"
        row-key="id"
        :loading="loading"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'report_type'">
            <a-tag>{{ formatReportType(record.report_type) }}</a-tag>
          </template>
          <template v-if="column.key === 'format'">
            <a-tag color="blue">{{ record.format.toUpperCase() }}</a-tag>
          </template>
          <template v-if="column.key === 'file_size_bytes'">
            {{ record.file_size_bytes ? formatBytes(record.file_size_bytes) : '-' }}
          </template>
          <template v-if="column.key === 'created_at'">
            {{ new Date(record.created_at).toLocaleDateString() }}
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button type="link" size="small" @click="handleDownload(record.id)">
                Download
              </a-button>
              <a-popconfirm title="Delete this report?" @confirm="handleDelete(record.id)">
                <a-button type="link" danger size="small">Delete</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Generate modal -->
    <a-modal
      v-model:open="showGenerateModal"
      title="Generate Report"
      @ok="handleGenerate"
      :confirm-loading="generating"
    >
      <a-form layout="vertical">
        <a-form-item label="Report Type" required>
          <a-select v-model:value="generateForm.report_type">
            <a-select-option value="full_snt">Full SNT Report</a-select-option>
            <a-select-option value="executive_summary">Executive Summary</a-select-option>
            <a-select-option value="stratification">Stratification Report</a-select-option>
            <a-select-option value="budget">Budget Report</a-select-option>
            <a-select-option value="step_summary">Step Summary</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="Format">
          <a-radio-group v-model:value="generateForm.format">
            <a-radio-button value="pdf">JSON/PDF</a-radio-button>
            <a-radio-button value="csv">CSV</a-radio-button>
            <a-radio-button value="excel">Excel</a-radio-button>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="Title (optional)">
          <a-input v-model:value="generateForm.title" placeholder="Custom report title" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import { reportsApi, type ReportRecordResponse } from '@/api/reports'

const props = defineProps<{ projectId: string }>()

const loading = ref(false)
const generating = ref(false)
const showGenerateModal = ref(false)
const reports = ref<ReportRecordResponse[]>([])

const generateForm = reactive({
  report_type: 'full_snt',
  format: 'pdf',
  title: '',
})

const reportColumns = [
  { title: 'Title', dataIndex: 'title', key: 'title' },
  { title: 'Type', key: 'report_type' },
  { title: 'Format', key: 'format' },
  { title: 'Size', key: 'file_size_bytes' },
  { title: 'Created', key: 'created_at' },
  { title: 'Actions', key: 'actions', width: 180 },
]

onMounted(fetchReports)

async function fetchReports() {
  loading.value = true
  try {
    const response = await reportsApi.list(props.projectId)
    reports.value = response.data.items
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  generating.value = true
  try {
    const response = await reportsApi.generate(props.projectId, {
      report_type: generateForm.report_type,
      format: generateForm.format,
      title: generateForm.title || undefined,
    })
    reports.value.unshift(response.data)
    showGenerateModal.value = false
    message.success('Report generated')
  } catch {
    message.error('Failed to generate report')
  } finally {
    generating.value = false
  }
}

async function handleDownload(reportId: string) {
  try {
    const response = await reportsApi.download(props.projectId, reportId)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${reportId}`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch {
    message.error('Failed to download report')
  }
}

async function handleDelete(reportId: string) {
  try {
    await reportsApi.delete(props.projectId, reportId)
    reports.value = reports.value.filter((r) => r.id !== reportId)
    message.success('Report deleted')
  } catch {
    message.error('Failed to delete report')
  }
}

function formatReportType(type: string): string {
  const labels: Record<string, string> = {
    full_snt: 'Full SNT',
    executive_summary: 'Executive Summary',
    stratification: 'Stratification',
    budget: 'Budget',
    step_summary: 'Step Summary',
  }
  return labels[type] || type
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>
