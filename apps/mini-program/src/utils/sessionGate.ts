import { useAuthStore } from '@/stores/auth'

/** 作业页会话门禁：非仓管员 / 未登录 → 登录页。 */
export async function requireOperatorSession(): Promise<boolean> {
  const auth = useAuthStore()
  if (!auth.accessToken) {
    const result = await auth.restoreSession()
    if (result !== 'ok') {
      uni.reLaunch({ url: '/pages/login/login' })
      return false
    }
    return true
  }
  if (!auth.isOperator) {
    uni.reLaunch({ url: '/pages/login/login' })
    return false
  }
  return true
}
