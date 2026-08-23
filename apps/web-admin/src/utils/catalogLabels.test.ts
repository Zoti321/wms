import { describe, expect, it } from 'vitest'

import type { Location, Sku } from '@/types/api'
import {
  buildLocationCodeById,
  buildSkuLabelById,
  labelFromMap,
  skuOptionLabel,
} from '@/utils/catalogLabels'

describe('catalogLabels', () => {
  const skus: Sku[] = [
    {
      id: 1,
      sku_code: 'SKU-001',
      name: '螺丝',
      unit: '个',
      spec: null,
      barcode: null,
      safety_stock: '10',
      status: 1,
    },
  ]

  const locations: Location[] = [
    {
      id: 9,
      warehouse_id: 1,
      location_code: 'A-01-01',
      zone: 'A',
      aisle: null,
      bin: null,
      space_status: 'idle',
      status: 1,
    },
  ]

  it('formats sku option label as code · name', () => {
    expect(skuOptionLabel(skus[0])).toBe('SKU-001 · 螺丝')
  })

  it('builds sku id to label map', () => {
    const map = buildSkuLabelById(skus)
    expect(map.get(1)).toBe('SKU-001 · 螺丝')
  })

  it('builds location id to code map', () => {
    const map = buildLocationCodeById(locations)
    expect(map.get(9)).toBe('A-01-01')
  })

  it('falls back to string id when label missing', () => {
    expect(labelFromMap(new Map(), 42)).toBe('42')
  })
})
