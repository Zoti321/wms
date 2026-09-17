import { requestData } from '@/api/client'
import type { Location, Paginated } from '@/types/api'

export interface LocationListQuery {
  warehouse_id?: number
  code?: string
  status?: number
  selectable?: boolean
  page?: number
  page_size?: number
}

export async function listLocations(
  query: LocationListQuery = {},
): Promise<Paginated<Location>> {
  return requestData<Paginated<Location>>('/locations', {
    query: query as Record<string, string | number | boolean | undefined | null>,
  })
}

export async function getLocation(locationId: number): Promise<Location> {
  return requestData<Location>(`/locations/${locationId}`)
}
