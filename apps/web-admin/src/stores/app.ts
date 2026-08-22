import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const warehouseId = ref<number | null>(null)

  function setWarehouseId(id: number | null): void {
    warehouseId.value = id
  }

  return {
    warehouseId,
    setWarehouseId,
  }
})
