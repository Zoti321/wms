import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listWarehouses } from '@/api/warehouses'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import type { Warehouse } from '@/types/api'
import {
  clearStoredWarehouseId,
  getStoredWarehouseId,
  setStoredWarehouseId,
} from '@/utils/warehouseStorage'

export const useAppStore = defineStore('app', () => {
  const warehouseId = ref<number | null>(null)
  const warehouseName = ref<string | null>(null)
  const warehouseReady = ref(false)
  const warehouseOptions = ref<Warehouse[]>([])

  function applyWarehouseSelection(warehouse: Warehouse | null): void {
    if (warehouse == null) {
      warehouseId.value = null
      warehouseName.value = null
      clearStoredWarehouseId()
      return
    }
    warehouseId.value = warehouse.id
    warehouseName.value = warehouse.name
    setStoredWarehouseId(warehouse.id)
  }

  function setWarehouse(id: number | null, name: string | null = null): void {
    warehouseId.value = id
    warehouseName.value = name
    if (id == null) {
      clearStoredWarehouseId()
    } else {
      setStoredWarehouseId(id)
    }
  }

  function warehouseLabel(id: number | null | undefined): string {
    if (id == null) {
      return '—'
    }
    if (warehouseId.value === id && warehouseName.value) {
      return warehouseName.value
    }
    const match = warehouseOptions.value.find((item) => item.id === id)
    return match?.name ?? String(id)
  }

  function clearWarehouse(): void {
    warehouseId.value = null
    warehouseName.value = null
    warehouseOptions.value = []
    warehouseReady.value = false
    clearStoredWarehouseId()
  }

  function selectWarehouse(id: number): void {
    const match = warehouseOptions.value.find((item) => item.id === id)
    if (match == null) {
      return
    }
    applyWarehouseSelection(match)
  }

  function resolveInitialWarehouse(items: Warehouse[]): Warehouse | null {
    if (items.length === 0) {
      return null
    }
    if (items.length === 1) {
      return items[0] ?? null
    }
    const storedId = getStoredWarehouseId()
    if (storedId != null) {
      const stored = items.find((item) => item.id === storedId)
      if (stored != null) {
        return stored
      }
    }
    return items[0] ?? null
  }

  async function ensureWarehouse(): Promise<void> {
    const page = await listWarehouses({
      status: 1,
      selectable: true,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    warehouseOptions.value = page.items
    applyWarehouseSelection(resolveInitialWarehouse(page.items))
    warehouseReady.value = true
  }

  return {
    warehouseId,
    warehouseName,
    warehouseReady,
    warehouseOptions,
    setWarehouse,
    selectWarehouse,
    warehouseLabel,
    clearWarehouse,
    ensureWarehouse,
  }
})
