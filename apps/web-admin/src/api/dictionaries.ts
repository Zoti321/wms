import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  CreateDictItemRequest,
  DictItem,
  Paginated,
  UpdateDictItemRequest,
} from '@/types/api'

export interface DictListQuery {
  dict_type?: string
  page?: number
  page_size?: number
}

export async function listDictItems(query: DictListQuery = {}): Promise<Paginated<DictItem>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<DictItem>>>('/dictionaries', { params: query }),
  )
}

export async function createDictItem(payload: CreateDictItemRequest): Promise<DictItem> {
  return requestData(apiClient.post<ApiEnvelope<DictItem>>('/dictionaries', payload))
}

export async function updateDictItem(
  itemId: number,
  payload: UpdateDictItemRequest,
): Promise<DictItem> {
  return requestData(
    apiClient.patch<ApiEnvelope<DictItem>>(`/dictionaries/${itemId}`, payload),
  )
}

export async function deactivateDictItem(itemId: number): Promise<DictItem> {
  return requestData(
    apiClient.post<ApiEnvelope<DictItem>>(`/dictionaries/${itemId}/deactivate`),
  )
}
