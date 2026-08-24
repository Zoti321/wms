import { describe, expect, it } from 'vitest'

import { unwrapEnvelope } from '@/api/client'
import { ApiError, type ApiEnvelope } from '@/types/api'

describe('unwrapEnvelope', () => {
  it('returns data when code is 0', () => {
    const body: ApiEnvelope<{ id: number }> = {
      code: 0,
      message: 'ok',
      data: { id: 1 },
      traceId: 'trace-1',
    }

    expect(unwrapEnvelope(body)).toEqual({ id: 1 })
  })

  it('throws ApiError when code is non-zero', () => {
    const body: ApiEnvelope = {
      code: 40100,
      message: '未授权',
      data: null,
      traceId: 'trace-2',
    }

    expect(() => unwrapEnvelope(body)).toThrow(ApiError)
    try {
      unwrapEnvelope(body)
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError)
      expect((error as ApiError).code).toBe(40100)
      expect((error as ApiError).message).toBe('未授权')
    }
  })

  it('throws when data is null on success code', () => {
    const body: ApiEnvelope = {
      code: 0,
      message: 'ok',
      data: null,
      traceId: 'trace-3',
    }

    expect(() => unwrapEnvelope(body)).toThrow('响应 data 为空')
  })
})
