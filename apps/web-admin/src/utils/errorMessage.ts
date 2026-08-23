import { ApiError } from '@/types/api'

export function errorMessage(error: unknown, fallback = '操作失败'): string {
  if (error instanceof ApiError) {
    return error.message || fallback
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return fallback
}
