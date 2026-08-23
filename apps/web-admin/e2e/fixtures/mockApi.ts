import type { Page, Route } from '@playwright/test'

import { apiEnvelope } from '../../src/testing/apiEnvelope'

const ADMIN_PERMISSIONS = [
  'catalog:read',
  'catalog:write',
  'inbound:read',
  'inbound:write',
  'inbound:approve',
  'outbound:read',
  'outbound:write',
  'outbound:approve',
  'stocktake:read',
  'stocktake:write',
  'stocktake:approve',
  'inventory:read',
  'audit:read',
  'dict:read',
  'dict:write',
  'user:write',
  'report:read',
] as const

const MOCK_ME = {
  id: 1,
  username: 'admin',
  role_code: 'admin',
  permissions: [...ADMIN_PERMISSIONS],
}

const MOCK_WAREHOUSE = {
  id: 1,
  warehouse_code: 'WH-E2E',
  name: 'E2E 主仓',
  status: 1,
}

const MOCK_SKU = {
  id: 1,
  sku_code: 'SKU-E2E',
  name: '测试物料',
  unit: '个',
  spec: null,
  barcode: null,
  safety_stock: '10',
  status: 1,
}

function apiPath(url: string): string {
  const parsed = new URL(url)
  const marker = '/api/v1'
  const index = parsed.pathname.indexOf(marker)
  if (index === -1) {
    return parsed.pathname
  }
  return parsed.pathname.slice(index + marker.length)
}

export async function installMockApi(page: Page): Promise<void> {
  await page.route('**/api/v1/**', async (route: Route) => {
    const path = apiPath(route.request().url())
    const method = route.request().method()

    if (path === '/auth/login' && method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope(
            {
              access_token: 'e2e-token',
              token_type: 'bearer',
            },
            'e2e-trace',
          ),
        ),
      })
      return
    }

    if (path === '/auth/me' && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(MOCK_ME, 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/warehouses') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope(
            {
              items: [MOCK_WAREHOUSE],
              total: 1,
              page: 1,
              page_size: 20,
            },
            'e2e-trace',
          ),
        ),
      })
      return
    }

    if (path.startsWith('/inventories/alerts') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope(
            {
              items: [],
              total: 0,
              page: 1,
              page_size: 1,
            },
            'e2e-trace',
          ),
        ),
      })
      return
    }

    if (path.startsWith('/skus') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope(
            {
              items: [MOCK_SKU],
              total: 1,
              page: 1,
              page_size: 20,
            },
            'e2e-trace',
          ),
        ),
      })
      return
    }

    await route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        code: 40400,
        message: `E2E mock missing: ${method} ${path}`,
        data: null,
        traceId: 'e2e-trace',
      }),
    })
  })
}
