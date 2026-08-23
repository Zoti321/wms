import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listWarehouses } from '@/api/warehouses'

export const useAppStore = defineStore('app', () => {
  const warehouseId = ref<number | null>(null)
  const warehouseName = ref<string | null>(null)
  const warehouseReady = ref(false)

  function setWarehouse(id: number | null, name: string | null = null): void {
    warehouseId.value = id
    warehouseName.value = name
  }

  function clearWarehouse(): void {
    warehouseId.value = null
    warehouseName.value = null
    warehouseReady.value = false
  }

  async function ensureWarehouse(): Promise<void> {
    const page = await listWarehouses({
      status: 1,
      selectable: true,
      page: 1,
      page_size: 20,
    })
    if (page.items.length === 1) {
      const sole = page.items[0]
      setWarehouse(sole.id, sole.name)
    } else {
      setWarehouse(null, null)
    }
    warehouseReady.value = true
  }

  return {
    warehouseId,
    warehouseName,
    warehouseReady,
    setWarehouse,
    clearWarehouse,
    ensureWarehouse,
  }
})
