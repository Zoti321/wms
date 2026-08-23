import { describe, expect, it } from 'vitest'

import { SIDE_MENU } from '@/router/menu'
import { useAuthStore } from '@/stores/auth'
import { createPinia, setActivePinia } from 'pinia'
import { hasPermission } from '@/utils/permission'

describe('SIDE_MENU stocktake entry', () => {
  it('includes stocktake menu item gated by stocktake:read', () => {
    const stocktake = SIDE_MENU.find(
      (entry) => entry.kind === 'item' && entry.path === '/stocktakes',
    )
    expect(stocktake).toBeDefined()
    expect(stocktake).toMatchObject({
      kind: 'item',
      title: '盘点',
      path: '/stocktakes',
      permission: 'stocktake:read',
    })
  })

  it('hides stocktake when stocktake:read is missing', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: { id: 1, username: 'viewer', role_code: 'viewer', permissions: ['inbound:read'] },
    })

    const visible = SIDE_MENU.filter(
      (entry) => !entry.permission || auth.hasPermission(entry.permission),
    )
    expect(visible.some((entry) => entry.kind === 'item' && entry.path === '/stocktakes')).toBe(
      false,
    )
  })
})

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

describe('SIDE_MENU inventory alerts entry', () => {
  it('includes inventory alerts under inventory group', () => {
    const inventoryGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '库存',
    )
    expect(inventoryGroup?.kind).toBe('group')
    if (inventoryGroup?.kind !== 'group') {
      return
    }
    const alerts = inventoryGroup.children.find((child) => child.path === '/inventory/alerts')
    expect(alerts).toMatchObject({
      kind: 'item',
      title: '库存预警',
      path: '/inventory/alerts',
      permission: 'inventory:read',
    })
  })

  it('hides inventory alerts when inventory:read is missing', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: { id: 1, username: 'viewer', role_code: 'viewer', permissions: ['inbound:read'] },
    })

    const inventoryGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '库存',
    )
    if (inventoryGroup?.kind !== 'group') {
      throw new Error('inventory group missing')
    }
    const visibleChildren = inventoryGroup.children.filter(
      (child) => !child.permission || auth.hasPermission(child.permission),
    )
    expect(visibleChildren.some((child) => child.path === '/inventory/alerts')).toBe(false)
  })
})

describe('SIDE_MENU platform group', () => {
  it('includes system management group with permission-gated children', () => {
    const platformGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '系统管理',
    )
    expect(platformGroup?.kind).toBe('group')
    if (platformGroup?.kind !== 'group') {
      return
    }
    expect(platformGroup.children).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          path: '/platform/users',
          permission: 'user:write',
        }),
        expect.objectContaining({
          path: '/platform/dictionaries',
          permission: 'dict:read',
        }),
        expect.objectContaining({
          path: '/platform/operation-logs',
          permission: 'audit:read',
        }),
        expect.objectContaining({
          path: '/platform/reports/daily',
          permission: 'report:read',
        }),
      ]),
    )
  })

  it('hides entire platform group when user has no platform permissions', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: {
        id: 1,
        username: 'operator',
        role_code: 'operator',
        permissions: ['inbound:read'],
      },
    })

    const platformGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '系统管理',
    )
    if (platformGroup?.kind !== 'group') {
      throw new Error('platform group missing')
    }
    const visibleChildren = platformGroup.children.filter(
      (child) => !child.permission || auth.hasPermission(child.permission),
    )
    expect(visibleChildren).toHaveLength(0)
  })

  it('shows dict and report entries for supervisor', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: {
        id: 1,
        username: 'supervisor',
        role_code: 'supervisor',
        permissions: ['dict:read', 'audit:read', 'report:read'],
      },
    })

    const platformGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '系统管理',
    )
    if (platformGroup?.kind !== 'group') {
      throw new Error('platform group missing')
    }
    const visibleChildren = platformGroup.children.filter(
      (child) => !child.permission || auth.hasPermission(child.permission),
    )
    expect(visibleChildren.map((c) => c.path)).toEqual(
      expect.arrayContaining([
        '/platform/dictionaries',
        '/platform/operation-logs',
        '/platform/reports/daily',
      ]),
    )
    expect(visibleChildren.some((c) => c.path === '/platform/users')).toBe(false)
  })
})

describe('SIDE_MENU catalog group', () => {
  it('includes warehouse, supplier, and customer under catalog group', () => {
    const catalogGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '主数据',
    )
    expect(catalogGroup?.kind).toBe('group')
    if (catalogGroup?.kind !== 'group') {
      return
    }
    expect(catalogGroup.children).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ path: '/catalog/warehouses', permission: 'catalog:read' }),
        expect.objectContaining({ path: '/catalog/suppliers', permission: 'catalog:read' }),
        expect.objectContaining({ path: '/catalog/customers', permission: 'catalog:read' }),
      ]),
    )
  })

  it('hides catalog entries when catalog:read is missing', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.$patch({
      user: { id: 1, username: 'viewer', role_code: 'viewer', permissions: ['inbound:read'] },
    })

    const catalogGroup = SIDE_MENU.find(
      (entry) => entry.kind === 'group' && entry.title === '主数据',
    )
    if (catalogGroup?.kind !== 'group') {
      throw new Error('catalog group missing')
    }
    expect(catalogGroup.children.every((child) => auth.hasPermission(child.permission!))).toBe(
      false,
    )
  })
})
