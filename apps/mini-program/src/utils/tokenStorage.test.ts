import { beforeEach, describe, expect, it, vi } from 'vitest'

const storage = new Map<string, string>()

vi.stubGlobal('uni', {
  getStorageSync: (key: string) => storage.get(key) ?? '',
  setStorageSync: (key: string, value: string) => {
    storage.set(key, value)
  },
  removeStorageSync: (key: string) => {
    storage.delete(key)
  },
})

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/utils/tokenStorage'

describe('tokenStorage', () => {
  beforeEach(() => {
    storage.clear()
  })

  it('stores and clears wms_access_token', () => {
    expect(getAccessToken()).toBeNull()
    setAccessToken('tok-1')
    expect(getAccessToken()).toBe('tok-1')
    clearAccessToken()
    expect(getAccessToken()).toBeNull()
  })
})
