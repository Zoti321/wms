import { describe, expect, it } from 'vitest'

import {
  hasAllPermissions,
  hasAnyPermission,
  hasPermission,
} from '@/utils/permission'

describe('permission utils', () => {
  const granted = ['catalog:read', 'inbound:write']

  it('hasPermission returns true when granted', () => {
    expect(hasPermission(granted, 'catalog:read')).toBe(true)
  })

  it('hasPermission returns false when missing', () => {
    expect(hasPermission(granted, 'catalog:write')).toBe(false)
  })

  it('hasAnyPermission matches one of required', () => {
    expect(hasAnyPermission(granted, ['catalog:write', 'inbound:write'])).toBe(true)
  })

  it('hasAllPermissions requires every permission', () => {
    expect(hasAllPermissions(granted, ['catalog:read', 'inbound:write'])).toBe(true)
    expect(hasAllPermissions(granted, ['catalog:read', 'catalog:write'])).toBe(false)
  })
})
