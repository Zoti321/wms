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
