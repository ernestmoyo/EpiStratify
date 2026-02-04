<template>
  <a-layout style="min-height: 100vh">
    <AppHeader />
    <a-layout>
      <AppSidebar />
      <a-layout-content style="padding: 24px; background: #f5f5f5">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>
