import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  Customer,
  CustomerCreate,
  CustomerUpdate,
  Paginated,
} from '@/types/api'

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

export async function getCustomer(customerId: number): Promise<Customer> {
  return requestData(apiClient.get<ApiEnvelope<Customer>>(`/customers/${customerId}`))
}

export async function createCustomer(payload: CustomerCreate): Promise<Customer> {
  return requestData(apiClient.post<ApiEnvelope<Customer>>('/customers', payload))
}

export async function updateCustomer(
  customerId: number,
  payload: CustomerUpdate,
): Promise<Customer> {
  return requestData(
    apiClient.patch<ApiEnvelope<Customer>>(`/customers/${customerId}`, payload),
  )
}

export async function deactivateCustomer(customerId: number): Promise<Customer> {
  return requestData(
    apiClient.post<ApiEnvelope<Customer>>(`/customers/${customerId}/deactivate`),
  )
}
