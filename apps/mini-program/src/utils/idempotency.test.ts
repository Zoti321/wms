import { describe, expect, it, vi } from 'vitest'

import { createIdempotencyKey, nextIdempotencyKey } from '@/utils/idempotency'

describe('createIdempotencyKey', () => {
  it('returns a non-empty string', () => {
    expect(createIdempotencyKey().length).toBeGreaterThan(8)
  })
})

describe('nextIdempotencyKey', () => {
  it('reuses key when fingerprint unchanged', () => {
    const first = nextIdempotencyKey(null, 'line=1|loc=2|qty=3', null)
    const second = nextIdempotencyKey(first.key, 'line=1|loc=2|qty=3', first.fingerprint)
    expect(second.key).toBe(first.key)
  })

  it('rotates key when fingerprint changes', () => {
    vi.spyOn(crypto, 'randomUUID')
      .mockReturnValueOnce('00000000-0000-4000-8000-00000000000a')
      .mockReturnValueOnce('00000000-0000-4000-8000-00000000000b')
    const first = nextIdempotencyKey(null, 'a', null)
    const second = nextIdempotencyKey(first.key, 'b', first.fingerprint)
    expect(first.key).toBe('00000000-0000-4000-8000-00000000000a')
    expect(second.key).toBe('00000000-0000-4000-8000-00000000000b')
  })
})
