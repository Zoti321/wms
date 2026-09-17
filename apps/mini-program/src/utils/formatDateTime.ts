/** API UTC/本地串 → 本地 `YYYY-MM-DD HH:mm`。 */
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
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}
