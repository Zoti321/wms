import type { InboundStatus, OutboundStatus } from '@/types/api'

export const INBOUND_STATUS_LABEL: Record<InboundStatus, string> = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  putaway: '上架中',
  done: '已完成',
  cancelled: '已取消',
}

export const INBOUND_STATUS_TAG_TYPE: Record<InboundStatus, string> = {
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

export const OUTBOUND_STATUS_LABEL: Record<OutboundStatus, string> = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  picking: '拣货中',
  done: '已完成',
  cancelled: '已取消',
}

export const OUTBOUND_STATUS_TAG_TYPE: Record<OutboundStatus, string> = {
  draft: 'info',
  pending: 'warning',
  approved: 'primary',
  picking: 'warning',
  done: 'success',
  cancelled: 'info',
}

export const OUTBOUND_ORDER_TYPE_LABEL: Record<string, string> = {
  sales: '销售出库',
  material: '领料出库',
  other: '其他出库',
}

export const ROLE_CODE_LABEL: Record<string, string> = {
  admin: '系统管理员',
  supervisor: '仓库主管',
  operator: '仓管员',
  viewer: '只读用户',
}

export function statusLabel(kind: 'inbound' | 'outbound', status: string): string {
  if (kind === 'inbound') {
    return INBOUND_STATUS_LABEL[status as InboundStatus] ?? status
  }
  return OUTBOUND_STATUS_LABEL[status as OutboundStatus] ?? status
}

export function statusTagClass(kind: 'inbound' | 'outbound', status: string): string {
  if (kind === 'inbound') {
    return INBOUND_STATUS_TAG_TYPE[status as InboundStatus] ?? 'info'
  }
  return OUTBOUND_STATUS_TAG_TYPE[status as OutboundStatus] ?? 'info'
}

export function orderTypeLabel(kind: 'inbound' | 'outbound', orderType: string): string {
  if (kind === 'inbound') {
    return INBOUND_ORDER_TYPE_LABEL[orderType] ?? orderType
  }
  return OUTBOUND_ORDER_TYPE_LABEL[orderType] ?? orderType
}
