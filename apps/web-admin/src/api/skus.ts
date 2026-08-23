import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, Paginated, Sku, SkuCreate, SkuUpdate } from '@/types/api'

export interface SkuListQuery {
  code?: string
  name?: string
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listSkus(query: SkuListQuery = {}): Promise<Paginated<Sku>> {
  return requestData(apiClient.get<ApiEnvelope<Paginated<Sku>>>('/skus', { params: query }))
}

export async function getSku(skuId: number): Promise<Sku> {
  return requestData(apiClient.get<ApiEnvelope<Sku>>(`/skus/${skuId}`))
}

export async function createSku(payload: SkuCreate): Promise<Sku> {
  return requestData(apiClient.post<ApiEnvelope<Sku>>('/skus', payload))
}

export async function updateSku(skuId: number, payload: SkuUpdate): Promise<Sku> {
  return requestData(apiClient.patch<ApiEnvelope<Sku>>(`/skus/${skuId}`, payload))
}

export async function deactivateSku(skuId: number): Promise<Sku> {
  return requestData(apiClient.post<ApiEnvelope<Sku>>(`/skus/${skuId}/deactivate`))
}
