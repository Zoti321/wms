/**
 * 解析 API 根地址。
 * - H5 开发：可留空，走 Vite 代理 `/api`
 * - 微信小程序：须配置 `VITE_API_BASE_URL` 为完整 HTTPS 域名
 */
export function resolveApiBaseUrl(raw = import.meta.env.VITE_API_BASE_URL): string {
  return (raw ?? '').trim().replace(/\/$/, '')
}

/** 拼接 API 路径；base 为空时返回相对路径供 H5 代理使用。 */
export function apiUrl(path: string, base = resolveApiBaseUrl()): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${normalizedPath}` : normalizedPath
}
