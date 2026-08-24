import { describe, expect, it } from 'vitest'

import { ApiError } from '@/types/api'
import { isStocktakeLockConflict } from '@/utils/stocktakeLock'

describe('isStocktakeLockConflict', () => {
  it('detects putaway lock message', () => {
    expect(
      isStocktakeLockConflict(new ApiError(40900, '库位已盘点锁定，不可上架', 't')),
    ).toBe(true)
  })

  it('detects pick lock message', () => {
    expect(
      isStocktakeLockConflict(new ApiError(40900, '库位已盘点锁定，不可拣货', 't')),
    ).toBe(true)
  })

  it('rejects other conflict messages', () => {
    expect(
      isStocktakeLockConflict(new ApiError(40900, '单据状态不允许上架', 't')),
    ).toBe(false)
  })

  it('rejects non-ApiError', () => {
    expect(isStocktakeLockConflict(new Error('库位已盘点锁定，不可上架'))).toBe(false)
    expect(isStocktakeLockConflict('库位已盘点锁定')).toBe(false)
  })
})
