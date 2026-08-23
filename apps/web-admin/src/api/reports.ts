import { apiClient, requestData, resolveApiBaseUrl } from '@/api/client'
import { notifyUnauthorized } from '@/api/unauthorized'
import { ApiError, type ApiEnvelope, type DailyReport } from '@/types/api'
import { clearAccessToken, getAccessToken } from '@/utils/tokenStorage'

export interface DailyReportQuery {
  warehouse_id: number
  business_date: string
}

export async function getDailyReport(query: DailyReportQuery): Promise<DailyReport> {
  return requestData(
    apiClient.get<ApiEnvelope<DailyReport>>('/reports/daily', { params: query }),
  )
}

export async function downloadDailyReportCsv(query: DailyReportQuery): Promise<Blob> {
  const url = new URL(`${resolveApiBaseUrl()}/reports/daily.csv`, window.location.origin)
  url.searchParams.set('warehouse_id', String(query.warehouse_id))
  url.searchParams.set('business_date', query.business_date)

  const token = getAccessToken()
  const response = await fetch(url.toString(), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (response.status === 401) {
    clearAccessToken()
    notifyUnauthorized()
    throw new ApiError(40100, '未授权')
  }

  if (!response.ok) {
    const contentType = response.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      const body = (await response.json()) as ApiEnvelope
      throw new ApiError(body.code, body.message, body.traceId)
    }
    throw new ApiError(response.status, '导出日报失败')
  }

  return response.blob()
}
