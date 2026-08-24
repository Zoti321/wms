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
  createSupplier,
  deactivateSupplier,
  listSuppliers,
  updateSupplier,
} from '@/api/suppliers'

describe('suppliers api', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset()
    vi.mocked(apiClient.post).mockReset()
    vi.mocked(apiClient.patch).mockReset()
  })

  it('lists suppliers with selectable param', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: {
          items: [{ id: 1, supplier_code: 'SUP01', name: '供应商A', status: 1 }],
          total: 1,
          page: 1,
          page_size: 100,
        },
        traceId: 't1',
      },
    } as never)

    await listSuppliers({ selectable: true, page: 1, page_size: 100 })

    expect(apiClient.get).toHaveBeenCalledWith('/suppliers', {
      params: { selectable: true, page: 1, page_size: 100 },
    })
  })

  it('creates supplier via POST /suppliers', async () => {
    const body = { supplier_code: 'SUP02', name: '供应商B' }
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, ...body, status: 1 },
        traceId: 't1',
      },
    } as never)

    await createSupplier(body)

    expect(apiClient.post).toHaveBeenCalledWith('/suppliers', body)
  })

  it('updates supplier via PATCH /suppliers/:id', async () => {
    const body = { name: '供应商B（更名）' }
    vi.mocked(apiClient.patch).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, supplier_code: 'SUP02', name: '供应商B（更名）', status: 1 },
        traceId: 't1',
      },
    } as never)

    await updateSupplier(2, body)

    expect(apiClient.patch).toHaveBeenCalledWith('/suppliers/2', body)
  })

  it('deactivates supplier via POST /suppliers/:id/deactivate', async () => {
    vi.mocked(apiClient.post).mockResolvedValue({
      data: {
        code: 0,
        message: 'ok',
        data: { id: 2, supplier_code: 'SUP02', name: '供应商B', status: 0 },
        traceId: 't1',
      },
    } as never)

    await deactivateSupplier(2)

    expect(apiClient.post).toHaveBeenCalledWith('/suppliers/2/deactivate')
  })
})
