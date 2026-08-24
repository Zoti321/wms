import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
  requestData: vi.fn(async (promise: Promise<unknown>) => {
    const response = (await promise) as { data: { data: unknown } }
    return response.data.data
  }),
}))

import { apiClient } from '@/api/client'
import { createSku, listSkus, updateSku } from '@/api/skus'

describe('skus api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists skus with code filter', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [{ id: 1, sku_code: 'SKU01', name: '物料', unit: '个', safety_stock: '0', status: 1 }],
          total: 1,
          page: 1,
          page_size: 20,
        },
        traceId: 't1',
      },
    } as never)

    await listSkus({ code: 'SKU01', page: 1, page_size: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/skus', {
      params: { code: 'SKU01', page: 1, page_size: 20 },
    })
  })

  it('creates sku via POST /skus', async () => {
    const body = {
      sku_code: 'SKU02',
      name: '新物料',
      unit: '个',
      safety_stock: '10',
    }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, ...body, spec: null, barcode: null, status: 1 },
        traceId: 't1',
      },
    } as never)

    await createSku(body)

    expect(apiClient.post).toHaveBeenCalledWith('/skus', body)
  })

  it('updates sku via PATCH /skus/:id', async () => {
    const body = { name: '物料（更名）' }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          id: 1,
          sku_code: 'SKU01',
          name: '物料（更名）',
          unit: '个',
          safety_stock: '0',
          status: 1,
        },
        traceId: 't1',
      },
    } as never)

    await updateSku(1, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/skus/1', body)
  })
})
