import { beforeEach, describe, expect, it } from 'vitest'

import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from '@/utils/tokenStorage'

describe('tokenStorage', () => {
  beforeEach(() => {
    sessionStorage.clear()
  })

  it('stores and reads access token from sessionStorage', () => {
    setAccessToken('token-abc')
    expect(getAccessToken()).toBe('token-abc')
  })

  it('clears access token', () => {
    setAccessToken('token-abc')
    clearAccessToken()
    expect(getAccessToken()).toBeNull()
  })
})
