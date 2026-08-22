import { createRouter, createWebHistory } from 'vue-router'

import { ROUTE_NAMES, appRoutes } from '@/router/routes'
import { useAuthStore } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: appRoutes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
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
})

export default router
