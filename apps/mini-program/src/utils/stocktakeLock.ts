import { ApiError } from '@/types/api'

/** 后端盘点锁冲突文案含「盘点锁定」（上架/拣货对称）。 */
export function isStocktakeLockConflict(error: unknown): boolean {
  if (!(error instanceof ApiError)) {
    return false
  }
  return error.message.includes('盘点锁定')
}
