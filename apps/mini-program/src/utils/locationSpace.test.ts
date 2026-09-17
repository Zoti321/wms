import { describe, expect, it } from 'vitest'

import {
  isLocationSelectable,
  spaceStatusLabel,
} from '@/utils/locationSpace'

describe('spaceStatusLabel', () => {
  it('maps known statuses', () => {
    expect(spaceStatusLabel('idle')).toBe('空闲')
    expect(spaceStatusLabel('occupied')).toBe('占用')
    expect(spaceStatusLabel('frozen')).toBe('冻结')
  })

  it('falls back for unknown', () => {
    expect(spaceStatusLabel('other')).toBe('other')
    expect(spaceStatusLabel(undefined)).toBe('—')
  })
})

describe('isLocationSelectable', () => {
  it('blocks frozen only', () => {
    expect(isLocationSelectable('idle')).toBe(true)
    expect(isLocationSelectable('occupied')).toBe(true)
    expect(isLocationSelectable('frozen')).toBe(false)
    expect(isLocationSelectable(undefined)).toBe(true)
  })
})
