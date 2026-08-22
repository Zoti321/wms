import type { components } from '@/types/openapi'

export interface ApiEnvelope<T = unknown> {
  code: number
  message: string
  data: T | null
  traceId: string
}

/** OpenAPI 已建模的请求体。 */
export type LoginRequest = components['schemas']['LoginRequest']

/**
 * 登录/当前用户 data 载荷。FastAPI auth 路由以 ok(dict) 返回且未声明 response_model，
 * OpenAPI 中响应为 unknown；待后端补 response_model 后可改为从 openapi.d.ts 提取。
 */
export interface TokenData {
  access_token: string
  token_type: string
}

export interface MeData {
  id: number
  username: string
  role_code: string
  permissions: string[]
}

export class ApiError extends Error {
  readonly code: number
  readonly traceId?: string

  constructor(code: number, message: string, traceId?: string) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.traceId = traceId
  }
}
