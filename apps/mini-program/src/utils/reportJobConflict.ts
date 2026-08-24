import { errorMessage } from '@/utils/errorMessage'
import { isStocktakeLockConflict } from '@/utils/stocktakeLock'

/** 盘点锁冲突：专用 Modal；其它错误：页内文案 + Toast。返回展示用 message。 */
export function reportJobConflict(error: unknown, fallback: string): string {
  const message = errorMessage(error, fallback)
  if (isStocktakeLockConflict(error)) {
    uni.showModal({
      title: '无法作业',
      content: message,
      showCancel: false,
      confirmText: '知道了',
    })
  } else {
    uni.showToast({ title: message, icon: 'none' })
  }
  return message
}
