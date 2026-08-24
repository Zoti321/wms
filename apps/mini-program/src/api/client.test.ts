import { beforeEach, describe, expect, it, vi } from 'vitest'

const storage = new Map<string, string>()
const requestMock = vi.fn()

vi.stubGlobal('uni', {
  getStorageSync: (key: string) => storage.get(key) ?? '',
  setStorageSync: (key: string, value: string) => storage.set(key, value),
  removeStorageSync: (key: string) => storage.delete(key),
  request: requestMock,
})

vi.mock('@/config/env', () => ({
  resolveApiBaseUrl: () => 'https://api.example.com',
}))

import { ApiError } from '@/types/api'
import { setAccessToken } from '@/utils/tokenStorage'
import { requestData, resolveApiBaseUrl, setUnauthorizedHandler } from '@/api/client'

describe('resolveApiBaseUrl', () => {
  it('appends /api/v1', () => {
    expect(resolveApiBaseUrl()).toBe('https://api.example.com/api/v1')
  })
})

describe('requestData', () => {
  beforeEach(() => {
    storage.clear()
    requestMock.mockReset()
    setUnauthorizedHandler(null)
  })

  it('injects Authorization and unwraps envelope data', async () => {
    setAccessToken('tok')
    requestMock.mockImplementation(({ success }: { success: (r: unknown) => void }) => {
      success({
        statusCode: 200,
        data: { code: 0, message: 'ok', data: { id: 1 }, traceId: 't1' },
      })
    })

    const data = await requestData<{ id: number }>('/auth/me')
    expect(data).toEqual({ id: 1 })
    expect(requestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        url: 'https://api.example.com/api/v1/auth/me',
        method: 'GET',
        header: expect.objectContaining({ Authorization: 'Bearer tok' }),
      }),
    )
  })

  it('throws ApiError and clears token on 40100', async () => {
    setAccessToken('tok')
    const unauthorized = vi.fn()
    setUnauthorizedHandler(unauthorized)
    requestMock.mockImplementation(({ success }: { success: (r: unknown) => void }) => {
      success({
        statusCode: 200,
        data: { code: 40100, message: '未登录', data: null, traceId: 't2' },
      })
    })

    await expect(requestData('/auth/me')).rejects.toBeInstanceOf(ApiError)
    expect(storage.has('wms_access_token')).toBe(false)
    expect(unauthorized).toHaveBeenCalled()
  })

  it('serializes query params', async () => {
    requestMock.mockImplementation(({ success }: { success: (r: unknown) => void }) => {
      success({
        statusCode: 200,
        data: { code: 0, message: 'ok', data: { items: [] }, traceId: 't3' },
      })
    })

    await requestData('/inbound-orders', {
      query: { status: 'approved', page: 1, page_size: 50 },
    })

    expect(requestMock.mock.calls[0][0].url).toContain('status=approved')
    expect(requestMock.mock.calls[0][0].url).toContain('page_size=50')
  })
})
