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
    <a-card style="width: 440px">
      <div style="text-align: center; margin-bottom: 24px">
        <h1 style="font-size: 24px; color: #1677ff">Create Account</h1>
        <p style="color: #8c8c8c">Join the SNT Planning Toolkit</p>
      </div>

      <a-form :model="form" layout="vertical" @finish="handleRegister">
        <a-form-item
          label="Full Name"
          name="full_name"
          :rules="[{ required: true, message: 'Enter your full name' }]"
        >
          <a-input v-model:value="form.full_name" placeholder="Full name" />
        </a-form-item>

        <a-form-item
          label="Email"
          name="email"
          :rules="[
            { required: true, type: 'email', message: 'Enter a valid email' },
          ]"
        >
          <a-input v-model:value="form.email" placeholder="you@example.com" />
        </a-form-item>

        <a-form-item label="Organization" name="organization">
          <a-input
            v-model:value="form.organization"
            placeholder="Organization (optional)"
          />
        </a-form-item>

        <a-form-item
          label="Password"
          name="password"
          :rules="[
            { required: true, min: 8, message: 'Minimum 8 characters' },
          ]"
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
            Register
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

      <a-alert
        v-if="success"
        message="Registration successful! You can now sign in."
        type="success"
        show-icon
        style="margin-bottom: 16px"
      />

      <div style="text-align: center">
        <router-link to="/login">Already have an account? Sign in</router-link>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const form = reactive({
  full_name: '',
  email: '',
  password: '',
  organization: '',
})
const loading = ref(false)
const error = ref('')
const success = ref(false)

async function handleRegister() {
  loading.value = true
  error.value = ''
  success.value = false
  try {
    await authStore.register(form)
    success.value = true
  } catch (err: unknown) {
    const axiosError = err as { response?: { data?: { detail?: string } } }
    error.value = axiosError.response?.data?.detail || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>
