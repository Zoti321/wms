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

const MOCK_LOCATION = {
  id: 1,
  warehouse_id: 1,
  location_code: 'A-01-01',
  zone: 'A',
  aisle: '01',
  bin: '01',
  space_status: 'idle',
  status: 1,
}

const MOCK_BALANCE = {
  id: 1,
  warehouse_id: 1,
  sku_id: 1,
  location_id: 1,
  qty_on_hand: '100',
  qty_frozen: '0',
  qty_available: '100',
  version: 1,
}

type InboundStatus = 'draft' | 'pending' | 'approved' | 'putaway' | 'done' | 'cancelled'
type OutboundStatus = 'draft' | 'pending' | 'approved' | 'picking' | 'done' | 'cancelled'
type StocktakeStatus = 'counting' | 'approved' | 'cancelled'

let inboundOrder: {
  id: number
  order_no: string
  warehouse_id: number
  order_type: string
  status: InboundStatus
  supplier_id: number | null
  remark: string | null
  created_by: number
  created_at: string
  lines: Array<{ id: number; sku_id: number; planned_qty: string; putaway_qty: string }>
}

let outboundOrder: {
  id: number
  order_no: string
  warehouse_id: number
  order_type: string
  status: OutboundStatus
  customer_id: number | null
  remark: string | null
  created_by: number
  created_at: string
  lines: Array<{
    id: number
    sku_id: number
    planned_qty: string
    allocated_qty: string
    picked_qty: string
    location_id: number | null
  }>
}

let stocktakeOrder: {
  id: number
  order_no: string
  warehouse_id: number
  zone: string | null
  status: StocktakeStatus
  remark: string | null
  created_by: number
  approved_by: number | null
  created_at: string
  lines: Array<{
    id: number
    sku_id: number
    location_id: number
    book_qty: string
    counted_qty: string | null
    diff_qty: string | null
  }>
}

export function resetMockState(): void {
  inboundOrder = {
    id: 101,
    order_no: 'IN-E2E-001',
    warehouse_id: 1,
    order_type: 'purchase',
    status: 'draft',
    supplier_id: null,
    remark: null,
    created_by: 1,
    created_at: '2026-08-23T10:00:00',
    lines: [{ id: 1001, sku_id: 1, planned_qty: '10', putaway_qty: '0' }],
  }

  outboundOrder = {
    id: 201,
    order_no: 'OUT-E2E-001',
    warehouse_id: 1,
    order_type: 'sales',
    status: 'pending',
    customer_id: null,
    remark: null,
    created_by: 1,
    created_at: '2026-08-23T10:00:00',
    lines: [
      {
        id: 2001,
        sku_id: 1,
        planned_qty: '5',
        picked_qty: '0',
        allocated_qty: '0',
        location_id: null,
      },
    ],
  }

  stocktakeOrder = {
    id: 301,
    order_no: 'ST-E2E-001',
    warehouse_id: 1,
    zone: null,
    status: 'counting',
    remark: null,
    created_by: 1,
    approved_by: null,
    created_at: '2026-08-23T10:00:00',
    lines: [
      {
        id: 3001,
        sku_id: 1,
        location_id: 1,
        book_qty: '10',
        counted_qty: null,
        diff_qty: null,
      },
    ],
  }
}

resetMockState()

