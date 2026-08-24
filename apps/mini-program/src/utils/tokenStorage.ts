const TOKEN_KEY = 'wms_access_token'

export function getAccessToken(): string | null {
  try {
    const value = uni.getStorageSync(TOKEN_KEY)
    return typeof value === 'string' && value.length > 0 ? value : null
  } catch {
    return null
  }
}

export function setAccessToken(token: string): void {
  uni.setStorageSync(TOKEN_KEY, token)
}

export function clearAccessToken(): void {
  try {
    uni.removeStorageSync(TOKEN_KEY)
  } catch {
    // ignore
  }
}
