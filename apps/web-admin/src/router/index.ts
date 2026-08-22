import { createRouter, createWebHistory } from 'vue-router'

import { resolveRouteGuard } from '@/router/guards'
import { appRoutes } from '@/router/routes'
import { useAuthStore } from '@/stores/auth'

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: appRoutes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  return resolveRouteGuard(to, auth)
})

export default router
