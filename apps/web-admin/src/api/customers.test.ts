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

import { apiClient } from '@/api/client'
import {
  createCustomer,
  deactivateCustomer,
  listCustomers,
  updateCustomer,
} from '@/api/customers'

describe('customers api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists customers with code/name filters', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [{ id: 1, customer_code: 'CUS01', name: '客户A', status: 1 }],
          total: 1,
          page: 1,
          page_size: 20,
        },
        traceId: 't1',
      },
    } as never)

    await listCustomers({ code: 'CUS', name: '客户', page: 1, page_size: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/customers', {
      params: { code: 'CUS', name: '客户', page: 1, page_size: 20 },
    })
  })

  it('creates customer via POST /customers', async () => {
    const body = { customer_code: 'CUS02', name: '客户B' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, ...body, status: 1 },
        traceId: 't1',
      },
    } as never)

    await createCustomer(body)

    expect(apiClient.post).toHaveBeenCalledWith('/customers', body)
  })

  it('updates customer via PATCH /customers/:id', async () => {
    const body = { name: '客户B（更名）' }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, customer_code: 'CUS02', name: '客户B（更名）', status: 1 },
        traceId: 't1',
      },
    } as never)

    await updateCustomer(2, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/customers/2', body)
  })

  it('deactivates customer via POST /customers/:id/deactivate', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, customer_code: 'CUS02', name: '客户B', status: 0 },
        traceId: 't1',
      },
    } as never)

    await deactivateCustomer(2)

    expect(apiClient.post).toHaveBeenCalledWith('/customers/2/deactivate')
  })
})
