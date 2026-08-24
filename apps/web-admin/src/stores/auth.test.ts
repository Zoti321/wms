import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  fetchMe: vi.fn(),
}))

import * as authApi from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    sessionStorage.clear()
    vi.mocked(authApi.login).mockReset()
    vi.mocked(authApi.fetchMe).mockReset()
  })

  it('login stores token and exposes permissions via utils', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      access_token: 'token-1',
      token_type: 'bearer',
    })
    vi.mocked(authApi.fetchMe).mockResolvedValue({
      id: 1,
      username: 'admin',
      role_code: 'admin',
      permissions: ['catalog:read'],
    })

    const auth = useAuthStore()
    await auth.login('admin', 'pass')

    expect(auth.token).toBe('token-1')
    expect(auth.permissions).toEqual(['catalog:read'])
    expect(auth.hasPermission('catalog:read')).toBe(true)
    expect(auth.hasPermission('catalog:write')).toBe(false)
  })

  it('restoreSession returns false and clears state when me fails', async () => {
    sessionStorage.setItem('wms_access_token', 'stale-token')
    vi.mocked(authApi.fetchMe).mockRejectedValue(new Error('未授权'))

    const auth = useAuthStore()
    const ok = await auth.restoreSession()

    expect(ok).toBe(false)
    expect(auth.token).toBeNull()
    expect(auth.user).toBeNull()
  })

  it('logout clears session storage', () => {
    sessionStorage.setItem('wms_access_token', 'token-1')
    const auth = useAuthStore()
    auth.logout()
    expect(sessionStorage.getItem('wms_access_token')).toBeNull()
  })
})
