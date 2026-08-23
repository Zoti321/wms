import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

import { apiClient } from '@/api/client'
import { listOperationLogs } from '@/api/operationLogs'

describe('listOperationLogs', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
  })

  it('gets operation logs with filters', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [
            {
              id: 1,
              operator_id: 1,
              operator_name: 'admin',
              action: 'auth.login',
              resource_type: null,
              resource_id: null,
              detail: null,
              created_at: '2026-01-01 00:00:00',
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
        traceId: 't1',
      },
    } as never)

    await listOperationLogs({
      operator_id: 1,
      action: 'auth.login',
      created_from: '2026-01-01T00:00:00',
      created_to: '2026-01-02T00:00:00',
      page: 1,
      page_size: 20,
    })

    expect(apiClient.get).toHaveBeenCalledWith('/operation-logs', {
      params: {
        operator_id: 1,
        action: 'auth.login',
        created_from: '2026-01-01T00:00:00',
        created_to: '2026-01-02T00:00:00',
        page: 1,
        page_size: 20,
      },
    })
  })
})
