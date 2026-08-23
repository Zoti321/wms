import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, Paginated, Warehouse } from '@/types/api'

export interface WarehouseListQuery {
  code?: string
  name?: string
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listWarehouses(
  query: WarehouseListQuery = {},
): Promise<Paginated<Warehouse>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<Warehouse>>>('/warehouses', { params: query }),
  )
}
