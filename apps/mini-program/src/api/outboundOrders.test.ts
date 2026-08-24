import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  requestData: vi.fn(),
}))

vi.mock('@/utils/idempotency', () => ({
  createIdempotencyKey: () => 'idem-key-fixed',
}))

import { requestData } from '@/api/client'
import {
  getOutboundOrder,
  listOutboundOrders,
  pickOutboundOrder,
} from '@/api/outboundOrders'

describe('outboundOrders api', () => {
  beforeEach(() => {
    vi.mocked(requestData).mockReset()
  })

  it('lists with status query', async () => {
    vi.mocked(requestData).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 50 })
    await listOutboundOrders({ status: 'picking', page: 1, page_size: 50 })
    expect(requestData).toHaveBeenCalledWith('/outbound-orders', {
      query: { status: 'picking', page: 1, page_size: 50 },
    })
  })

  it('gets detail by id', async () => {
    vi.mocked(requestData).mockResolvedValue({ id: 2 })
    await getOutboundOrder(2)
    expect(requestData).toHaveBeenCalledWith('/outbound-orders/2')
  })

  it('posts pick with Idempotency-Key', async () => {
    const payload = { line_id: 3, location_id: 8, qty: '2.000' }
    vi.mocked(requestData).mockResolvedValue({ order: { id: 2 }, replayed: false })
    await pickOutboundOrder(2, payload)
    expect(requestData).toHaveBeenCalledWith('/outbound-orders/2/pick', {
      method: 'POST',
      data: payload,
      headers: { 'Idempotency-Key': 'idem-key-fixed' },
    })
  })
})
