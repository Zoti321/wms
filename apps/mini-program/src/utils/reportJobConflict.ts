import { errorMessage } from '@/utils/errorMessage'
import { isStocktakeLockConflict } from '@/utils/stocktakeLock'

export interface JobFailureReport {
  message: string
  /** 是否已用盘点锁专用 Modal 展示 */
  usedStocktakeLockModal: boolean
}

/** 盘点锁：专用 Modal；其它错误：Toast。页内 formError 仅在非盘点锁时由调用方写入。 */
export function reportJobConflict(error: unknown, fallback: string): JobFailureReport {
  const message = errorMessage(error, fallback)
  if (isStocktakeLockConflict(error)) {
    uni.showModal({
      title: '无法作业',
      content: message,
      showCancel: false,
      confirmText: '知道了',
    })
    return { message, usedStocktakeLockModal: true }
  }
  uni.showToast({ title: message, icon: 'none' })
  return { message, usedStocktakeLockModal: false }
}
