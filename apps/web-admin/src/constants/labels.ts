import type { InboundStatus } from '@/types/api'

export const INBOUND_STATUS_LABEL: Record<InboundStatus, string> = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  putaway: '上架中',
  done: '已完成',
  cancelled: '已取消',
}

export const INBOUND_STATUS_TAG_TYPE: Record<
  InboundStatus,
  'info' | 'warning' | 'success' | 'primary' | 'danger'
> = {
  draft: 'info',
  pending: 'warning',
  approved: 'primary',
  putaway: 'warning',
  done: 'success',
  cancelled: 'info',
}

export const INBOUND_ORDER_TYPE_LABEL: Record<string, string> = {
  purchase: '采购入库',
  return: '退货入库',
  other: '其他入库',
}

export const ACTIVE_STATUS_LABEL: Record<number, string> = {
  1: '启用',
  0: '停用',
}

export const SPACE_STATUS_LABEL: Record<string, string> = {
  idle: '空闲',
  occupied: '占用',
  frozen: '冻结',
}
