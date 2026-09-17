import { describe, expect, it } from 'vitest'

import { canAccessOperatorApp } from '@/utils/authGate'

describe('canAccessOperatorApp', () => {
  it('allows operator', () => {
    expect(canAccessOperatorApp('operator')).toBe(true)
  })

  it('rejects supervisor, admin, viewer, and empty', () => {
    expect(canAccessOperatorApp('supervisor')).toBe(false)
    expect(canAccessOperatorApp('admin')).toBe(false)
    expect(canAccessOperatorApp('viewer')).toBe(false)
    expect(canAccessOperatorApp(null)).toBe(false)
    expect(canAccessOperatorApp(undefined)).toBe(false)
  })
})
