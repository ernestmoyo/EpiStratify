import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { projectsApi, type ProjectResponse, type ProjectCreate } from '@/api/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<ProjectResponse[]>([])
  const currentProject = ref<ProjectResponse | null>(null)
  const loading = ref(false)

  const projectCount = computed(() => projects.value.length)

  async function fetchProjects() {
    loading.value = true
    try {
      const response = await projectsApi.list()
      projects.value = response.data.items
    } finally {
      loading.value = false
    }
  }

  async function createProject(data: ProjectCreate) {
    const response = await projectsApi.create(data)
    projects.value.unshift(response.data)
    return response.data
  }

  async function fetchProject(projectId: string) {
    loading.value = true
    try {
      const response = await projectsApi.get(projectId)
      currentProject.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function archiveProject(projectId: string) {
    await projectsApi.archive(projectId)
    projects.value = projects.value.filter((p) => p.id !== projectId)
    if (currentProject.value?.id === projectId) {
      currentProject.value = null
    }
  }

  return {
    projects,
    currentProject,
    loading,
    projectCount,
    fetchProjects,
    createProject,
    fetchProject,
    archiveProject,
  }
})
