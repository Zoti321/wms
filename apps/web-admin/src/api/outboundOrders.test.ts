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

vi.mock('@/utils/idempotency', () => ({
  createIdempotencyKey: () => 'idem-key-fixed',
}))

import { apiClient, requestData } from '@/api/client'
import {
  approveOutboundOrder,
  cancelOutboundOrder,
  listOutboundOrders,
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

describe('listOutboundOrders', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(requestData).mockClear()
  })

  it('passes order_no and order_type query params', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { items: [], total: 0, page: 1, page_size: 20 },
        traceId: 't1',
      },
    } as never)

    await listOutboundOrders({
      warehouse_id: 1,
      status: 'pending',
      order_no: 'OUT-001',
      order_type: 'sales',
      page: 1,
      page_size: 20,
    })

    expect(apiClient.get).toHaveBeenCalledWith('/outbound-orders', {
      params: {
        warehouse_id: 1,
        status: 'pending',
        order_no: 'OUT-001',
        order_type: 'sales',
        page: 1,
        page_size: 20,
      },
    })
  })
})

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

    expect(apiClient.post).toHaveBeenCalledWith('/outbound-orders/1/cancel', {}, {
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
    expect(result.order.status).toBe('cancelled')
  })

  it('posts cancel with cancel_reason_code in body', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { order: { ...sampleOrder, status: 'cancelled' }, replayed: false },
        traceId: 't1',
      },
    } as never)

    await cancelOutboundOrder(1, { cancel_reason_code: 'customer_cancel' })

    expect(apiClient.post).toHaveBeenCalledWith(
      '/outbound-orders/1/cancel',
      { cancel_reason_code: 'customer_cancel' },
      { headers: { 'Idempotency-Key': 'idem-key-fixed' } },
    )
  })
})