function paginate<T>(items: T[], page: number, pageSize: number) {
  return {
    items,
    total: items.length,
    page,
    page_size: pageSize,
  }
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

function queryParam(url: string, key: string): string | null {
  return new URL(url).searchParams.get(key)
}

export async function installMockApi(page: Page): Promise<void> {
  resetMockState()

  await page.route('**/api/v1/**', async (route: Route) => {
    const url = route.request().url()
    const path = apiPath(url)
    const method = route.request().method()

    if (path === '/auth/login' && method === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ access_token: 'e2e-token', token_type: 'bearer' }, 'e2e-trace'),
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
        body: JSON.stringify(apiEnvelope(paginate([MOCK_WAREHOUSE], 1, 100), 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/inventories/alerts') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(paginate([], 1, 1), 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/inventories/ledgers') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(paginate([], 1, 20), 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/inventories') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(paginate([MOCK_BALANCE], 1, 1), 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/skus') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(paginate([MOCK_SKU], 1, 100), 'e2e-trace')),
      })
      return
    }

    if (path.startsWith('/locations') && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(paginate([MOCK_LOCATION], 1, 100), 'e2e-trace')),
      })
      return
    }

    if (path === '/inbound-orders' && method === 'GET') {
      const status = queryParam(url, 'status')
      const items =
        status == null || inboundOrder.status === status
          ? [
              {
                id: inboundOrder.id,
                order_no: inboundOrder.order_no,
                warehouse_id: inboundOrder.warehouse_id,
                order_type: inboundOrder.order_type,
                status: inboundOrder.status,
                supplier_id: inboundOrder.supplier_id,
                created_at: inboundOrder.created_at,
              },
            ]
          : []
      const page = Number(queryParam(url, 'page') ?? '1')
      const pageSize = Number(queryParam(url, 'page_size') ?? '20')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ ...paginate(items, page, pageSize), total: items.length }, 'e2e-trace'),
        ),
      })
      return
    }

    if (path === `/inbound-orders/${inboundOrder.id}` && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(inboundOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/inbound-orders/${inboundOrder.id}/submit` && method === 'POST') {
      inboundOrder = { ...inboundOrder, status: 'pending' }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(inboundOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/inbound-orders/${inboundOrder.id}/approve` && method === 'POST') {
      inboundOrder = { ...inboundOrder, status: 'approved' }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(inboundOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/inbound-orders/${inboundOrder.id}/putaway` && method === 'POST') {
      inboundOrder = {
        ...inboundOrder,
        status: 'done',
        lines: inboundOrder.lines.map((line) => ({ ...line, putaway_qty: line.planned_qty })),
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ order: inboundOrder, putaway_record_id: 1, replayed: false }, 'e2e-trace'),
        ),
      })
      return
    }

    if (path === '/outbound-orders' && method === 'GET') {
      const status = queryParam(url, 'status')
      const items =
        status == null || outboundOrder.status === status
          ? [
              {
                id: outboundOrder.id,
                order_no: outboundOrder.order_no,
                warehouse_id: outboundOrder.warehouse_id,
                order_type: outboundOrder.order_type,
                status: outboundOrder.status,
                created_at: outboundOrder.created_at,
              },
            ]
          : []
      const page = Number(queryParam(url, 'page') ?? '1')
      const pageSize = Number(queryParam(url, 'page_size') ?? '20')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ ...paginate(items, page, pageSize), total: items.length }, 'e2e-trace'),
        ),
      })
      return
    }

    if (path === `/outbound-orders/${outboundOrder.id}` && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(outboundOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/outbound-orders/${outboundOrder.id}/approve` && method === 'POST') {
      outboundOrder = {
        ...outboundOrder,
        status: 'approved',
        lines: outboundOrder.lines.map((line) => ({
          ...line,
          allocated_qty: line.planned_qty,
          location_id: 1,
        })),
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope({ order: outboundOrder, replayed: false }, 'e2e-trace')),
      })
      return
    }

    if (path === `/outbound-orders/${outboundOrder.id}/pick` && method === 'POST') {
      outboundOrder = {
        ...outboundOrder,
        status: 'done',
        lines: outboundOrder.lines.map((line) => ({
          ...line,
          picked_qty: line.planned_qty,
        })),
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ order: outboundOrder, pick_record_id: 1, replayed: false }, 'e2e-trace'),
        ),
      })
      return
    }

    if (path === '/stocktakes' && method === 'GET') {
      const status = queryParam(url, 'status')
      const items =
        status == null || stocktakeOrder.status === status
          ? [
              {
                id: stocktakeOrder.id,
                order_no: stocktakeOrder.order_no,
                warehouse_id: stocktakeOrder.warehouse_id,
                status: stocktakeOrder.status,
                created_at: stocktakeOrder.created_at,
              },
            ]
          : []
      const page = Number(queryParam(url, 'page') ?? '1')
      const pageSize = Number(queryParam(url, 'page_size') ?? '20')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ ...paginate(items, page, pageSize), total: items.length }, 'e2e-trace'),
        ),
      })
      return
    }

    if (path === `/stocktakes/${stocktakeOrder.id}` && method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(stocktakeOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/stocktakes/${stocktakeOrder.id}/counts` && method === 'POST') {
      stocktakeOrder = {
        ...stocktakeOrder,
        lines: stocktakeOrder.lines.map((line) => ({
          ...line,
          counted_qty: '10',
          diff_qty: '0',
        })),
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(apiEnvelope(stocktakeOrder, 'e2e-trace')),
      })
      return
    }

    if (path === `/stocktakes/${stocktakeOrder.id}/approve` && method === 'POST') {
      stocktakeOrder = { ...stocktakeOrder, status: 'approved', approved_by: 1 }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(
          apiEnvelope({ order: stocktakeOrder, replayed: false }, 'e2e-trace'),
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
