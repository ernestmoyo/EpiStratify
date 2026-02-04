import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Dashboard',
          component: () => import('@/views/dashboard/DashboardView.vue'),
        },
        {
          path: 'projects/:projectId',
          name: 'ProjectDetail',
          component: () => import('@/views/projects/ProjectDetailView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/workflow',
          name: 'Workflow',
          component: () => import('@/views/workflow/WorkflowView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/workflow/:step',
          name: 'StepDetail',
          component: () => import('@/views/workflow/StepDetailView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/data-quality',
          name: 'DataQuality',
          component: () => import('@/views/data-quality/DataQualityView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/stratification',
          name: 'Stratification',
          component: () =>
            import('@/views/stratification/StratificationView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/interventions',
          name: 'Interventions',
          component: () =>
            import('@/views/interventions/InterventionTailoringView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/scenarios',
          name: 'Scenarios',
          component: () => import('@/views/scenarios/ScenarioView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/forecasts',
          name: 'Forecasts',
          component: () => import('@/views/forecasts/ForecastView.vue'),
          props: true,
        },
        {
          path: 'projects/:projectId/reports',
          name: 'Reports',
          component: () => import('@/views/reports/ReportsView.vue'),
          props: true,
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: 'Login' }
  }

  if (to.meta.public && authStore.isAuthenticated) {
    return { name: 'Dashboard' }
  }
})

export default router
