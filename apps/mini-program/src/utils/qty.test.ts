import { describe, expect, it } from 'vitest'

import { isPositiveQty, remainQty } from '@/utils/qty'

describe('remainQty', () => {
  it('computes planned minus done', () => {
    expect(remainQty('10.000', '3.500')).toBe('6.500')
  })

  it('floors at zero', () => {
    expect(remainQty('1.000', '1.000')).toBe('0.000')
    expect(remainQty('1.000', '2.000')).toBe('0.000')
  })
})

describe('isPositiveQty', () => {
  it('accepts positive decimals', () => {
    expect(isPositiveQty('0.001')).toBe(true)
    expect(isPositiveQty('0')).toBe(false)
    expect(isPositiveQty('-1')).toBe(false)
  })
})
