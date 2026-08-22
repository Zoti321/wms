export interface ApiEnvelope<T = unknown> {
  code: number
  message: string
  data: T | null
  traceId: string
}

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
