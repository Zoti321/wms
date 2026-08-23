import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

import { apiClient } from '@/api/client'
import { fetchMe, login } from '@/api/auth'

describe('auth api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
  })

  it('logs in via POST /auth/login', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { access_token: 'token-1', token_type: 'bearer' },
        traceId: 't1',
      },
    } as never)

    const result = await login({ username: 'admin', password: 'secret' })

    expect(apiClient.post).toHaveBeenCalledWith('/auth/login', {
      username: 'admin',
      password: 'secret',
    })
    expect(result.access_token).toBe('token-1')
  })

  it('fetches current user via GET /auth/me', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          id: 1,
          username: 'admin',
          role_code: 'admin',
          permissions: ['catalog:read'],
        },
        traceId: 't1',
      },
    } as never)

    const me = await fetchMe()

    expect(apiClient.get).toHaveBeenCalledWith('/auth/me')
    expect(me.username).toBe('admin')
  })
})
