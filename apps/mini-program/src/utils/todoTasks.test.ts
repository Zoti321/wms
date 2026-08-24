import { describe, expect, it } from 'vitest'

import {
  filterTodoTasks,
  mergeTodoTasks,
  toTaskCard,
  type TaskCard,
} from '@/utils/todoTasks'

describe('toTaskCard', () => {
  it('maps list item fields and uses created_at as updatedAt', () => {
    const card = toTaskCard('inbound', {
      id: 3,
      order_no: 'INB-1',
      status: 'approved',
      order_type: 'purchase',
      created_at: '2026-08-24 10:00:00',
    })
    expect(card).toEqual({
      kind: 'inbound',
      orderId: 3,
      orderNo: 'INB-1',
      status: 'approved',
      orderType: 'purchase',
      updatedAt: '2026-08-24 10:00:00',
    })
  })
})

describe('mergeTodoTasks', () => {
  it('sorts by updatedAt descending then orderId', () => {
    const cards: TaskCard[] = [
      {
        kind: 'inbound',
        orderId: 1,
        orderNo: 'A',
        status: 'approved',
        orderType: 'purchase',
        updatedAt: '2026-08-24 09:00:00',
      },
      {
        kind: 'outbound',
        orderId: 9,
        orderNo: 'B',
        status: 'picking',
        orderType: 'sales',
        updatedAt: '2026-08-24 11:00:00',
      },
      {
        kind: 'inbound',
        orderId: 2,
        orderNo: 'C',
        status: 'putaway',
        orderType: 'purchase',
        updatedAt: '2026-08-24 11:00:00',
      },
    ]
    expect(mergeTodoTasks(cards).map((c) => c.orderNo)).toEqual(['B', 'C', 'A'])
  })
})

describe('filterTodoTasks', () => {
  const cards: TaskCard[] = [
    {
      kind: 'inbound',
      orderId: 1,
      orderNo: 'IN',
      status: 'approved',
      orderType: 'purchase',
      updatedAt: '2026-08-24 09:00:00',
    },
    {
      kind: 'outbound',
      orderId: 2,
      orderNo: 'OUT',
      status: 'approved',
      orderType: 'sales',
      updatedAt: '2026-08-24 10:00:00',
    },
  ]

  it('returns all when filter is all', () => {
    expect(filterTodoTasks(cards, 'all')).toHaveLength(2)
  })

  it('filters by kind', () => {
    expect(filterTodoTasks(cards, 'inbound').map((c) => c.orderNo)).toEqual(['IN'])
    expect(filterTodoTasks(cards, 'outbound').map((c) => c.orderNo)).toEqual(['OUT'])
  })
})
