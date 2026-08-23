import { expect, test } from '@playwright/test'

import { installMockApi } from './fixtures/mockApi'

async function loginAsAdmin(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('用户名').fill('admin')
  await page.getByLabel('密码').fill('Admin@123456')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/dashboard/)
}

async function confirmDialog(page: import('@playwright/test').Page): Promise<void> {
  const confirmButton = page
    .locator('.el-message-box')
    .getByRole('button', { name: /确定|确认审核|确认/ })
  await expect(confirmButton.first()).toBeVisible()
  await confirmButton.first().click()
}

test.describe('core path smoke', () => {
  test.beforeEach(async ({ page }) => {
    await installMockApi(page)
  })

  test('login redirects to dashboard', async ({ page }) => {
    await loginAsAdmin(page)
    await expect(page.getByText('你好，admin（admin）')).toBeVisible()
    await expect(page.locator('.warehouse-line')).toContainText('E2E 主仓')
  })

  test('unknown route shows 404 page', async ({ page }) => {
    await loginAsAdmin(page)
    await page.goto('/this-route-does-not-exist')
    await expect(page.getByText('页面不存在或已被移除')).toBeVisible()
  })

  test('dashboard shows pending todo counts', async ({ page }) => {
    await loginAsAdmin(page)
    await expect(page.getByRole('button', { name: /待审核出库单 \(1\)/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /进行中盘点 \(1\)/ })).toBeVisible()
  })
})

test.describe('inbound happy path', () => {
  test.beforeEach(async ({ page }) => {
    await installMockApi(page)
    await loginAsAdmin(page)
  })

  test('submit, approve, and putaway draft inbound order', async ({ page }) => {
    await page.goto('/inbound/101')
    await expect(page.getByText('IN-E2E-001')).toBeVisible()
    await expect(page.getByText('草稿')).toBeVisible()

    await page.getByRole('button', { name: '提交' }).click()
    await confirmDialog(page)
    await expect(page.getByText('待审核')).toBeVisible()

    await page.getByRole('button', { name: '审核' }).click()
    await confirmDialog(page)
    await expect(page.getByText('已审核')).toBeVisible()

    await page.getByRole('button', { name: '上架' }).click()
    await page.getByLabel('库位').click()
    await page.getByRole('option', { name: 'A-01-01' }).click()
    await page.getByLabel('数量').fill('10')
    await page.getByRole('button', { name: '确认上架' }).click()
    await expect(page.getByText('已完成')).toBeVisible()
  })
})

test.describe('outbound happy path', () => {
  test.beforeEach(async ({ page }) => {
    await installMockApi(page)
    await loginAsAdmin(page)
  })

  test('approve and pick pending outbound order', async ({ page }) => {
    await page.goto('/outbound/201')
    await expect(page.getByText('OUT-E2E-001')).toBeVisible()
    await expect(page.getByText('待审核')).toBeVisible()

    await page.getByRole('button', { name: '审核' }).click()
    const approveDialog = page.getByRole('dialog', { name: '审核（分配）' })
    await expect(approveDialog).toBeVisible()
    await approveDialog.getByRole('combobox').click()
    await page.getByRole('option', { name: 'A-01-01' }).click()
    await approveDialog.getByRole('button', { name: '确认审核' }).click()
    await expect(page.getByText('已审核')).toBeVisible()

    await page.getByRole('button', { name: '拣货' }).click()
    await page.getByLabel('数量').fill('5')
    await page.getByRole('button', { name: '确认拣货' }).click()
    await expect(page.getByText('已完成')).toBeVisible()
  })
})

test.describe('stocktake happy path', () => {
  test.beforeEach(async ({ page }) => {
    await installMockApi(page)
    await loginAsAdmin(page)
  })

  test('count lines and approve stocktake', async ({ page }) => {
    await page.goto('/stocktakes/301')
    await expect(page.getByText('ST-E2E-001')).toBeVisible()
    await expect(page.getByText('盘点中')).toBeVisible()

    await page.getByPlaceholder('录入实盘').fill('10')
    await page.getByRole('button', { name: '保存实盘' }).click()
    await expect(page.getByText('实盘数量已保存')).toBeVisible()

    await page.getByRole('button', { name: '审核', exact: true }).click()
    await confirmDialog(page)
    await expect(page.getByText('已完成')).toBeVisible()
  })
})
