import { describe, expect, it, vi } from 'vitest'

import {
  notifyUnauthorized,
  registerUnauthorizedHandler,
  resetUnauthorizedHandler,
} from '@/api/unauthorized'

describe('unauthorized handler', () => {
  it('invokes registered handler', () => {
    const handler = vi.fn()
    registerUnauthorizedHandler(handler)

    notifyUnauthorized()

    expect(handler).toHaveBeenCalledOnce()
    resetUnauthorizedHandler()
  })

  it('does nothing when handler is not registered', () => {
    resetUnauthorizedHandler()
    expect(() => notifyUnauthorized()).not.toThrow()
  })
})
