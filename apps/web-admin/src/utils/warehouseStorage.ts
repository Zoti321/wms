const WAREHOUSE_ID_KEY = 'wms_selected_warehouse_id'

export function getStoredWarehouseId(): number | null {
  const raw = sessionStorage.getItem(WAREHOUSE_ID_KEY)
  if (raw == null || raw === '') {
    return null
  }
  const value = Number(raw)
  return Number.isFinite(value) ? value : null
}

export function setStoredWarehouseId(id: number | null): void {
  if (id == null) {
    sessionStorage.removeItem(WAREHOUSE_ID_KEY)
    return
  }
  sessionStorage.setItem(WAREHOUSE_ID_KEY, String(id))
}

export function clearStoredWarehouseId(): void {
  sessionStorage.removeItem(WAREHOUSE_ID_KEY)
}
