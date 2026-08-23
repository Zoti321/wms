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

export const INVENTORY_ALERT_STATUS_LABEL: Record<string, string> = {
  open: '预警中',
  cleared: '已解除',
}

export const INVENTORY_ALERT_STATUS_TAG_TYPE: Record<
  string,
  'info' | 'warning' | 'success' | 'primary' | 'danger'
> = {
  open: 'danger',
  cleared: 'success',
}

export const INVENTORY_REF_TYPE_LABEL: Record<string, string> = {
  PUTAWAY: '上架',
  ALLOCATE: '分配',
  PICK: '拣货',
  RELEASE: '释放',
  STOCKTAKE: '盘点',
}

export const ROLE_CODE_LABEL: Record<string, string> = {
  admin: '系统管理员',
  supervisor: '仓库主管',
  operator: '仓管员',
  viewer: '只读用户',
}

export const OPERATION_ACTION_LABEL: Record<string, string> = {
  'auth.login': '登录',
  'user.create': '创建用户',
  'user.deactivate': '停用用户',
  'user.reset_password': '重置密码',
  'dict.create': '创建字典',
  'dict.update': '更新字典',
  'dict.deactivate': '停用字典',
  'inbound.approve': '审核入库',
  'outbound.approve': '审核出库',
  'stocktake.approve': '审核盘点',
}

export const DICT_TYPE_LABEL: Record<string, string> = {
  unit: '计量单位',
  order_type: '单据类型',
  cancel_reason: '取消原因',
}
