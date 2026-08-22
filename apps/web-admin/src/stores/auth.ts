import { defineStore } from 'pinia'
import { ref } from 'vue'

import * as authApi from '@/api/auth'
import type { MeData } from '@/types/api'
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/utils/tokenStorage'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(getAccessToken())
  const user = ref<MeData | null>(null)
  const loading = ref(false)

  const permissions = ref<string[]>([])

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    try {
      const result = await authApi.login({ username, password })
      token.value = result.access_token
      setAccessToken(result.access_token)
      await loadMe()
    } finally {
      loading.value = false
    }
  }

  async function loadMe(): Promise<void> {
    if (!token.value) {
      user.value = null
      permissions.value = []
      return
    }

    const me = await authApi.fetchMe()
    user.value = me
    permissions.value = me.permissions
  }

  async function restoreSession(): Promise<boolean> {
    const stored = getAccessToken()
    if (!stored) {
      logout()
      return false
    }

    token.value = stored
    try {
      await loadMe()
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout(): void {
    token.value = null
    user.value = null
    permissions.value = []
    clearAccessToken()
  }

  function hasPermission(required: string): boolean {
    return permissions.value.includes(required)
  }

  return {
    token,
    user,
    permissions,
    loading,
    login,
    loadMe,
    restoreSession,
    logout,
    hasPermission,
  }
})
