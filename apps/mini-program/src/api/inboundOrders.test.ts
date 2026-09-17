import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  requestData: vi.fn(),
}))

vi.mock('@/utils/idempotency', () => ({
  createIdempotencyKey: () => 'idem-key-fixed',
}))

import { requestData } from '@/api/client'
import {
  getInboundOrder,
  listInboundOrders,
  putawayInboundOrder,
} from '@/api/inboundOrders'

describe('inboundOrders api', () => {
  beforeEach(() => {
    vi.mocked(requestData).mockReset()
  })

  it('lists with status query', async () => {
    vi.mocked(requestData).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 })
    await listInboundOrders({ status: 'approved', page: 1, page_size: 50 })
    expect(requestData).toHaveBeenCalledWith('/inbound-orders', {
      query: { status: 'approved', page: 1, page_size: 50 },
    })
  })

  it('gets detail by id', async () => {
    vi.mocked(requestData).mockResolvedValue({ id: 1 })
    await getInboundOrder(1)
    expect(requestData).toHaveBeenCalledWith('/inbound-orders/1')
  })

  it('posts putaway with Idempotency-Key', async () => {
    const payload = { line_id: 2, location_id: 9, qty: '1.000' }
    vi.mocked(requestData).mockResolvedValue({ order: { id: 1 }, replayed: false })
    await putawayInboundOrder(1, payload)
    expect(requestData).toHaveBeenCalledWith('/inbound-orders/1/putaway', {
      method: 'POST',
      data: payload,
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
  })
})
