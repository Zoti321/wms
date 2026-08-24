import axios, {
  type AxiosInstance,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'

import { ApiError, type ApiEnvelope } from '@/types/api'
import { notifyUnauthorized } from '@/api/unauthorized'
import { clearAccessToken, getAccessToken } from '@/utils/tokenStorage'

export function unwrapEnvelope<T>(body: ApiEnvelope<T>): T {
  if (body.code !== 0) {
    throw new ApiError(body.code, body.message, body.traceId)
  }
  if (body.data === null) {
    throw new ApiError(body.code, '响应 data 为空', body.traceId)
  }
  return body.data
}

function resolveApiBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL?.trim() ?? ''
  return base ? `${base.replace(/\/$/, '')}/api/v1` : '/api/v1'
}

export { resolveApiBaseUrl }

function clearTokenIfUnauthorized(code: number, httpStatus?: number): void {
  if (code === 40100 || httpStatus === 401) {
    clearAccessToken()
    notifyUnauthorized()
  }
}

function throwApiError(payload: ApiEnvelope, httpStatus?: number): never {
  clearTokenIfUnauthorized(payload.code, httpStatus)
  throw new ApiError(payload.code, payload.message, payload.traceId)
}

export function createApiClient(): AxiosInstance {
  const client = axios.create({
    baseURL: resolveApiBaseUrl(),
    headers: {
      'Content-Type': 'application/json',
    },
  })

  client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  client.interceptors.response.use(
    (response: AxiosResponse<ApiEnvelope>) => {
      const payload = response.data
      if (payload.code !== 0) {
        throwApiError(payload, response.status)
      }
      return response
    },
    (error) => {
      const payload = error.response?.data as ApiEnvelope | undefined
      if (payload && typeof payload.code === 'number') {
        throwApiError(payload, error.response?.status)
      }
      throw error
    },
  )

  return client
}

export const apiClient = createApiClient()

export async function requestData<T>(
  request: Promise<AxiosResponse<ApiEnvelope<T>>>,
): Promise<T> {
  const response = await request
  return unwrapEnvelope(response.data)
}
