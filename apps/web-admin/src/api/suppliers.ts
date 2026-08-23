import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, Paginated, Supplier } from '@/types/api'

export interface SupplierListQuery {
  code?: string
  name?: string
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listSuppliers(
  query: SupplierListQuery = {},
): Promise<Paginated<Supplier>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<Supplier>>>('/suppliers', { params: query }),
  )
}
