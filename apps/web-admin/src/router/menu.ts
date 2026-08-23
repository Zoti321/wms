import type { Component } from 'vue'

export interface SideMenuLeaf {
  kind: 'item'
  title: string
  path: string
  permission?: string
  icon?: Component
}

export interface SideMenuGroup {
  kind: 'group'
  title: string
  permission?: string
  icon?: Component
  children: SideMenuLeaf[]
}

export type SideMenuEntry = SideMenuLeaf | SideMenuGroup

/** 侧栏仅列本切片已实现项；渲染时再按权限过滤。 */
export const SIDE_MENU: SideMenuEntry[] = [
  {
    kind: 'item',
    title: '工作台',
    path: '/dashboard',
  },
  {
    kind: 'group',
    title: '主数据',
    permission: 'catalog:read',
    children: [
      { kind: 'item', title: 'SKU', path: '/catalog/skus', permission: 'catalog:read' },
      {
        kind: 'item',
        title: '库位',
        path: '/catalog/locations',
        permission: 'catalog:read',
      },
    ],
  },
  {
    kind: 'item',
    title: '入库',
    path: '/inbound',
    permission: 'inbound:read',
  },
  {
    kind: 'item',
    title: '出库',
    path: '/outbound',
    permission: 'outbound:read',
  },
  {
    kind: 'group',
    title: '库存',
    permission: 'inventory:read',
    children: [
      {
        kind: 'item',
        title: '库存余额',
        path: '/inventory',
        permission: 'inventory:read',
      },
      {
        kind: 'item',
        title: '库存流水',
        path: '/inventory/ledgers',
        permission: 'inventory:read',
      },
    ],
  },
]
