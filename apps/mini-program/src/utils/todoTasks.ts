import { remainQty } from '@/utils/qty'

export type TaskKind = 'inbound' | 'outbound'
export type TaskFilter = 'all' | TaskKind

export interface TaskCard {
  kind: TaskKind
  orderId: number
  orderNo: string
  status: string
  orderType: string
  /** 用于排序与展示；列表 API 当前为 created_at */
  updatedAt: string
  pendingLineCount?: number
}

export interface OrderListItemLike {
  id: number
  order_no: string
  status: string
  order_type: string
  created_at: string
}

export function toTaskCard(kind: TaskKind, item: OrderListItemLike): TaskCard {
  return {
    kind,
    orderId: item.id,
    orderNo: item.order_no,
    status: item.status,
    orderType: item.order_type,
    updatedAt: item.created_at,
  }
}

/** 合并多路待办列表，按时间降序。 */
export function mergeTodoTasks(cards: TaskCard[]): TaskCard[] {
  return [...cards].sort((a, b) => {
    if (a.updatedAt === b.updatedAt) {
      return b.orderId - a.orderId
    }
    return a.updatedAt < b.updatedAt ? 1 : -1
  })
}

export function filterTodoTasks(cards: TaskCard[], filter: TaskFilter): TaskCard[] {
  if (filter === 'all') {
    return cards
  }
  return cards.filter((card) => card.kind === filter)
}

export function countInboundPendingLines(
  lines: Array<{ planned_qty: string; putaway_qty: string }>,
): number {
  return lines.filter((line) => Number(remainQty(line.planned_qty, line.putaway_qty)) > 0).length
}

export function countOutboundPendingLines(
  lines: Array<{ allocated_qty: string; picked_qty: string }>,
): number {
  return lines.filter((line) => Number(remainQty(line.allocated_qty, line.picked_qty)) > 0)
    .length
}

export function mergePendingLineCount(
  card: TaskCard,
  pendingLineCount: number | undefined,
): TaskCard {
  if (pendingLineCount === undefined) {
    const { pendingLineCount: _drop, ...rest } = card
    return rest
  }
  return { ...card, pendingLineCount }
}

export interface EnrichPendingFetchers {
  fetchInbound: (orderId: number) => Promise<{
    lines: Array<{ planned_qty: string; putaway_qty: string }>
  }>
  fetchOutbound: (orderId: number) => Promise<{
    lines: Array<{ allocated_qty: string; picked_qty: string }>
  }>
  concurrency?: number
}

/** 有界并发拉详情补全 pendingLineCount；单卡失败则该卡不带行数。 */
export async function enrichPendingLineCounts(
  cards: TaskCard[],
  options: EnrichPendingFetchers,
): Promise<TaskCard[]> {
  const concurrency = Math.max(1, options.concurrency ?? 5)
  const results = cards.map((card) => ({ ...card }))
  let nextIndex = 0

  async function worker(): Promise<void> {
    while (nextIndex < cards.length) {
      const index = nextIndex
      nextIndex += 1
      const card = cards[index]
      try {
        if (card.kind === 'inbound') {
          const order = await options.fetchInbound(card.orderId)
          results[index] = mergePendingLineCount(
            results[index],
            countInboundPendingLines(order.lines),
          )
        } else {
          const order = await options.fetchOutbound(card.orderId)
          results[index] = mergePendingLineCount(
            results[index],
            countOutboundPendingLines(order.lines),
          )
        }
      } catch {
        results[index] = mergePendingLineCount(results[index], undefined)
      }
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, cards.length) }, () => worker())
  await Promise.all(workers)
  return results
}
