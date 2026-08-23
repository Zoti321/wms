import { describe, expect, it } from 'vitest'

import { SIDE_MENU } from '@/router/menu'
import { useAuthStore } from '@/stores/auth'
import { createPinia, setActivePinia } from 'pinia'
import { hasPermission } from '@/utils/permission'

describe('SIDE_MENU outbound entry', () => {
  it('includes outbound menu item gated by outbound:read', () => {
    const outbound = SIDE_MENU.find(
      (entry) => entry.kind === 'item' && entry.path === '/outbound',
    )
    expect(outbound).toBeDefined()
    expect(outbound).toMatchObject({
      kind: 'item',
      title: '出库',
      path: '/outbound',
      permission: 'outbound:read',
    })
  })

  it('hides outbound when outbound:read is missing', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: { id: 1, username: 'viewer', role_code: 'viewer', permissions: ['inbound:read'] },
    })

    const visible = SIDE_MENU.filter(
      (entry) => !entry.permission || auth.hasPermission(entry.permission),
    )
    expect(visible.some((entry) => entry.kind === 'item' && entry.path === '/outbound')).toBe(
      false,
    )
  })

  it('shows outbound when outbound:read is granted', () => {
    expect(hasPermission(['outbound:read'], 'outbound:read')).toBe(true)
  })
})
