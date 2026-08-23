import { apiClient, requestData } from '@/api/client'
import type {
  ApiEnvelope,
  Location,
  LocationCreate,
  LocationUpdate,
  Paginated,
} from '@/types/api'

export interface LocationListQuery {
  warehouse_id?: number
  code?: string
  status?: number
  space_status?: string
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listLocations(
  query: LocationListQuery = {},
): Promise<Paginated<Location>> {
  return requestData(
    apiClient.get<ApiEnvelope<Paginated<Location>>>('/locations', { params: query }),
  )
}

export async function getLocation(locationId: number): Promise<Location> {
  return requestData(apiClient.get<ApiEnvelope<Location>>(`/locations/${locationId}`))
}

export async function createLocation(payload: LocationCreate): Promise<Location> {
  return requestData(apiClient.post<ApiEnvelope<Location>>('/locations', payload))
}

export async function updateLocation(
  locationId: number,
  payload: LocationUpdate,
): Promise<Location> {
  return requestData(
    apiClient.patch<ApiEnvelope<Location>>(`/locations/${locationId}`, payload),
  )
}

export async function deactivateLocation(locationId: number): Promise<Location> {
  return requestData(
    apiClient.post<ApiEnvelope<Location>>(`/locations/${locationId}/deactivate`),
  )
}
