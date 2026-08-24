import { describe, expect, it } from 'vitest'

import { apiUrl, resolveApiBaseUrl } from '@/config/env'

describe('resolveApiBaseUrl', () => {
  it('trims whitespace and trailing slash', () => {
    expect(resolveApiBaseUrl('  https://api.example.com/  ')).toBe('https://api.example.com')
  })

  it('returns empty string when unset', () => {
    expect(resolveApiBaseUrl('')).toBe('')
    expect(resolveApiBaseUrl(undefined)).toBe('')
  })
})

describe('apiUrl', () => {
  it('joins base and path', () => {
    expect(apiUrl('/api/v1/health', 'https://api.example.com')).toBe(
      'https://api.example.com/api/v1/health',
    )
  })

  it('returns relative path when base is empty (H5 proxy)', () => {
    expect(apiUrl('/api/v1/health', '')).toBe('/api/v1/health')
  })
})
