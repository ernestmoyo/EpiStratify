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
          <h1>Projects</h1>
          <p>Manage your SNT planning projects</p>
        </div>
        <a-button type="primary" @click="showCreateModal = true">
          New Project
        </a-button>
      </div>
    </div>

    <a-spin :spinning="projectStore.loading">
      <a-empty v-if="projectStore.projects.length === 0" description="No projects yet. Create one to get started." />

      <a-row :gutter="[16, 16]">
        <a-col
          v-for="project in projectStore.projects"
          :key="project.id"
          :xs="24"
          :sm="12"
          :lg="8"
        >
          <a-card
            hoverable
            @click="openProject(project.id)"
          >
            <template #title>{{ project.name }}</template>
            <template #extra>
              <a-tag :color="statusColor(project.status)">
                {{ project.status }}
              </a-tag>
            </template>
            <p>{{ project.country }} &mdash; {{ project.year }}</p>
            <p v-if="project.description" style="color: #8c8c8c">
              {{ project.description }}
            </p>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- Create project modal -->
    <a-modal
      v-model:open="showCreateModal"
      title="New Project"
      @ok="handleCreateProject"
      :confirm-loading="creating"
    >
      <a-form layout="vertical">
        <a-form-item label="Project Name" required>
          <a-input v-model:value="newProject.name" placeholder="e.g. Ghana SNT 2025" />
        </a-form-item>
        <a-form-item label="Country" required>
          <a-input v-model:value="newProject.country" placeholder="e.g. Ghana" />
        </a-form-item>
        <a-form-item label="Year" required>
          <a-input-number
            v-model:value="newProject.year"
            :min="2000"
            :max="2100"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea
            v-model:value="newProject.description"
            placeholder="Brief description"
            :rows="3"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const projectStore = useProjectStore()

const showCreateModal = ref(false)
const creating = ref(false)
const newProject = reactive({
  name: '',
  country: '',
  year: new Date().getFullYear(),
  description: '',
})

onMounted(() => {
  projectStore.fetchProjects()
})

function statusColor(status: string) {
  const colors: Record<string, string> = {
    draft: 'default',
    in_progress: 'processing',
    completed: 'success',
    archived: 'warning',
  }
  return colors[status] || 'default'
}

function openProject(id: string) {
  projectStore.fetchProject(id)
  router.push(`/projects/${id}/workflow`)
}

async function handleCreateProject() {
  creating.value = true
  try {
    const project = await projectStore.createProject({
      name: newProject.name,
      country: newProject.country,
      year: newProject.year,
      description: newProject.description || undefined,
    })
    showCreateModal.value = false
    router.push(`/projects/${project.id}/workflow`)
  } finally {
    creating.value = false
  }
}
</script>
