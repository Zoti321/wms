import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

import { apiClient, requestData } from '@/api/client'
import {
  assignUserRole,
  createUser,
  deactivateUser,
  listUsers,
  resetUserPassword,
} from '@/api/users'

describe('users api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('lists users with pagination params', async () => {
    const payload = {
      items: [{ id: 1, username: 'admin', role_code: 'admin', status: 1 }],
      total: 1,
      page: 1,
      page_size: 20,
    }
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { code: 0, message: 'ok', data: payload, traceId: 't1' },
    } as never)

    const result = await listUsers({ page: 1, page_size: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/users', {
      params: { page: 1, page_size: 20 },
    })
    expect(result.items[0]?.username).toBe('admin')
  })

  it('creates user via POST /users', async () => {
    const body = { username: 'op1', password: 'Temp@123456', role_code: 'operator' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, username: 'op1', role_code: 'operator', status: 1 },
        traceId: 't1',
      },
    } as never)

    await createUser(body)

    expect(apiClient.post).toHaveBeenCalledWith('/users', body)
  })

  it('deactivates user via POST /users/:id/deactivate', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, username: 'op1', role_code: 'operator', status: 0 },
        traceId: 't1',
      },
    } as never)

    await deactivateUser(2)

    expect(apiClient.post).toHaveBeenCalledWith('/users/2/deactivate')
  })

  it('resets password via POST /users/:id/reset-password', async () => {
    const body = { password: 'NewPass@123' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, username: 'op1', role_code: 'operator', status: 1 },
        traceId: 't1',
      },
    } as never)

    await resetUserPassword(2, body)

    expect(apiClient.post).toHaveBeenCalledWith('/users/2/reset-password', body)
  })

  it('assigns role via PATCH /users/:id/role', async () => {
    const body = { role_code: 'supervisor' }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, username: 'op1', role_code: 'supervisor', status: 1 },
        traceId: 't1',
      },
    } as never)

    await assignUserRole(2, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/users/2/role', body)
  })
})
