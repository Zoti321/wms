import { requestData } from '@/api/client'
import type {
  InboundOrder,
  InboundOrderListItem,
  Paginated,
  PutawayRequest,
  PutawayResult,
} from '@/types/api'
import { createIdempotencyKey } from '@/utils/idempotency'

export interface InboundOrderListQuery {
  warehouse_id?: number
  status?: string
  page?: number
  page_size?: number
}

export async function listInboundOrders(
  query: InboundOrderListQuery = {},
): Promise<Paginated<InboundOrderListItem>> {
  return requestData<Paginated<InboundOrderListItem>>('/inbound-orders', {
    query: query as Record<string, string | number | boolean | undefined | null>,
  })
}

export async function getInboundOrder(orderId: number): Promise<InboundOrder> {
  return requestData<InboundOrder>(`/inbound-orders/${orderId}`)
}

export async function putawayInboundOrder(
  orderId: number,
  payload: PutawayRequest,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<PutawayResult> {
  return requestData<PutawayResult>(`/inbound-orders/${orderId}/putaway`, {
    method: 'POST',
    data: payload,
    headers: { 'Idempotency-Key': idempotencyKey },
  })
}
