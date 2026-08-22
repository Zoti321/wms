import type { RouteLocationNormalized, RouteLocationRaw } from 'vue-router'

import { ROUTE_NAMES } from '@/router/routes'

export interface AuthGuardContext {
  token: string | null
  user: { permissions: string[] } | null
  hasPermission: (permission: string) => boolean
  restoreSession: () => Promise<boolean>
}

export async function resolveRouteGuard(
  to: RouteLocationNormalized,
  auth: AuthGuardContext,
): Promise<RouteLocationRaw | true> {
  const isPublic = Boolean(to.meta.public)

  if (!auth.token && !isPublic) {
    return {
      name: ROUTE_NAMES.login,
      query: { redirect: to.fullPath },
    }
  }

  if (auth.token && !auth.user && !isPublic) {
    const ok = await auth.restoreSession()
    if (!ok) {
      return {
        name: ROUTE_NAMES.login,
        query: { redirect: to.fullPath },
      }
    }
  }

  if (to.name === ROUTE_NAMES.login && auth.token) {
    return { name: ROUTE_NAMES.dashboard }
  }

  const requiredPermission = to.meta.permission as string | undefined
  if (requiredPermission && !auth.hasPermission(requiredPermission)) {
    return { name: ROUTE_NAMES.forbidden }
  }

  return true
}
