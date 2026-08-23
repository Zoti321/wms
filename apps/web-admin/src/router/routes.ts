import type { RouteRecordRaw } from 'vue-router'

export const ROUTE_NAMES = {
  login: 'login',
  dashboard: 'dashboard',
  catalogSkus: 'catalog-skus',
  catalogLocations: 'catalog-locations',
  inboundList: 'inbound-list',
  inboundCreate: 'inbound-create',
  inboundDetail: 'inbound-detail',
  outboundList: 'outbound-list',
  outboundCreate: 'outbound-create',
  outboundEdit: 'outbound-edit',
  outboundDetail: 'outbound-detail',
  inventoryBalances: 'inventory-balances',
  inventoryLedgers: 'inventory-ledgers',
  inventoryAlerts: 'inventory-alerts',
  stocktakeList: 'stocktake-list',
  stocktakeCreate: 'stocktake-create',
  stocktakeDetail: 'stocktake-detail',
  forbidden: 'forbidden',
} as const

export const appRoutes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: ROUTE_NAMES.login,
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: '登录',
      public: true,
    },
  },
  {
    path: '/',
    component: () => import('@/views/layout/AdminLayout.vue'),
    children: [
      {
        path: '',
        redirect: { name: ROUTE_NAMES.dashboard },
      },
      {
        path: 'dashboard',
        name: ROUTE_NAMES.dashboard,
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          title: '工作台',
        },
      },
      {
        path: 'catalog/skus',
        name: ROUTE_NAMES.catalogSkus,
        component: () => import('@/views/catalog/SkuListView.vue'),
        meta: {
          title: 'SKU',
          permission: 'catalog:read',
        },
      },
      {
        path: 'catalog/locations',
        name: ROUTE_NAMES.catalogLocations,
        component: () => import('@/views/catalog/LocationListView.vue'),
        meta: {
          title: '库位',
          permission: 'catalog:read',
        },
      },
      {
        path: 'inbound',
        name: ROUTE_NAMES.inboundList,
        component: () => import('@/views/inbound/InboundListView.vue'),
        meta: {
          title: '入库单',
          permission: 'inbound:read',
        },
      },
      {
        path: 'inbound/create',
        name: ROUTE_NAMES.inboundCreate,
        component: () => import('@/views/inbound/InboundFormView.vue'),
        meta: {
          title: '新建入库单',
          permission: 'inbound:write',
        },
      },
      {
        path: 'inbound/:id',
        name: ROUTE_NAMES.inboundDetail,
        component: () => import('@/views/inbound/InboundDetailView.vue'),
        meta: {
          title: '入库单详情',
          permission: 'inbound:read',
        },
      },
      {
        path: 'outbound',
        name: ROUTE_NAMES.outboundList,
        component: () => import('@/views/outbound/OutboundListView.vue'),
        meta: {
          title: '出库单',
          permission: 'outbound:read',
        },
      },
      {
        path: 'outbound/create',
        name: ROUTE_NAMES.outboundCreate,
        component: () => import('@/views/outbound/OutboundFormView.vue'),
        meta: {
          title: '新建出库单',
          permission: 'outbound:write',
        },
      },
      {
        path: 'outbound/:id/edit',
        name: ROUTE_NAMES.outboundEdit,
        component: () => import('@/views/outbound/OutboundFormView.vue'),
        meta: {
          title: '编辑出库单',
          permission: 'outbound:write',
        },
      },
      {
        path: 'outbound/:id',
        name: ROUTE_NAMES.outboundDetail,
        component: () => import('@/views/outbound/OutboundDetailView.vue'),
        meta: {
          title: '出库单详情',
          permission: 'outbound:read',
        },
      },
      {
        path: 'stocktakes',
        name: ROUTE_NAMES.stocktakeList,
        component: () => import('@/views/stocktake/StocktakeListView.vue'),
        meta: {
          title: '盘点单',
          permission: 'stocktake:read',
        },
      },
      {
        path: 'stocktakes/create',
        name: ROUTE_NAMES.stocktakeCreate,
        component: () => import('@/views/stocktake/StocktakeFormView.vue'),
        meta: {
          title: '发起盘点',
          permission: 'stocktake:write',
        },
      },
      {
        path: 'stocktakes/:id',
        name: ROUTE_NAMES.stocktakeDetail,
        component: () => import('@/views/stocktake/StocktakeDetailView.vue'),
        meta: {
          title: '盘点单详情',
          permission: 'stocktake:read',
        },
      },
      {
        path: 'inventory',
        name: ROUTE_NAMES.inventoryBalances,
        component: () => import('@/views/inventory/InventoryBalanceView.vue'),
        meta: {
          title: '库存余额',
          permission: 'inventory:read',
        },
      },
      {
        path: 'inventory/ledgers',
        name: ROUTE_NAMES.inventoryLedgers,
        component: () => import('@/views/inventory/InventoryLedgerView.vue'),
        meta: {
          title: '库存流水',
          permission: 'inventory:read',
        },
      },
      {
        path: 'inventory/alerts',
        name: ROUTE_NAMES.inventoryAlerts,
        component: () => import('@/views/inventory/InventoryAlertView.vue'),
        meta: {
          title: '库存预警',
          permission: 'inventory:read',
        },
      },
    ],
  },
  {
    path: '/403',
    name: ROUTE_NAMES.forbidden,
    component: () => import('@/views/ForbiddenView.vue'),
    meta: {
      title: '无权限',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: ROUTE_NAMES.dashboard },
  },
]
