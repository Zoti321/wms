import { requestData } from '@/api/client'
import type { Paginated, Sku, Warehouse } from '@/types/api'

export interface WarehouseListQuery {
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listWarehouses(
  query: WarehouseListQuery = {},
): Promise<Paginated<Warehouse>> {
  return requestData<Paginated<Warehouse>>('/warehouses', {
    query: query as Record<string, string | number | boolean | undefined | null>,
  })
}

export interface SkuListQuery {
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listSkus(query: SkuListQuery = {}): Promise<Paginated<Sku>> {
  return requestData<Paginated<Sku>>('/skus', {
    query: query as Record<string, string | number | boolean | undefined | null>,
  })
}
