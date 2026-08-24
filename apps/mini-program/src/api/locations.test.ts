import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  requestData: vi.fn(),
}))

import { requestData } from '@/api/client'
import { getLocation, listLocations } from '@/api/locations'

describe('locations api', () => {
  beforeEach(() => {
    vi.mocked(requestData).mockReset()
  })

  it('lists with warehouse and code', async () => {
    vi.mocked(requestData).mockResolvedValue({ items: [], total: 0, page: 1, page_size: 20 })
    await listLocations({ warehouse_id: 1, code: 'A-01', page: 1, page_size: 20 })
    expect(requestData).toHaveBeenCalledWith('/locations', {
      query: { warehouse_id: 1, code: 'A-01', page: 1, page_size: 20 },
    })
  })

  it('gets location by id', async () => {
    vi.mocked(requestData).mockResolvedValue({ id: 9, location_code: 'A-01' })
    await getLocation(9)
    expect(requestData).toHaveBeenCalledWith('/locations/9')
  })
})
