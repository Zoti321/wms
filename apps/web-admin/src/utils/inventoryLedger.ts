import { ROUTE_NAMES } from '@/router/routes'
import type { InventoryLedger } from '@/types/api'

export interface LedgerRefRoute {
  name: string
  params: { id: number }
}

export function resolveLedgerRefRoute(row: Pick<InventoryLedger, 'ref_type' | 'ref_id'>): LedgerRefRoute | null {
  if (row.ref_id == null) {
    return null
  }

  switch (row.ref_type) {
    case 'PUTAWAY':
      return { name: ROUTE_NAMES.inboundDetail, params: { id: row.ref_id } }
    case 'ALLOCATE':
    case 'PICK':
    case 'RELEASE':
      return { name: ROUTE_NAMES.outboundDetail, params: { id: row.ref_id } }
    case 'STOCKTAKE':
      return { name: ROUTE_NAMES.stocktakeDetail, params: { id: row.ref_id } }
    default:
      return null
  }
}
