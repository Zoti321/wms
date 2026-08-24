import { expect, test } from '@playwright/test'

import { installMockApi } from './fixtures/mockApi'

async function loginAsAdmin(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/login')
  await page.getByLabel('用户名').fill('admin')
  await page.getByLabel('密码').fill('Admin@123456')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page).toHaveURL(/\/dashboard/)
  await expect(page.getByText('你好，admin（admin）')).toBeVisible()
}

test.describe('core path smoke', () => {
  test.beforeEach(async ({ page }) => {
    await installMockApi(page)
  })

  test('login redirects to dashboard', async ({ page }) => {
    await loginAsAdmin(page)
    await expect(page.getByRole('main').getByText('工作台')).toBeVisible()
    await expect(page.locator('.warehouse-line')).toContainText('E2E 主仓')
  })

  test('dashboard shortcut opens SKU list', async ({ page }) => {
    await loginAsAdmin(page)
    await page.getByRole('button', { name: /SKU/ }).click()
    await expect(page).toHaveURL(/\/catalog\/skus/)
    await expect(page.getByText('SKU 列表')).toBeVisible()
    await expect(page.getByText('SKU-E2E')).toBeVisible()
  })
})
