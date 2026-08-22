import type { RouteRecordRaw } from 'vue-router'

export const ROUTE_NAMES = {
  login: 'login',
  dashboard: 'dashboard',
  catalog: 'catalog',
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
          menu: true,
        },
      },
      {
        path: 'catalog',
        name: ROUTE_NAMES.catalog,
        component: () => import('@/views/CatalogView.vue'),
        meta: {
          title: '主数据',
          menu: true,
          permission: 'catalog:read',
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
      hideInMenu: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: ROUTE_NAMES.dashboard },
  },
]
