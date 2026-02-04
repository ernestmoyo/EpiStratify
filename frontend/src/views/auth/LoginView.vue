<template>
  <div
    style="
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #f5f5f5;
    "
  >
    <a-card style="width: 400px">
      <div style="text-align: center; margin-bottom: 24px">
        <h1 style="font-size: 24px; color: #1677ff">EpiStratify</h1>
        <p style="color: #8c8c8c">SNT Planning Toolkit</p>
      </div>

      <a-form
        :model="form"
        layout="vertical"
        @finish="handleLogin"
      >
        <a-form-item
          label="Email"
          name="email"
          :rules="[{ required: true, type: 'email', message: 'Enter a valid email' }]"
        >
          <a-input v-model:value="form.email" placeholder="you@example.com" />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[{ required: true, message: 'Enter your password' }]"
        >
          <a-input-password
            v-model:value="form.password"
            placeholder="Password"
          />
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            block
          >
            Sign In
          </a-button>
        </a-form-item>
      </a-form>

      <a-alert
        v-if="error"
        :message="error"
        type="error"
        show-icon
        closable
        style="margin-bottom: 16px"
        @close="error = ''"
      />

      <div style="text-align: center">
        <router-link to="/register">Create an account</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ email: '', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.email, form.password)
    router.push('/')
  } catch (err: unknown) {
    const axiosError = err as { response?: { data?: { detail?: string } } }
    error.value = axiosError.response?.data?.detail || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>
