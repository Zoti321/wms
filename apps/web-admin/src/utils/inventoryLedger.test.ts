import { describe, expect, it } from 'vitest'

import { ROUTE_NAMES } from '@/router/routes'
import { resolveLedgerRefRoute } from '@/utils/inventoryLedger'

describe('resolveLedgerRefRoute', () => {
  it('returns inbound detail for PUTAWAY', () => {
    expect(resolveLedgerRefRoute({ ref_type: 'PUTAWAY', ref_id: 5 })).toEqual({
      name: ROUTE_NAMES.inboundDetail,
      params: { id: 5 },
    })
  })

  it('returns outbound detail for ALLOCATE/PICK/RELEASE', () => {
    expect(resolveLedgerRefRoute({ ref_type: 'PICK', ref_id: 8 })).toEqual({
      name: ROUTE_NAMES.outboundDetail,
      params: { id: 8 },
    })
  })

  it('returns stocktake detail for STOCKTAKE', () => {
    expect(resolveLedgerRefRoute({ ref_type: 'STOCKTAKE', ref_id: 3 })).toEqual({
      name: ROUTE_NAMES.stocktakeDetail,
      params: { id: 3 },
    })
  })

  it('returns null when ref_id is missing', () => {
    expect(resolveLedgerRefRoute({ ref_type: 'PUTAWAY', ref_id: null })).toBeNull()
  })

  it('returns null for unknown ref_type', () => {
    expect(resolveLedgerRefRoute({ ref_type: 'UNKNOWN', ref_id: 1 })).toBeNull()
  })
})
