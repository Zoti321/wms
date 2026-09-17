import { requestData } from '@/api/client'
import type {
  OutboundOrder,
  OutboundOrderListItem,
  Paginated,
  PickRequest,
  PickResult,
} from '@/types/api'
import { createIdempotencyKey } from '@/utils/idempotency'

export interface OutboundOrderListQuery {
  warehouse_id?: number
  status?: string
  page?: number
  page_size?: number
}

export async function listOutboundOrders(
  query: OutboundOrderListQuery = {},
): Promise<Paginated<OutboundOrderListItem>> {
  return requestData<Paginated<OutboundOrderListItem>>('/outbound-orders', {
    query: query as Record<string, string | number | boolean | undefined | null>,
  })
}

export async function getOutboundOrder(orderId: number): Promise<OutboundOrder> {
  return requestData<OutboundOrder>(`/outbound-orders/${orderId}`)
}

export async function pickOutboundOrder(
  orderId: number,
  payload: PickRequest,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<PickResult> {
  return requestData<PickResult>(`/outbound-orders/${orderId}/pick`, {
    method: 'POST',
    data: payload,
    headers: { 'Idempotency-Key': idempotencyKey },
  })
}
