import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  CountLineInput,
  Paginated,
  StocktakeOrder,
  StocktakeOrderCreate,
  StocktakeOrderListItem,
  StocktakeOrderResult,
} from '@/types/api'
import { createIdempotencyKey } from '@/utils/idempotency'

export interface CancelPayload {
  cancel_reason_code?: string
}

export interface StocktakeListQuery {
  warehouse_id?: number
  status?: string
  page?: number
  page_size?: number
}

export async function listStocktakes(
  query: StocktakeListQuery = {},
): Promise<Paginated<StocktakeOrderListItem>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<StocktakeOrderListItem>>>('/stocktakes', {
      params: query,
    }),
  )
}

export async function getStocktake(orderId: number): Promise<StocktakeOrder> {
  return requestData(
    apiClient.get<ApiEnvelope<StocktakeOrder>>(`/stocktakes/${orderId}`),
  )
}

export async function createStocktake(
  payload: StocktakeOrderCreate,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<StocktakeOrderResult> {
  return requestData(
    apiClient.post<ApiEnvelope<StocktakeOrderResult>>('/stocktakes', payload, {
      headers: { 'Idempotency-Key': idempotencyKey },
    }),
  )
}

export async function recordStocktakeCounts(
  orderId: number,
  lines: CountLineInput[],
): Promise<StocktakeOrder> {
  return requestData(
    apiClient.post<ApiEnvelope<StocktakeOrder>>(`/stocktakes/${orderId}/counts`, {
      lines,
    }),
  )
}

export async function approveStocktake(
  orderId: number,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<StocktakeOrderResult> {
  return requestData(
    apiClient.post<ApiEnvelope<StocktakeOrderResult>>(
      `/stocktakes/${orderId}/approve`,
      undefined,
      { headers: { 'Idempotency-Key': idempotencyKey } },
    ),
  )
}

export async function cancelStocktake(
  orderId: number,
  payload?: CancelPayload,
  idempotencyKey: string = createIdempotencyKey(),
): Promise<StocktakeOrderResult> {
  return requestData(
    apiClient.post<ApiEnvelope<StocktakeOrderResult>>(
      `/stocktakes/${orderId}/cancel`,
      payload ?? {},
      { headers: { 'Idempotency-Key': idempotencyKey } },
    ),
  )
}
