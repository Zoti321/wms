import { apiClient, requestData } from '@/api/client'
import type { ApiEnvelope, OperationLog, Paginated } from '@/types/api'

export interface OperationLogListQuery {
  operator_id?: number
  action?: string
  created_from?: string
  created_to?: string
  page?: number
  page_size?: number
}

export async function listOperationLogs(
  query: OperationLogListQuery = {},
): Promise<Paginated<OperationLog>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<OperationLog>>>('/operation-logs', { params: query }),
  )
}
