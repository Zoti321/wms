import { describe, expect, it } from 'vitest'

import { apiEnvelope } from '@/testing/apiEnvelope'

describe('apiEnvelope', () => {
  it('builds success envelope with data', () => {
    expect(apiEnvelope({ id: 1 })).toEqual({
      code: 0,
      message: 'ok',
      data: { id: 1 },
      traceId: 'test-trace',
    })
  })
})
