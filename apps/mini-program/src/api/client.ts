import { resolveApiBaseUrl as resolveEnvBase } from '@/config/env'
import { ApiError, type ApiEnvelope } from '@/types/api'
import { clearAccessToken, getAccessToken } from '@/utils/tokenStorage'

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export type QueryParams = Record<string, string | number | boolean | undefined | null>

export interface RequestOptions {
  method?: HttpMethod
  data?: unknown
  query?: QueryParams
  headers?: Record<string, string>
  /** 为 false 时不附带 Authorization（登录） */
  auth?: boolean
}

type UniRequestSuccess = UniApp.RequestSuccessCallbackResult

let onUnauthorized: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  onUnauthorized = handler
}

export function resolveApiBaseUrl(): string {
  const base = resolveEnvBase()
  return base ? `${base}/api/v1` : '/api/v1'
}

function buildUrl(path: string, query?: QueryParams): string {
  const base = resolveApiBaseUrl().replace(/\/$/, '')
  const normalized = path.startsWith('/') ? path : `/${path}`
  const url = `${base}${normalized}`
  if (!query) {
    return url
  }
  const parts: string[] = []
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === null || value === '') {
      continue
    }
    parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  }
  return parts.length ? `${url}?${parts.join('&')}` : url
}

function clearTokenIfUnauthorized(code: number, httpStatus?: number): void {
  if (code === 40100 || httpStatus === 401) {
    clearAccessToken()
    onUnauthorized?.()
  }
}

export function unwrapEnvelope<T>(body: ApiEnvelope<T>, httpStatus?: number): T {
  if (body.code !== 0) {
    clearTokenIfUnauthorized(body.code, httpStatus)
    throw new ApiError(body.code, body.message, body.traceId)
  }
  if (body.data === null) {
    throw new ApiError(body.code, '响应 data 为空', body.traceId)
  }
  return body.data
}

function requestOnce<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? 'GET'
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (options.auth !== false) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: buildUrl(path, options.query),
      method,
      data: options.data as UniApp.RequestOptions['data'],
      header: headers,
      success: (res: UniRequestSuccess) => {
        const status = res.statusCode
        const body = res.data as ApiEnvelope<T> | undefined
        if (!body || typeof body !== 'object' || typeof (body as ApiEnvelope).code !== 'number') {
          if (status === 401) {
            clearAccessToken()
            onUnauthorized?.()
          }
          reject(new Error('网络异常，请重试'))
          return
        }
        try {
          resolve(unwrapEnvelope(body, status))
        } catch (error) {
          reject(error)
        }
      },
      fail: () => {
        reject(new Error('网络异常，请重试'))
      },
    })
  })
}

export async function requestData<T>(path: string, options?: RequestOptions): Promise<T> {
  return requestOnce<T>(path, options)
}
