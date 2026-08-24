import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authApi from '@/api/auth'
import type { MeData } from '@/types/api'
import { canAccessOperatorApp } from '@/utils/authGate'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/utils/tokenStorage'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(getAccessToken())
  const user = ref<MeData | null>(null)
  const loading = ref(false)
  /** 已登录但非仓管员 */
  const denied = ref(false)

  const isOperator = computed(() => canAccessOperatorApp(user.value?.role_code))

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    denied.value = false
    try {
      const result = await authApi.login({ username, password })
      accessToken.value = result.access_token
      setAccessToken(result.access_token)
      await fetchMe()
      denied.value = !canAccessOperatorApp(user.value?.role_code)
    } finally {
      loading.value = false
    }
  }

  async function fetchMe(): Promise<void> {
    if (!accessToken.value) {
      user.value = null
      return
    }
    user.value = await authApi.fetchMe()
  }

  async function restoreSession(): Promise<'ok' | 'denied' | 'none'> {
    const stored = getAccessToken()
    if (!stored) {
      logout()
      return 'none'
    }
    accessToken.value = stored
    try {
      await fetchMe()
      if (!canAccessOperatorApp(user.value?.role_code)) {
        denied.value = true
        return 'denied'
      }
      denied.value = false
      return 'ok'
    } catch {
      logout()
      return 'none'
    }
  }

  function logout(): void {
    accessToken.value = null
    user.value = null
    denied.value = false
    clearAccessToken()
  }

  return {
    accessToken,
    user,
    loading,
    denied,
    isOperator,
    login,
    fetchMe,
    restoreSession,
    logout,
  }
})
