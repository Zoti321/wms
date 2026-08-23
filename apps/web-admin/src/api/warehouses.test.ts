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
  createWarehouse,
  deactivateWarehouse,
  listWarehouses,
  updateWarehouse,
} from '@/api/warehouses'

describe('warehouses api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists warehouses with code/name filters', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [{ id: 1, warehouse_code: 'WH01', name: '主仓', status: 1 }],
          total: 1,
          page: 1,
          page_size: 20,
        },
        traceId: 't1',
      },
    } as never)

    await listWarehouses({ code: 'WH', name: '主', page: 1, page_size: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/warehouses', {
      params: { code: 'WH', name: '主', page: 1, page_size: 20 },
    })
  })

  it('creates warehouse via POST /warehouses', async () => {
    const body = { warehouse_code: 'WH02', name: '分仓' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, ...body, status: 1 },
        traceId: 't1',
      },
    } as never)

    await createWarehouse(body)

    expect(apiClient.post).toHaveBeenCalledWith('/warehouses', body)
  })

  it('updates warehouse via PATCH /warehouses/:id', async () => {
    const body = { name: '主仓（更名）' }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 1, warehouse_code: 'WH01', name: '主仓（更名）', status: 1 },
        traceId: 't1',
      },
    } as never)

    await updateWarehouse(1, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/warehouses/1', body)
  })

  it('deactivates warehouse via POST /warehouses/:id/deactivate', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 1, warehouse_code: 'WH01', name: '主仓', status: 0 },
        traceId: 't1',
      },
    } as never)

    await deactivateWarehouse(1)

    expect(apiClient.post).toHaveBeenCalledWith('/warehouses/1/deactivate')
  })
})
