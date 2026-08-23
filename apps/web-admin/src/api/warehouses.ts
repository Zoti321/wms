import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  Paginated,
  Warehouse,
  WarehouseCreate,
  WarehouseUpdate,
} from '@/types/api'

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

export async function getWarehouse(warehouseId: number): Promise<Warehouse> {
  return requestData(apiClient.get<ApiEnvelope<Warehouse>>(`/warehouses/${warehouseId}`))
}

export async function createWarehouse(payload: WarehouseCreate): Promise<Warehouse> {
  return requestData(apiClient.post<ApiEnvelope<Warehouse>>('/warehouses', payload))
}

export async function updateWarehouse(
  warehouseId: number,
  payload: WarehouseUpdate,
): Promise<Warehouse> {
  return requestData(
    apiClient.patch<ApiEnvelope<Warehouse>>(`/warehouses/${warehouseId}`, payload),
  )
}

export async function deactivateWarehouse(warehouseId: number): Promise<Warehouse> {
  return requestData(
    apiClient.post<ApiEnvelope<Warehouse>>(`/warehouses/${warehouseId}/deactivate`),
  )
}
