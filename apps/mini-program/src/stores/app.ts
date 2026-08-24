import { defineStore } from 'pinia'
import { ref } from 'vue'

import { listWarehouses } from '@/api/catalog'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'

export const useAppStore = defineStore('app', () => {
  const warehouseId = ref<number | null>(null)
  const warehouseName = ref<string | null>(null)

  function clearWarehouse(): void {
    warehouseId.value = null
    warehouseName.value = null
  }

  async function ensureWarehouse(): Promise<void> {
    const page = await listWarehouses({
      status: 1,
      selectable: true,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    const first = page.items[0]
    if (first) {
      warehouseId.value = first.id
      warehouseName.value = first.name
    } else {
      clearWarehouse()
    }
  }

  return {
    warehouseId,
    warehouseName,
    clearWarehouse,
    ensureWarehouse,
  }
})
