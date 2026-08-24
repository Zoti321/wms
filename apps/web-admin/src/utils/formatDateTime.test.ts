import { describe, expect, it } from 'vitest'

import { formatDateTime, formatDateTimeForQuery } from '@/utils/formatDateTime'

describe('formatDateTime', () => {
  it('returns em dash for empty input', () => {
    expect(formatDateTime(null)).toBe('—')
    expect(formatDateTime('')).toBe('—')
  })

  it('formats ISO strings in local timezone', () => {
    const formatted = formatDateTime('2026-08-23T04:30:00.000Z')
    expect(formatted).toMatch(/^2026-08-23 \d{2}:\d{2}:\d{2}$/)
  })

  it('formats space-separated datetime strings', () => {
    const formatted = formatDateTime('2026-08-23 12:00:00')
    expect(formatted).toMatch(/^2026-08-23 \d{2}:\d{2}:\d{2}$/)
  })

  it('returns original value when unparseable', () => {
    expect(formatDateTime('not-a-date')).toBe('not-a-date')
  })
})

describe('formatDateTimeForQuery', () => {
  it('formats date parts with zero padding', () => {
    const date = new Date(2026, 0, 5, 8, 9, 7)
    expect(formatDateTimeForQuery(date)).toBe('2026-01-05 08:09:07')
  })
})
