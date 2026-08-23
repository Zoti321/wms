import type { Location, Sku } from '@/types/api'

export function skuOptionLabel(sku: Pick<Sku, 'sku_code' | 'name'>): string {
  return `${sku.sku_code} · ${sku.name}`
}

export function buildSkuLabelById(skus: Sku[]): Map<number, string> {
  const map = new Map<number, string>()
  for (const sku of skus) {
    map.set(sku.id, skuOptionLabel(sku))
  }
  return map
}

export function buildLocationCodeById(locations: Location[]): Map<number, string> {
  const map = new Map<number, string>()
  for (const location of locations) {
    map.set(location.id, location.location_code)
  }
  return map
}

export function labelFromMap(map: Map<number, string>, id: number): string {
  return map.get(id) ?? String(id)
}
