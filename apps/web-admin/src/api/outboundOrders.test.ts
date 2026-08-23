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
  approveOutboundOrder,
  cancelOutboundOrder,
  pickOutboundOrder,
} from '@/api/outboundOrders'

const sampleOrder = {
  id: 1,
  order_no: 'OUT-1',
  warehouse_id: 1,
  order_type: 'sales' as const,
  status: 'approved' as const,
  customer_id: null,
  remark: null,
  created_by: 1,
  created_at: '2026-01-01 00:00:00',
  lines: [],
}

describe('outboundOrders idempotent actions', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('posts approve with allocations body and Idempotency-Key header', async () => {
    const payload = { allocations: [{ line_id: 2, location_id: 9 }] }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: sampleOrder, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await approveOutboundOrder(1, payload)

    expect(apiClient.post).toHaveBeenCalledWith('/outbound-orders/1/approve', payload, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.id).toBe(1)
  })

  it('posts pick with Idempotency-Key header', async () => {
    const payload = { line_id: 2, location_id: 9, qty: '1.000' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: sampleOrder, pick_record_id: 11, replayed: false },
        traceId: 't1',
      },
    } as never)

    const result = await pickOutboundOrder(1, payload)

    expect(apiClient.post).toHaveBeenCalledWith('/outbound-orders/1/pick', payload, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.pick_record_id).toBe(11)
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

    const result = await cancelOutboundOrder(1)

    expect(apiClient.post).toHaveBeenCalledWith('/outbound-orders/1/cancel', undefined, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.status).toBe('cancelled')
  })
})
