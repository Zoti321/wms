import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

import { apiClient } from '@/api/client'
import { createLocation, listLocations } from '@/api/locations'

describe('locations api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists locations for warehouse', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [
            {
              id: 1,
              warehouse_id: 1,
              location_code: 'A-01-01',
              zone: 'A',
              aisle: '01',
              bin: '01',
              space_status: 'idle',
              status: 1,
            },
          ],
          total: 1,
          page: 1,
          page_size: 100,
        },
        traceId: 't1',
      },
    } as never)

    await listLocations({ warehouse_id: 1, selectable: true, page: 1, page_size: 100 })

    expect(apiClient.get).toHaveBeenCalledWith('/locations', {
      params: { warehouse_id: 1, selectable: true, page: 1, page_size: 100 },
    })
  })

  it('creates location via POST /locations', async () => {
    const body = {
      warehouse_id: 1,
      location_code: 'A-01-02',
      zone: 'A',
      aisle: '01',
      bin: '02',
    }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          id: 2,
          ...body,
          space_status: 'idle',
          status: 1,
        },
        traceId: 't1',
      },
    } as never)

    await createLocation(body)

    expect(apiClient.post).toHaveBeenCalledWith('/locations', body)
  })
})
