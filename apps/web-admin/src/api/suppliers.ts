import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  Paginated,
  Supplier,
  SupplierCreate,
  SupplierUpdate,
} from '@/types/api'

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

export async function getSupplier(supplierId: number): Promise<Supplier> {
  return requestData(apiClient.get<ApiEnvelope<Supplier>>(`/suppliers/${supplierId}`))
}

export async function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  return requestData(apiClient.post<ApiEnvelope<Supplier>>('/suppliers', payload))
}

export async function updateSupplier(
  supplierId: number,
  payload: SupplierUpdate,
): Promise<Supplier> {
  return requestData(
    apiClient.patch<ApiEnvelope<Supplier>>(`/suppliers/${supplierId}`, payload),
  )
}

export async function deactivateSupplier(supplierId: number): Promise<Supplier> {
  return requestData(
    apiClient.post<ApiEnvelope<Supplier>>(`/suppliers/${supplierId}/deactivate`),
  )
}
