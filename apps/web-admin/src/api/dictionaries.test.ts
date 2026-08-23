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
import {
  createDictItem,
  deactivateDictItem,
  listDictItems,
  updateDictItem,
} from '@/api/dictionaries'

describe('dictionaries api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists dictionaries with dict_type filter', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [
            {
              id: 1,
              dict_type: 'inbound_order_type',
              code: 'purchase',
              name: '采购入库',
              sort_order: 1,
              status: 1,
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        },
        traceId: 't1',
      },
    } as never)

    await listDictItems({ dict_type: 'inbound_order_type', page: 1, page_size: 20 })

    expect(apiClient.get).toHaveBeenCalledWith('/dictionaries', {
      params: { dict_type: 'inbound_order_type', page: 1, page_size: 20 },
    })
  })

  it('creates dictionary item', async () => {
    const body = { dict_type: 'unit', code: 'BOX', name: '箱', sort_order: 1 }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: { code: 0, message: 'ok', data: { id: 2, ...body, status: 1 }, traceId: 't1' },
    } as never)

    await createDictItem(body)

    expect(apiClient.post).toHaveBeenCalledWith('/dictionaries', body)
  })

  it('updates dictionary item', async () => {
    const body = { name: '箱（大）', sort_order: 2 }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          id: 2,
          dict_type: 'unit',
          code: 'BOX',
          name: '箱（大）',
          sort_order: 2,
          status: 1,
        },
        traceId: 't1',
      },
    } as never)

    await updateDictItem(2, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/dictionaries/2', body)
  })

  it('deactivates dictionary item', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          id: 2,
          dict_type: 'unit',
          code: 'BOX',
          name: '箱',
          sort_order: 1,
          status: 0,
        },
        traceId: 't1',
      },
    } as never)

    await deactivateDictItem(2)

    expect(apiClient.post).toHaveBeenCalledWith('/dictionaries/2/deactivate')
  })
})
