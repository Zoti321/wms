import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    post: vi.fn(),
    patch: vi.fn(),
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
import { putawayInboundOrder, updateInboundOrder } from '@/api/inboundOrders'

describe('putawayInboundOrder', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('posts putaway with Idempotency-Key header', async () => {
    const payload = { line_id: 2, location_id: 9, qty: '1.000' }
    const order = {
      id: 1,
      order_no: 'INB-1',
      warehouse_id: 1,
      order_type: 'purchase' as const,
      status: 'putaway',
      supplier_id: null,
      remark: null,
      created_by: 1,
      created_at: '2026-01-01 00:00:00',
      lines: [],
    }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order, putaway_record_id: 11, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await putawayInboundOrder(1, payload)

    expect(apiClient.post).toHaveBeenCalledWith('/inbound-orders/1/putaway', payload, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.id).toBe(1)
    expect(result.putaway_record_id).toBe(11)
  })
})

describe('updateInboundOrder', () => {
  beforeEach(() => {
    vi.mocked(apiClient.patch).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('patches inbound order with payload', async () => {
    const payload = {
      supplier_id: 3,
      remark: 'updated',
      lines: [{ sku_id: 10, planned_qty: '5.000' }],
    }
    const order = {
      id: 1,
      order_no: 'INB-1',
      warehouse_id: 1,
      order_type: 'purchase' as const,
      status: 'draft' as const,
      supplier_id: 3,
      remark: 'updated',
      created_by: 1,
      created_at: '2026-01-01 00:00:00',
      lines: [],
    }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: order,
        traceId: 't1',
      },
    } as never)

    const result = await updateInboundOrder(1, payload)

    expect(apiClient.patch).toHaveBeenCalledWith('/inbound-orders/1', payload)
    expect(result.id).toBe(1)
    expect(result.remark).toBe('updated')
  })
})
