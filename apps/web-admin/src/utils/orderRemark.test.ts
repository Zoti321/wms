import { describe, expect, it } from 'vitest'

import { parseCancelReasonFromRemark } from '@/utils/orderRemark'

describe('parseCancelReasonFromRemark', () => {
  it('returns nulls for empty remark', () => {
    expect(parseCancelReasonFromRemark(null)).toEqual({
      cancelReason: null,
      userRemark: null,
    })
  })

  it('parses cancel reason prefix and user remark', () => {
    expect(parseCancelReasonFromRemark('[取消原因: 客户取消] 供应商延迟')).toEqual({
      cancelReason: '客户取消',
      userRemark: '供应商延迟',
    })
  })

  it('returns plain remark when no cancel prefix', () => {
    expect(parseCancelReasonFromRemark('仅备注')).toEqual({
      cancelReason: null,
      userRemark: '仅备注',
    })
  })
})
