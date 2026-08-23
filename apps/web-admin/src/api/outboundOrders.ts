import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  ApproveRequest,
  ApproveResult,
  CancelResult,
  OutboundOrder,
  OutboundOrderCreate,
  OutboundOrderListItem,
  OutboundOrderUpdate,
  Paginated,
  PickRequest,
  PickResult,
} from '@/types/api'
import { createIdempotencyKey } from '@/utils/idempotency'

export interface OutboundOrderListQuery {
  warehouse_id?: number
  status?: string
  order_no?: string
  order_type?: string
  page?: number
  page_size?: number
}

export async function listOutboundOrders(
  query: OutboundOrderListQuery = {},
): Promise<Paginated<OutboundOrderListItem>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<OutboundOrderListItem>>>('/outbound-orders', {
      params: query,
    }),
  )
}

export async function getOutboundOrder(orderId: number): Promise<OutboundOrder> {
  return requestData(
    apiClient.get<ApiEnvelope<OutboundOrder>>(`/outbound-orders/${orderId}`),
  )
}

export async function createOutboundOrder(
  payload: OutboundOrderCreate,
): Promise<OutboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<OutboundOrder>>('/outbound-orders', payload),
  )
}

export async function updateOutboundOrder(
  orderId: number,
  payload: OutboundOrderUpdate,
): Promise<OutboundOrder> {
  return requestData(
    apiClient.patch<ApiEnvelope<OutboundOrder>>(`/outbound-orders/${orderId}`, payload),
  )
}

export async function submitOutboundOrder(orderId: number): Promise<OutboundOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<OutboundOrder>>(`/outbound-orders/${orderId}/submit`),
  )
}

export async function approveOutboundOrder(
  orderId: number,
  payload: ApproveRequest,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<ApproveResult> {
  return requestData(
    apiClient.post<ApiEnvelope<ApproveResult>>(
      `/outbound-orders/${orderId}/approve`,
      payload,
      { headers: { 'Idempotency-Key': idempotencyKey } },
    ),
  )
}

export async function pickOutboundOrder(
  orderId: number,
  payload: PickRequest,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<PickResult> {
  return requestData(
    apiClient.post<ApiEnvelope<PickResult>>(`/outbound-orders/${orderId}/pick`, payload, {
      headers: { 'Idempotency-Key': idempotencyKey },
    }),
  )
}

export async function cancelOutboundOrder(
  orderId: number,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<CancelResult> {
  return requestData(
    apiClient.post<ApiEnvelope<CancelResult>>(
      `/outbound-orders/${orderId}/cancel`,
      undefined,
      { headers: { 'Idempotency-Key': idempotencyKey } },
    ),
  )
}
