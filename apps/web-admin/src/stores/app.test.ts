import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/api/warehouses', () => ({
  listWarehouses: vi.fn(),
}))

import * as warehousesApi from '@/api/warehouses'
import { useAppStore } from '@/stores/app'
import {
  clearStoredWarehouseId,
  getStoredWarehouseId,
  setStoredWarehouseId,
} from '@/utils/warehouseStorage'

describe('useAppStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.mocked(warehousesApi.listWarehouses).mockReset()
    clearStoredWarehouseId()
  })

  it('ensureWarehouse selects the sole active warehouse', async () => {
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [{ id: 7, warehouse_code: 'WH01', name: '主仓', status: 1 }],
      total: 1,
      page: 1,
      page_size: 100,
    })

    const app = useAppStore()
    await app.ensureWarehouse()

    expect(warehousesApi.listWarehouses).toHaveBeenCalledWith({
      status: 1,
      selectable: true,
      page: 1,
      page_size: 100,
    })
    expect(app.warehouseId).toBe(7)
    expect(app.warehouseName).toBe('主仓')
    expect(getStoredWarehouseId()).toBe(7)
  })

  it('ensureWarehouse clears context when no active warehouse', async () => {
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 100,
    })

    const app = useAppStore()
    app.setWarehouse(3, '旧仓')
    await app.ensureWarehouse()

    expect(app.warehouseId).toBeNull()
    expect(app.warehouseName).toBeNull()
    expect(getStoredWarehouseId()).toBeNull()
  })

  it('ensureWarehouse restores stored warehouse when multiple are active', async () => {
    setStoredWarehouseId(9)
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [
        { id: 8, warehouse_code: 'WH-A', name: '分仓 A', status: 1 },
        { id: 9, warehouse_code: 'WH-B', name: '分仓 B', status: 1 },
      ],
      total: 2,
      page: 1,
      page_size: 100,
    })

    const app = useAppStore()
    await app.ensureWarehouse()

    expect(app.warehouseId).toBe(9)
    expect(app.warehouseName).toBe('分仓 B')
    expect(app.warehouseOptions).toHaveLength(2)
  })

  it('ensureWarehouse defaults to first warehouse when stored id is invalid', async () => {
    setStoredWarehouseId(999)
    vi.mocked(warehousesApi.listWarehouses).mockResolvedValue({
      items: [
        { id: 8, warehouse_code: 'WH-A', name: '分仓 A', status: 1 },
        { id: 9, warehouse_code: 'WH-B', name: '分仓 B', status: 1 },
      ],
      total: 2,
      page: 1,
      page_size: 100,
    })

    const app = useAppStore()
    await app.ensureWarehouse()

    expect(app.warehouseId).toBe(8)
    expect(app.warehouseName).toBe('分仓 A')
  })

  it('selectWarehouse updates context and session storage', () => {
    const app = useAppStore()
    app.warehouseOptions = [
      { id: 8, warehouse_code: 'WH-A', name: '分仓 A', status: 1 },
      { id: 9, warehouse_code: 'WH-B', name: '分仓 B', status: 1 },
    ]

    app.selectWarehouse(9)

    expect(app.warehouseId).toBe(9)
    expect(app.warehouseName).toBe('分仓 B')
    expect(getStoredWarehouseId()).toBe(9)
  })

  it('warehouseLabel resolves from options when id differs from current', () => {
    const app = useAppStore()
    app.warehouseOptions = [{ id: 8, warehouse_code: 'WH-A', name: '分仓 A', status: 1 }]
    app.setWarehouse(9, '分仓 B')

    expect(app.warehouseLabel(8)).toBe('分仓 A')
    expect(app.warehouseLabel(9)).toBe('分仓 B')
    expect(app.warehouseLabel(null)).toBe('—')
  })

  it('clearWarehouse resets warehouse context', () => {
    const app = useAppStore()
    app.setWarehouse(1, '主仓')
    app.clearWarehouse()
    expect(app.warehouseId).toBeNull()
    expect(app.warehouseName).toBeNull()
    expect(getStoredWarehouseId()).toBeNull()
  })
})
