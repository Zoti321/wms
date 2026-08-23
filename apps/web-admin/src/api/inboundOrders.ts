import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  InboundOrder,
  InboundOrderCreate,
  InboundOrderListItem,
  InboundOrderUpdate,
  Paginated,
  PutawayRequest,
  PutawayResult,
} from '@/types/api'
import { createIdempotencyKey } from '@/utils/idempotency'

export interface InboundOrderListQuery {
  warehouse_id?: number
  status?: string
  order_no?: string
  order_type?: string
  page?: number
  page_size?: number
}

export async function listInboundOrders(
  query: InboundOrderListQuery = {},
): Promise<Paginated<InboundOrderListItem>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<InboundOrderListItem>>>('/inbound-orders', {
      params: query,
    }),
  )
}

export async function getInboundOrder(orderId: number): Promise<InboundOrder> {
  return requestData(
    apiClient.get<ApiEnvelope<InboundOrder>>(`/inbound-orders/${orderId}`),
  )
}

export async function createInboundOrder(
  payload: InboundOrderCreate,
): Promise<InboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<InboundOrder>>('/inbound-orders', payload),
  )
}

export async function updateInboundOrder(
  orderId: number,
  payload: InboundOrderUpdate,
): Promise<InboundOrder> {
  return requestData(
    apiClient.patch<ApiEnvelope<InboundOrder>>(`/inbound-orders/${orderId}`, payload),
  )
}

export async function submitInboundOrder(orderId: number): Promise<InboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<InboundOrder>>(`/inbound-orders/${orderId}/submit`),
  )
}

export async function approveInboundOrder(orderId: number): Promise<InboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<InboundOrder>>(`/inbound-orders/${orderId}/approve`),
  )
}

export async function cancelInboundOrder(orderId: number): Promise<InboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<InboundOrder>>(`/inbound-orders/${orderId}/cancel`),
  )
}

export async function putawayInboundOrder(
  orderId: number,
  payload: PutawayRequest,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<PutawayResult> {
  return requestData(
    apiClient.post<ApiEnvelope<PutawayResult>>(
      `/inbound-orders/${orderId}/putaway`,
      payload,
      { headers: { 'Idempotency-Key': idempotencyKey } },
    ),
  )
}
