import { describe, expect, it } from 'vitest'

import type { Customer, Location, Sku, Supplier } from '@/types/api'
import {
  buildCustomerLabelById,
  buildLocationCodeById,
  buildSkuLabelById,
  buildSupplierLabelById,
  customerOptionLabel,
  labelFromMap,
  skuOptionLabel,
  supplierOptionLabel,
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

  const suppliers: Supplier[] = [
    {
      id: 3,
      supplier_code: 'SUP-001',
      name: '华东供应商',
      status: 1,
    },
  ]

  const customers: Customer[] = [
    {
      id: 5,
      customer_code: 'CUS-001',
      name: '华南客户',
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

  it('formats supplier option label as code · name', () => {
    expect(supplierOptionLabel(suppliers[0])).toBe('SUP-001 · 华东供应商')
  })

  it('formats customer option label as code · name', () => {
    expect(customerOptionLabel(customers[0])).toBe('CUS-001 · 华南客户')
  })

  it('builds supplier id to label map', () => {
    const map = buildSupplierLabelById(suppliers)
    expect(map.get(3)).toBe('SUP-001 · 华东供应商')
  })

  it('builds customer id to label map', () => {
    const map = buildCustomerLabelById(customers)
    expect(map.get(5)).toBe('CUS-001 · 华南客户')
  })

  it('falls back to string id when label missing', () => {
    expect(labelFromMap(new Map(), 42)).toBe('42')
  })

  it('falls back to string id for supplier and customer maps', () => {
    expect(labelFromMap(buildSupplierLabelById(suppliers), 99)).toBe('99')
    expect(labelFromMap(buildCustomerLabelById(customers), 88)).toBe('88')
  })
})
