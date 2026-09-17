import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  requestData: vi.fn(),
}))

import { requestData } from '@/api/client'
import { fetchMe, login } from '@/api/auth'

describe('auth api', () => {
  beforeEach(() => {
    vi.mocked(requestData).mockReset()
  })

  it('posts login without auth header flag', async () => {
    vi.mocked(requestData).mockResolvedValue({
      access_token: 'a',
      token_type: 'bearer',
    })
    await login({ username: 'operator', password: 'x' })
    expect(requestData).toHaveBeenCalledWith('/auth/login', {
      method: 'POST',
      data: { username: 'operator', password: 'x' },
      auth: false,
    })
  })

  it('gets /auth/me', async () => {
    vi.mocked(requestData).mockResolvedValue({
      id: 1,
      username: 'operator',
      role_code: 'operator',
      permissions: [],
    })
    await fetchMe()
    expect(requestData).toHaveBeenCalledWith('/auth/me')
  })
})
