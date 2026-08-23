import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  InventoryBalance,
  InventoryLedger,
  Paginated,
} from '@/types/api'

export interface InventoryBalanceQuery {
  warehouse_id?: number
  sku_id?: number
  location_id?: number
  page?: number
  page_size?: number
}

export interface InventoryLedgerQuery {
  warehouse_id?: number
  sku_id?: number
  ref_line_id?: number
  ref_id?: number
  ref_type?: string
  page?: number
  page_size?: number
}

export async function listInventoryBalances(
  query: InventoryBalanceQuery = {},
): Promise<Paginated<InventoryBalance>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<InventoryBalance>>>('/inventories', {
      params: query,
    }),
  )
}

export async function listInventoryLedgers(
  query: InventoryLedgerQuery = {},
): Promise<Paginated<InventoryLedger>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<InventoryLedger>>>('/inventories/ledgers', {
      params: query,
    }),
  )
}
