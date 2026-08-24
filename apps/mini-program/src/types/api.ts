import type { components } from '@/types/openapi'

export interface ApiEnvelope<T = unknown> {
  code: number
  message: string
  data: T | null
  traceId: string
}

export class ApiError extends Error {
  readonly code: number
  readonly traceId: string

  constructor(code: number, message: string, traceId: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.traceId = traceId
  }
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** OpenAPI 已建模的请求体。 */
export type LoginRequest = components['schemas']['LoginRequest']
export type PutawayRequest = components['schemas']['PutawayRequest']
export type PickRequest = components['schemas']['PickRequest']

/**
 * 登录/业务 data 载荷。FastAPI 路由以 ok(dict) 返回且未声明 response_model，
 * OpenAPI 中响应多为 unknown；字段对齐后端 *_to_dict。
 */
export interface TokenData {
  access_token: string
  token_type: string
}

export interface MeData {
  id: number
  username: string
  role_code: string
  permissions: string[]
}

export interface Warehouse {
  id: number
  warehouse_code: string
  name: string
  status: number
}

export interface Sku {
  id: number
  sku_code: string
  name: string
  unit: string
  status: number
}

export interface Location {
  id: number
  warehouse_id: number
  location_code: string
  zone: string | null
  status: number
}

export type InboundStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'putaway'
  | 'done'
  | 'cancelled'

export type InboundOrderType = 'purchase' | 'return' | 'other'

export interface InboundOrderLine {
  id: number
  sku_id: number
  planned_qty: string
  putaway_qty: string
}

export interface InboundOrderListItem {
  id: number
  order_no: string
  warehouse_id: number
  order_type: InboundOrderType
  status: InboundStatus
  supplier_id: number | null
  created_at: string
}

export interface InboundOrder extends InboundOrderListItem {
  remark: string | null
  created_by: number
  lines: InboundOrderLine[]
}

export interface PutawayResult {
  order: InboundOrder
  putaway_record_id?: number
  replayed?: boolean
}

export type OutboundStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'picking'
  | 'done'
  | 'cancelled'

export type OutboundOrderType = 'sales' | 'material' | 'other'

export interface OutboundOrderLine {
  id: number
  sku_id: number
  planned_qty: string
  allocated_qty: string
  picked_qty: string
  location_id: number | null
}

export interface OutboundOrderListItem {
  id: number
  order_no: string
  warehouse_id: number
  order_type: OutboundOrderType
  status: OutboundStatus
  created_at: string
}

export interface OutboundOrder extends OutboundOrderListItem {
  customer_id: number | null
  remark: string | null
  created_by: number
  lines: OutboundOrderLine[]
}

export interface PickResult {
  order: OutboundOrder
  pick_record_id?: number
  replayed?: boolean
}
