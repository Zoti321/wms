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

import { apiClient, requestData } from '@/api/client'
import { listInventoryAlerts } from '@/api/inventories'

describe('listInventoryAlerts', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('gets alerts with warehouse and pagination params', async () => {
    const payload = {
      items: [
        {
          id: 1,
          warehouse_id: 2,
          sku_id: 3,
          qty_available: '5.000',
          safety_stock: '10.000',
          status: 'open',
          created_at: '2026-01-01 00:00:00',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    }
    vi.mocked(apiClient.get).mockResolvedValue({
      data: { code: 0, message: 'ok', data: payload, traceId: 't1' },
    } as never)

    const result = await listInventoryAlerts({
      warehouse_id: 2,
      page: 1,
      page_size: 20,
    })

    expect(apiClient.get).toHaveBeenCalledWith('/inventories/alerts', {
      params: { warehouse_id: 2, page: 1, page_size: 20 },
    })
    expect(result.total).toBe(1)
    expect(result.items[0]?.status).toBe('open')
  })
})
