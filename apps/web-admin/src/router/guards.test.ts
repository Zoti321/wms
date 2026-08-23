import { describe, expect, it, vi } from 'vitest'
import type { RouteLocationNormalized } from 'vue-router'

import { resolveRouteGuard } from '@/router/guards'
import { ROUTE_NAMES } from '@/router/routes'

function routeOf(
  partial: Pick<RouteLocationNormalized, 'name' | 'fullPath' | 'meta'>,
): RouteLocationNormalized {
  return partial as RouteLocationNormalized
}

describe('resolveRouteGuard', () => {
  it('redirects unauthenticated users to login', async () => {
    const result = await resolveRouteGuard(
      routeOf({ name: ROUTE_NAMES.dashboard, fullPath: '/dashboard', meta: {} }),
      {
        token: null,
        user: null,
        hasPermission: () => false,
        restoreSession: vi.fn(),
      },
    )

    expect(result).toEqual({
      name: ROUTE_NAMES.login,
      query: { redirect: '/dashboard' },
    })
  })

  it('redirects to forbidden when permission is missing', async () => {
    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.catalogSkus,
        fullPath: '/catalog/skus',
        meta: { permission: 'catalog:read' },
      }),
      {
        token: 'token',
        user: { permissions: [] },
        hasPermission: () => false,
        restoreSession: vi.fn(),
      },
    )

    expect(result).toEqual({ name: ROUTE_NAMES.forbidden })
  })

  it('restores session before checking permission', async () => {
    const restoreSession = vi.fn().mockResolvedValue(true)
    const hasPermission = vi.fn().mockReturnValue(true)

    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.catalogSkus,
        fullPath: '/catalog/skus',
        meta: { permission: 'catalog:read' },
      }),
      {
        token: 'token',
        user: null,
        hasPermission,
        restoreSession,
      },
    )

    expect(restoreSession).toHaveBeenCalledOnce()
    expect(hasPermission).toHaveBeenCalledWith('catalog:read')
    expect(result).toBe(true)
  })

  it('allows public login route without token', async () => {
    const result = await resolveRouteGuard(
      routeOf({ name: ROUTE_NAMES.login, fullPath: '/login', meta: { public: true } }),
      {
        token: null,
        user: null,
        hasPermission: () => false,
        restoreSession: vi.fn(),
      },
    )

    expect(result).toBe(true)
  })

  it('allows inbound routes when inbound:read is granted', async () => {
    const hasPermission = vi.fn().mockReturnValue(true)

    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.inboundList,
        fullPath: '/inbound',
        meta: { permission: 'inbound:read' },
      }),
      {
        token: 'token',
        user: { permissions: ['inbound:read'] },
        hasPermission,
        restoreSession: vi.fn(),
      },
    )

    expect(hasPermission).toHaveBeenCalledWith('inbound:read')
    expect(result).toBe(true)
  })

  it('allows outbound routes when outbound:read is granted', async () => {
    const hasPermission = vi.fn().mockReturnValue(true)

    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.outboundList,
        fullPath: '/outbound',
        meta: { permission: 'outbound:read' },
      }),
      {
        token: 'token',
        user: { permissions: ['outbound:read'] },
        hasPermission,
        restoreSession: vi.fn(),
      },
    )

    expect(hasPermission).toHaveBeenCalledWith('outbound:read')
    expect(result).toBe(true)
  })

  it('forbids outbound create without outbound:write', async () => {
    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.outboundCreate,
        fullPath: '/outbound/create',
        meta: { permission: 'outbound:write' },
      }),
      {
        token: 'token',
        user: { permissions: ['outbound:read'] },
        hasPermission: (p) => p === 'outbound:read',
        restoreSession: vi.fn(),
      },
    )

    expect(result).toEqual({ name: ROUTE_NAMES.forbidden })
  })

  it('allows stocktake routes when stocktake:read is granted', async () => {
    const hasPermission = vi.fn().mockReturnValue(true)

    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.stocktakeList,
        fullPath: '/stocktakes',
        meta: { permission: 'stocktake:read' },
      }),
      {
        token: 'token',
        user: { permissions: ['stocktake:read'] },
        hasPermission,
        restoreSession: vi.fn(),
      },
    )

    expect(hasPermission).toHaveBeenCalledWith('stocktake:read')
    expect(result).toBe(true)
  })

  it('forbids stocktake create without stocktake:write', async () => {
    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.stocktakeCreate,
        fullPath: '/stocktakes/create',
        meta: { permission: 'stocktake:write' },
      }),
      {
        token: 'token',
        user: { permissions: ['stocktake:read'] },
        hasPermission: (p) => p === 'stocktake:read',
        restoreSession: vi.fn(),
      },
    )

    expect(result).toEqual({ name: ROUTE_NAMES.forbidden })
  })

  it('forbids inventory routes without inventory:read', async () => {
    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.inventoryBalances,
        fullPath: '/inventory',
        meta: { permission: 'inventory:read' },
      }),
      {
        token: 'token',
        user: { permissions: ['inbound:read'] },
        hasPermission: (p) => p === 'inbound:read',
        restoreSession: vi.fn(),
      },
    )

    expect(result).toEqual({ name: ROUTE_NAMES.forbidden })
  })

  it('allows inventory alert routes when inventory:read is granted', async () => {
    const hasPermission = vi.fn().mockReturnValue(true)

    const result = await resolveRouteGuard(
      routeOf({
        name: ROUTE_NAMES.inventoryAlerts,
        fullPath: '/inventory/alerts',
        meta: { permission: 'inventory:read' },
      }),
      {
        token: 'token',
        user: { permissions: ['inventory:read'] },
        hasPermission,
        restoreSession: vi.fn(),
      },
    )

    expect(hasPermission).toHaveBeenCalledWith('inventory:read')
    expect(result).toBe(true)
  })
})
