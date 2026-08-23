import type { InboundStatus, OutboundStatus, StocktakeStatus } from '@/types/api'

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

export const OUTBOUND_STATUS_LABEL: Record<OutboundStatus, string> = {
  draft: '草稿',
  pending: '待审核',
  approved: '已审核',
  picking: '拣货中',
  done: '已完成',
  cancelled: '已取消',
}

export const OUTBOUND_STATUS_TAG_TYPE: Record<
  OutboundStatus,
  'info' | 'warning' | 'success' | 'primary' | 'danger'
> = {
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

export const ACTIVE_STATUS_LABEL: Record<number, string> = {
  1: '启用',
  0: '停用',
}

export const SPACE_STATUS_LABEL: Record<string, string> = {
  idle: '空闲',
  occupied: '占用',
  frozen: '冻结',
}

export const STOCKTAKE_STATUS_LABEL: Record<StocktakeStatus, string> = {
  counting: '盘点中',
  approved: '已完成',
  cancelled: '已取消',
}

export const STOCKTAKE_STATUS_TAG_TYPE: Record<
  StocktakeStatus,
  'info' | 'warning' | 'success' | 'primary' | 'danger'
> = {
  counting: 'warning',
  approved: 'success',
  cancelled: 'info',
}
