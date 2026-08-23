import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    post: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

vi.mock('@/utils/idempotency', () => ({
  createIdempotencyKey: () => 'idem-key-fixed',
}))

import { apiClient, requestData } from '@/api/client'
import {
  approveStocktake,
  cancelStocktake,
  createStocktake,
} from '@/api/stocktakes'

const sampleOrder = {
  id: 1,
  order_no: 'ST-1',
  warehouse_id: 1,
  zone: 'A',
  status: 'counting' as const,
  remark: null,
  created_by: 1,
  created_at: '2026-01-01 00:00:00',
  approved_by: null,
  lines: [],
}

describe('stocktakes idempotent actions', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('posts create with Idempotency-Key header', async () => {
    const payload = { warehouse_id: 1, zone: 'A' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: sampleOrder, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await createStocktake(payload)

    expect(apiClient.post).toHaveBeenCalledWith('/stocktakes', payload, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.id).toBe(1)
  })

  it('posts approve with Idempotency-Key header', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: { ...sampleOrder, status: 'approved' }, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await approveStocktake(1)

    expect(apiClient.post).toHaveBeenCalledWith('/stocktakes/1/approve', undefined, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.status).toBe('approved')
  })

  it('posts cancel with Idempotency-Key header', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: { ...sampleOrder, status: 'cancelled' }, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await cancelStocktake(1)

    expect(apiClient.post).toHaveBeenCalledWith('/stocktakes/1/cancel', undefined, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.status).toBe('cancelled')
  })
})
