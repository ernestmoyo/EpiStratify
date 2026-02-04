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
          <h1>Data Quality</h1>
          <p>Upload data and run quality assessments</p>
        </div>
        <a-button type="primary" @click="showUploadModal = true">
          Upload Data
        </a-button>
      </div>
    </div>

    <!-- Data sources list -->
    <a-table
      :columns="columns"
      :data-source="dataSources"
      :loading="loading"
      row-key="id"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'quality_score'">
          <a-progress
            v-if="record.quality_score !== null"
            :percent="Math.round(record.quality_score * 100)"
            :status="qualityStatus(record.quality_score)"
            size="small"
          />
          <span v-else style="color: #8c8c8c">Not checked</span>
        </template>

        <template v-if="column.key === 'source_type'">
          <a-tag>{{ record.source_type }}</a-tag>
        </template>

        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="runQualityCheck(record.id)">
              Run Checks
            </a-button>
            <a-button
              size="small"
              type="link"
              @click="viewReport(record.id)"
            >
              Report
            </a-button>
            <a-popconfirm
              title="Delete this data source?"
              @confirm="deleteSource(record.id)"
            >
              <a-button size="small" danger type="link">Delete</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>

    <!-- Quality report drawer -->
    <a-drawer
      v-model:open="showReport"
      title="Quality Report"
      :width="600"
    >
      <template v-if="currentReport">
        <a-statistic
          title="Overall Quality Score"
          :value="
            currentReport.overall_score !== null
              ? Math.round(currentReport.overall_score * 100)
              : 'N/A'
          "
          suffix="%"
          style="margin-bottom: 24px"
        />

        <a-list
          :data-source="currentReport.checks"
          item-layout="horizontal"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta
                :title="item.check_type"
                :description="item.message"
              />
              <template #actions>
                <a-tag :color="checkStatusColor(item.status)">
                  {{ item.status }}
                </a-tag>
                <span v-if="item.score !== null">
                  {{ Math.round(item.score * 100) }}%
                </span>
              </template>
            </a-list-item>
          </template>
        </a-list>

        <a-divider />

        <h4>Recommendations</h4>
        <a-list
          v-if="currentReport.recommendations.length > 0"
          :data-source="currentReport.recommendations"
          size="small"
        >
          <template #renderItem="{ item }">
            <a-list-item>{{ item }}</a-list-item>
          </template>
        </a-list>
        <p v-else style="color: #8c8c8c">No recommendations at this time.</p>
      </template>
    </a-drawer>

    <!-- Upload modal -->
    <a-modal
      v-model:open="showUploadModal"
      title="Upload Data Source"
      @ok="handleUpload"
      :confirm-loading="uploading"
    >
      <a-form layout="vertical">
        <a-form-item label="Name" required>
          <a-input
            v-model:value="uploadForm.name"
            placeholder="e.g. HMIS 2024 Data"
          />
        </a-form-item>
        <a-form-item label="Data Type" required>
          <a-select v-model:value="uploadForm.source_type">
            <a-select-option value="epidemiological">
              Epidemiological
            </a-select-option>
            <a-select-option value="intervention">Intervention</a-select-option>
            <a-select-option value="demographic">Demographic</a-select-option>
            <a-select-option value="geospatial">Geospatial</a-select-option>
            <a-select-option value="entomological">
              Entomological
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="File">
          <a-upload
            :before-upload="handleFileSelect"
            :max-count="1"
            accept=".csv,.xlsx,.xls,.geojson,.json"
          >
            <a-button>Select File</a-button>
          </a-upload>
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea
            v-model:value="uploadForm.description"
            :rows="2"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  dataSourcesApi,
  type DataSourceResponse,
  type QualityReportResponse,
} from '@/api/dataSources'

const props = defineProps<{ projectId: string }>()

const loading = ref(false)
const uploading = ref(false)
const showUploadModal = ref(false)
const showReport = ref(false)
const dataSources = ref<DataSourceResponse[]>([])
const currentReport = ref<QualityReportResponse | null>(null)
const selectedFile = ref<File | null>(null)

const uploadForm = reactive({
  name: '',
  source_type: 'epidemiological',
  description: '',
})

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Type', dataIndex: 'source_type', key: 'source_type' },
  { title: 'Format', dataIndex: 'file_format', key: 'file_format' },
  { title: 'Records', dataIndex: 'record_count', key: 'record_count' },
  { title: 'Quality', key: 'quality_score' },
  { title: 'Actions', key: 'actions', width: 280 },
]

onMounted(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const response = await dataSourcesApi.list(props.projectId)
    dataSources.value = response.data
  } finally {
    loading.value = false
  }
}

function handleFileSelect(file: File) {
  selectedFile.value = file
  return false // Prevent auto-upload
}

async function handleUpload() {
  if (!selectedFile.value) {
    message.warning('Please select a file')
    return
  }

  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('name', uploadForm.name)
    formData.append('source_type', uploadForm.source_type)
    if (uploadForm.description) {
      formData.append('description', uploadForm.description)
    }

    await dataSourcesApi.upload(props.projectId, formData)
    showUploadModal.value = false
    message.success('Data source uploaded')
    await fetchData()
  } catch {
    message.error('Upload failed')
  } finally {
    uploading.value = false
  }
}

async function runQualityCheck(dataSourceId: string) {
  try {
    message.loading({ content: 'Running quality checks...', key: 'qc' })
    const response = await dataSourcesApi.runQualityCheck(
      props.projectId,
      dataSourceId,
    )
    currentReport.value = response.data
    showReport.value = true
    message.success({ content: 'Quality checks complete', key: 'qc' })
    await fetchData()
  } catch {
    message.error({ content: 'Quality check failed', key: 'qc' })
  }
}

async function viewReport(dataSourceId: string) {
  try {
    const response = await dataSourcesApi.getQualityReport(
      props.projectId,
      dataSourceId,
    )
    currentReport.value = response.data
    showReport.value = true
  } catch {
    message.error('Could not load report')
  }
}

async function deleteSource(dataSourceId: string) {
  try {
    await dataSourcesApi.delete(props.projectId, dataSourceId)
    message.success('Data source deleted')
    await fetchData()
  } catch {
    message.error('Could not delete data source')
  }
}

function qualityStatus(score: number): 'success' | 'normal' | 'exception' {
  if (score >= 0.8) return 'success'
  if (score >= 0.5) return 'normal'
  return 'exception'
}

function checkStatusColor(status: string): string {
  const colors: Record<string, string> = {
    passed: 'success',
    warning: 'warning',
    failed: 'error',
    pending: 'default',
    running: 'processing',
  }
  return colors[status] || 'default'
}
</script>
