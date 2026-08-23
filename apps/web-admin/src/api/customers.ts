import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, Customer, Paginated } from '@/types/api'

export interface CustomerListQuery {
  code?: string
  name?: string
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listCustomers(
  query: CustomerListQuery = {},
): Promise<Paginated<Customer>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<Customer>>>('/customers', { params: query }),
  )
}
