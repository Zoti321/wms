import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
  resolveApiBaseUrl: () => '/api/v1',
}))

vi.mock('@/utils/tokenStorage', () => ({
  getAccessToken: () => 'test-token',
}))

import { apiClient } from '@/api/client'
import { downloadDailyReportCsv, getDailyReport } from '@/api/reports'

describe('reports api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.stubGlobal('fetch', vi.fn())
  })

  it('gets daily report with warehouse and date params', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          warehouse_id: 1,
          business_date: '2026-01-01',
          inbound_order_count: 2,
          putaway_qty: '10.000',
          outbound_order_count: 1,
          picked_qty: '5.000',
          sku_count: 3,
          total_available: '100.000',
          open_alert_count: 0,
        },
        traceId: 't1',
      },
    } as never)

    const result = await getDailyReport({ warehouse_id: 1, business_date: '2026-01-01' })

    expect(apiClient.get).toHaveBeenCalledWith('/reports/daily', {
      params: { warehouse_id: 1, business_date: '2026-01-01' },
    })
    expect(result.inbound_order_count).toBe(2)
  })

  it('downloads daily report csv via fetch with auth header', async () => {
    const blob = new Blob(['csv'], { type: 'text/csv' })
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      blob: async () => blob,
      headers: { get: () => 'text/csv' },
    } as never)

    const result = await downloadDailyReportCsv({
      warehouse_id: 1,
      business_date: '2026-01-01',
    })

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/reports/daily.csv'),
      expect.objectContaining({
        headers: { Authorization: 'Bearer test-token' },
      }),
    )
    expect(result).toBe(blob)
  })
})
