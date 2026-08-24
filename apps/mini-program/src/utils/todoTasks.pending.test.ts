import { describe, expect, it, vi } from 'vitest'

import {
  countInboundPendingLines,
  countOutboundPendingLines,
  enrichPendingLineCounts,
  mergePendingLineCount,
  type TaskCard,
} from '@/utils/todoTasks'

describe('countInboundPendingLines', () => {
  it('counts lines with remain planned minus putaway', () => {
    expect(
      countInboundPendingLines([
        { planned_qty: '10.000', putaway_qty: '10.000' },
        { planned_qty: '5.000', putaway_qty: '1.000' },
        { planned_qty: '2.000', putaway_qty: '0.000' },
      ]),
    ).toBe(2)
  })
})

describe('countOutboundPendingLines', () => {
  it('counts lines with remain allocated minus picked', () => {
    expect(
      countOutboundPendingLines([
        { allocated_qty: '3.000', picked_qty: '3.000' },
        { allocated_qty: '4.000', picked_qty: '1.000' },
      ]),
    ).toBe(1)
  })
})

describe('mergePendingLineCount', () => {
  it('sets pendingLineCount when defined', () => {
    const card: TaskCard = {
      kind: 'inbound',
      orderId: 1,
      orderNo: 'IN',
      status: 'approved',
      orderType: 'purchase',
      updatedAt: '2026-08-24 09:00:00',
    }
    expect(mergePendingLineCount(card, 3).pendingLineCount).toBe(3)
  })

  it('omits pendingLineCount when undefined', () => {
    const card: TaskCard = {
      kind: 'inbound',
      orderId: 1,
      orderNo: 'IN',
      status: 'approved',
      orderType: 'purchase',
      updatedAt: '2026-08-24 09:00:00',
      pendingLineCount: 2,
    }
    const next = mergePendingLineCount(card, undefined)
    expect(next.pendingLineCount).toBeUndefined()
  })
})

describe('enrichPendingLineCounts', () => {
  const cards: TaskCard[] = [
    {
      kind: 'inbound',
      orderId: 1,
      orderNo: 'IN1',
      status: 'approved',
      orderType: 'purchase',
      updatedAt: '2026-08-24 09:00:00',
    },
    {
      kind: 'outbound',
      orderId: 2,
      orderNo: 'OUT2',
      status: 'picking',
      orderType: 'sales',
      updatedAt: '2026-08-24 10:00:00',
    },
    {
      kind: 'inbound',
      orderId: 3,
      orderNo: 'IN3',
      status: 'putaway',
      orderType: 'purchase',
      updatedAt: '2026-08-24 11:00:00',
    },
  ]

  it('fills counts from fetchers and skips failed cards', async () => {
    const fetchInbound = vi.fn(async (id: number) => {
      if (id === 3) {
        throw new Error('fail')
      }
      return {
        lines: [
          { planned_qty: '10.000', putaway_qty: '0.000' },
          { planned_qty: '5.000', putaway_qty: '5.000' },
        ],
      }
    })
    const fetchOutbound = vi.fn(async () => ({
      lines: [{ allocated_qty: '2.000', picked_qty: '0.000' }],
    }))

    const enriched = await enrichPendingLineCounts(cards, {
      fetchInbound,
      fetchOutbound,
      concurrency: 2,
    })

    expect(enriched[0].pendingLineCount).toBe(1)
    expect(enriched[1].pendingLineCount).toBe(1)
    expect(enriched[2].pendingLineCount).toBeUndefined()
    expect(fetchInbound).toHaveBeenCalledTimes(2)
    expect(fetchOutbound).toHaveBeenCalledTimes(1)
  })
})
