<template>
  <a-layout-sider
    v-model:collapsed="collapsed"
    collapsible
    :width="240"
    style="background: #fff"
  >
    <a-menu
      v-model:selectedKeys="selectedKeys"
      mode="inline"
      style="border-right: 0"
    >
      <a-menu-item key="dashboard" @click="router.push('/')">
        <template #icon><DashboardOutlined /></template>
        Dashboard
      </a-menu-item>

      <template v-if="projectStore.currentProject">
        <a-menu-divider />
        <a-menu-item-group
          :title="collapsed ? '' : projectStore.currentProject.name"
        >
          <a-menu-item
            key="workflow"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/workflow`,
              )
            "
          >
            <template #icon><OrderedListOutlined /></template>
            Workflow
          </a-menu-item>

          <a-menu-item
            key="data-quality"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/data-quality`,
              )
            "
          >
            <template #icon><FileSearchOutlined /></template>
            Data Quality
          </a-menu-item>

          <a-menu-item
            key="stratification"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/stratification`,
              )
            "
          >
            <template #icon><HeatMapOutlined /></template>
            Stratification
          </a-menu-item>

          <a-menu-item
            key="interventions"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/interventions`,
              )
            "
          >
            <template #icon><MedicineBoxOutlined /></template>
            Interventions
          </a-menu-item>

          <a-menu-item
            key="scenarios"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/scenarios`,
              )
            "
          >
            <template #icon><FundOutlined /></template>
            Budget Scenarios
          </a-menu-item>

          <a-menu-item
            key="forecasts"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/forecasts`,
              )
            "
          >
            <template #icon><LineChartOutlined /></template>
            Forecasting
          </a-menu-item>

          <a-menu-item
            key="reports"
            @click="
              router.push(
                `/projects/${projectStore.currentProject!.id}/reports`,
              )
            "
          >
            <template #icon><FileDoneOutlined /></template>
            Reports
          </a-menu-item>
        </a-menu-item-group>
      </template>
    </a-menu>
  </a-layout-sider>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import {
  DashboardOutlined,
  OrderedListOutlined,
  FileSearchOutlined,
  HeatMapOutlined,
  MedicineBoxOutlined,
  FundOutlined,
  LineChartOutlined,
  FileDoneOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const route = useRoute()
const projectStore = useProjectStore()

const collapsed = ref(false)
const selectedKeys = ref<string[]>(['dashboard'])

watch(
  () => route.name,
  (name) => {
    if (name === 'Dashboard') selectedKeys.value = ['dashboard']
    else if (name === 'Workflow' || name === 'StepDetail')
      selectedKeys.value = ['workflow']
    else if (name === 'DataQuality') selectedKeys.value = ['data-quality']
    else if (name === 'Stratification')
      selectedKeys.value = ['stratification']
    else if (name === 'Interventions')
      selectedKeys.value = ['interventions']
    else if (name === 'Scenarios')
      selectedKeys.value = ['scenarios']
    else if (name === 'Forecasts')
      selectedKeys.value = ['forecasts']
    else if (name === 'Reports')
      selectedKeys.value = ['reports']
  },
  { immediate: true },
)
</script>
