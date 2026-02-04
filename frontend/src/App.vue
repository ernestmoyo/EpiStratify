<template>
  <a-config-provider
    :theme="{
      token: {
        colorPrimary: '#1677ff',
        borderRadius: 6,
      },
    }"
  >
    <router-view />
  </a-config-provider>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await authStore.fetchUser()
  }
})
</script>
