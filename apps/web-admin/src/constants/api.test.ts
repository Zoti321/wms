import { describe, expect, it } from 'vitest'

import { MAX_LIST_PAGE_SIZE } from '@/constants/api'

describe('MAX_LIST_PAGE_SIZE', () => {
  it('matches wms-api MAX_PAGE_SIZE (100)', () => {
    expect(MAX_LIST_PAGE_SIZE).toBe(100)
  })
})
