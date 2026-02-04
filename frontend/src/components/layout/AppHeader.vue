<template>
  <a-layout-header
    style="
      background: #fff;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #f0f0f0;
    "
  >
    <div style="display: flex; align-items: center; gap: 12px">
      <h2 style="margin: 0; font-size: 18px; color: #1677ff">EpiStratify SNT Toolkit</h2>
    </div>

    <div style="display: flex; align-items: center; gap: 16px">
      <span style="color: #8c8c8c">{{ authStore.userName }}</span>
      <a-dropdown>
        <a-avatar style="background-color: #1677ff; cursor: pointer">
          {{ initials }}
        </a-avatar>
        <template #overlay>
          <a-menu>
            <a-menu-item key="logout" @click="handleLogout">
              Logout
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </a-layout-header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const initials = computed(() => {
  const name = authStore.user?.full_name || ''
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>
