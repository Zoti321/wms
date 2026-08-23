/** 将 API 返回的 ISO / `YYYY-MM-DD HH:mm:ss` 字符串格式化为本地时区可读时间。 */
export function formatDateTime(value: string | null | undefined): string {
  if (value == null || value.trim() === '') {
    return '—'
  }

  const normalized = value.includes('T') ? value : value.replace(' ', 'T')
  const date = new Date(normalized)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

/** 将 Date 格式化为 API 查询参数用的 `YYYY-MM-DD HH:mm:ss`（本地时区）。 */
export function formatDateTimeForQuery(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}
