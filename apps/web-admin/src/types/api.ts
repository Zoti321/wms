import type { components } from '@/types/openapi'

export interface ApiEnvelope<T = unknown> {
  code: number
  message: string
  data: T | null
  traceId: string
}

export interface Paginated<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** OpenAPI 已建模的请求体。 */
export type LoginRequest = components['schemas']['LoginRequest']
export type SkuCreate = components['schemas']['SkuCreate']
export type SkuUpdate = components['schemas']['SkuUpdate']
export type LocationCreate = components['schemas']['LocationCreate']
export type LocationUpdate = components['schemas']['LocationUpdate']
export type InboundOrderCreate = components['schemas']['InboundOrderCreate']
export type InboundOrderUpdate = components['schemas']['InboundOrderUpdate']
export type InboundLineInput = components['schemas']['InboundLineInput']
export type PutawayRequest = components['schemas']['PutawayRequest']
export type OutboundOrderCreate = components['schemas']['OutboundOrderCreate']
export type OutboundOrderUpdate = components['schemas']['OutboundOrderUpdate']
export type OutboundLineInput = components['schemas']['OutboundLineInput']
export type ApproveRequest = components['schemas']['ApproveRequest']
export type AllocationInput = components['schemas']['AllocationInput']
export type PickRequest = components['schemas']['PickRequest']
export type StocktakeOrderCreate = components['schemas']['StocktakeOrderCreate']
export type CountLineInput = components['schemas']['CountLineInput']

/**
 * 登录/业务 data 载荷。FastAPI 路由以 ok(dict) 返回且未声明 response_model，
 * OpenAPI 中响应多为 unknown；字段对齐后端 *_to_dict，缺口另开后端 issue。
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
  spec: string | null
  barcode: string | null
  safety_stock: string
  status: number
}

export interface Location {
  id: number
  warehouse_id: number
  location_code: string
  zone: string | null
  aisle: string | null
  bin: string | null
  space_status: 'idle' | 'occupied' | 'frozen'
  status: number
}

export interface Supplier {
  id: number
  supplier_code: string
  name: string
  status: number
}

export interface Customer {
  id: number
  customer_code: string
  name: string
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
  increase?: unknown
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

export interface ApproveResult {
  order: OutboundOrder
  replayed?: boolean
}

export interface PickResult {
  order: OutboundOrder
  pick_record_id?: number
  deduct?: unknown
  replayed?: boolean
}

export interface CancelResult {
  order: OutboundOrder
  note?: string | null
  replayed?: boolean
}

export type StocktakeStatus = 'counting' | 'approved' | 'cancelled'

export interface StocktakeOrderLine {
  id: number
  location_id: number
  sku_id: number
  book_qty: string
  counted_qty: string | null
  diff_qty: string | null
}

export interface StocktakeOrderListItem {
  id: number
  order_no: string
  warehouse_id: number
  status: StocktakeStatus
  created_at: string
}

export interface StocktakeOrder extends StocktakeOrderListItem {
  zone: string | null
  remark: string | null
  created_by: number
  approved_by: number | null
  lines: StocktakeOrderLine[]
}

export interface StocktakeOrderResult {
  order: StocktakeOrder
  replayed?: boolean
}

export interface InventoryBalance {
  id: number
  warehouse_id: number
  sku_id: number
  location_id: number
  qty_on_hand: string
  qty_frozen: string
  qty_available: string
  version: number
}

export interface InventoryLedger {
  id: number
  warehouse_id: number
  sku_id: number
  location_id: number
  change_qty: string
  bal_qty: string
  ref_type: string
  ref_id: number | null
  ref_line_id: number | null
  ref_no: string | null
  operator_id: number | null
  created_at: string
}

export type InventoryAlertStatus = 'open' | 'cleared'

export interface InventoryAlert {
  id: number
  warehouse_id: number
  sku_id: number
  qty_available: string
  safety_stock: string
  status: InventoryAlertStatus
  created_at: string
}

export class ApiError extends Error {
  readonly code: number
  readonly traceId?: string

  constructor(code: number, message: string, traceId?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.traceId = traceId
  }
}
