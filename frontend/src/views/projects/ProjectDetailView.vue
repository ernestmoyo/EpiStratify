<template>
  <div class="content-container">
    <a-spin :spinning="projectStore.loading">
      <template v-if="projectStore.currentProject">
        <div class="page-header">
          <h1>{{ projectStore.currentProject.name }}</h1>
          <p>
            {{ projectStore.currentProject.country }} &mdash;
            {{ projectStore.currentProject.year }}
          </p>
        </div>

        <a-row :gutter="[16, 16]">
          <a-col :span="8">
            <a-card>
              <a-statistic
                title="Status"
                :value="projectStore.currentProject.status"
              />
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card>
              <a-statistic
                title="Admin Level"
                :value="projectStore.currentProject.admin_level"
              />
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card>
              <a-statistic title="Workflow Progress" suffix="%">
                <template #formatter>
                  {{ Math.round(workflowStore.overallProgress) }}
                </template>
              </a-statistic>
            </a-card>
          </a-col>
        </a-row>

        <a-card title="Quick Actions" style="margin-top: 16px">
          <a-space>
            <a-button
              type="primary"
              @click="
                router.push(
                  `/projects/${projectStore.currentProject.id}/workflow`,
                )
              "
            >
              Open Workflow
            </a-button>
            <a-button
              @click="
                router.push(
                  `/projects/${projectStore.currentProject.id}/data-quality`,
                )
              "
            >
              Data Quality
            </a-button>
            <a-button
              @click="
                router.push(
                  `/projects/${projectStore.currentProject.id}/stratification`,
                )
              "
            >
              Stratification
            </a-button>
          </a-space>
        </a-card>
      </template>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useWorkflowStore } from '@/stores/workflow'

const props = defineProps<{ projectId: string }>()

const router = useRouter()
const projectStore = useProjectStore()
const workflowStore = useWorkflowStore()

onMounted(async () => {
  await projectStore.fetchProject(props.projectId)
  await workflowStore.fetchWorkflow(props.projectId)
})
</script>
