import type { Customer, Location, Sku, Supplier } from '@/types/api'

export function skuOptionLabel(sku: Pick<Sku, 'sku_code' | 'name'>): string {
  return `${sku.sku_code} · ${sku.name}`
}

export function supplierOptionLabel(
  supplier: Pick<Supplier, 'supplier_code' | 'name'>,
): string {
  return `${supplier.supplier_code} · ${supplier.name}`
}

export function customerOptionLabel(
  customer: Pick<Customer, 'customer_code' | 'name'>,
): string {
  return `${customer.customer_code} · ${customer.name}`
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

export function buildSupplierLabelById(suppliers: Supplier[]): Map<number, string> {
  const map = new Map<number, string>()
  for (const supplier of suppliers) {
    map.set(supplier.id, supplierOptionLabel(supplier))
  }
  return map
}

export function buildCustomerLabelById(customers: Customer[]): Map<number, string> {
  const map = new Map<number, string>()
  for (const customer of customers) {
    map.set(customer.id, customerOptionLabel(customer))
  }
  return map
}

export function labelFromMap(map: Map<number, string>, id: number): string {
  return map.get(id) ?? String(id)
}
