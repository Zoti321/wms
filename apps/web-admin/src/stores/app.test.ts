import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/warehouses', () => ({
  listWarehouses: vi.fn(),
}))

import * as warehousesApi from '@/api/warehouses'
import { useAppStore } from '@/stores/app'

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(warehousesApi.listWarehouses).mockReset()
  })

  it('ensureWarehouse selects the sole active warehouse', async () => {
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [{ id: 7, warehouse_code: 'WH01', name: '主仓', status: 1 }],
      total: 1,
      page: 1,
      page_size: 20,
    })

    const app = useAppStore()
    await app.ensureWarehouse()

    expect(warehousesApi.listWarehouses).toHaveBeenCalledWith({
      status: 1,
      selectable: true,
      page: 1,
      page_size: 20,
    })
    expect(app.warehouseId).toBe(7)
    expect(app.warehouseName).toBe('主仓')
  })

  it('ensureWarehouse clears context when no active warehouse', async () => {
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    const app = useAppStore()
    app.setWarehouse(3, '旧仓')
    await app.ensureWarehouse()

    expect(app.warehouseId).toBeNull()
    expect(app.warehouseName).toBeNull()
  })

  it('clearWarehouse resets warehouse context', () => {
    const app = useAppStore()
    app.setWarehouse(1, '主仓')
    app.clearWarehouse()
    expect(app.warehouseId).toBeNull()
    expect(app.warehouseName).toBeNull()
  })
})
