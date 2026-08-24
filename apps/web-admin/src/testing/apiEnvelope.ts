import type { ApiEnvelope } from '@/types/api'

export function apiEnvelope<T>(data: T, traceId = 'test-trace'): ApiEnvelope<T> {
  return {
    code: 0,
    message: 'ok',
    data,
    traceId,
  }
}
