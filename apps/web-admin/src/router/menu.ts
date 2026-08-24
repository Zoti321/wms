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
      {
        kind: 'item',
        title: '仓库',
        path: '/catalog/warehouses',
        permission: 'catalog:read',
      },
      {
        kind: 'item',
        title: '供应商',
        path: '/catalog/suppliers',
        permission: 'catalog:read',
      },
      {
        kind: 'item',
        title: '客户',
        path: '/catalog/customers',
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
    kind: 'item',
    title: '盘点',
    path: '/stocktakes',
    permission: 'stocktake:read',
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
      {
        kind: 'item',
        title: '库存预警',
        path: '/inventory/alerts',
        permission: 'inventory:read',
      },
    ],
  },
  {
    kind: 'group',
    title: '系统管理',
    children: [
      {
        kind: 'item',
        title: '用户',
        path: '/platform/users',
        permission: 'user:write',
      },
      {
        kind: 'item',
        title: '字典',
        path: '/platform/dictionaries',
        permission: 'dict:read',
      },
      {
        kind: 'item',
        title: '操作日志',
        path: '/platform/operation-logs',
        permission: 'audit:read',
      },
      {
        kind: 'item',
        title: '日报',
        path: '/platform/reports/daily',
        permission: 'report:read',
      },
    ],
  },
]
