<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { listInventoryAlerts } from '@/api/inventories'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const app = useAppStore()
const router = useRouter()

const openAlertCount = ref<number | null>(null)

const shortcuts = computed(() => {
  const items: { title: string; desc: string; route: string; permission?: string }[] = [
    {
      title: 'SKU',
      desc: '维护物料主数据',
      route: ROUTE_NAMES.catalogSkus,
      permission: 'catalog:read',
    },
    {
      title: '库位',
      desc: '维护当前仓库库位',
      route: ROUTE_NAMES.catalogLocations,
      permission: 'catalog:read',
    },
    {
      title: '入库单',
      desc: '查看与处理入库',
      route: ROUTE_NAMES.inboundList,
      permission: 'inbound:read',
    },
    {
      title: '出库单',
      desc: '查看与处理出库',
      route: ROUTE_NAMES.outboundList,
      permission: 'outbound:read',
    },
    {
      title: '盘点单',
      desc: '发起盘点与审核调账',
      route: ROUTE_NAMES.stocktakeList,
      permission: 'stocktake:read',
    },
    {
      title: '库存余额',
      desc: '查询在库与可用数量',
      route: ROUTE_NAMES.inventoryBalances,
      permission: 'inventory:read',
    },
    {
      title: '库存预警',
      desc: '查看低库存预警',
      route: ROUTE_NAMES.inventoryAlerts,
      permission: 'inventory:read',
    },
  ]
  return items.filter((item) => !item.permission || auth.hasPermission(item.permission))
})

function goPendingInbound(): void {
  void router.push({
    name: ROUTE_NAMES.inboundList,
    query: { status: 'pending' },
  })
}

function goPendingOutbound(): void {
  void router.push({
    name: ROUTE_NAMES.outboundList,
    query: { status: 'pending' },
  })
}

function goCountingStocktakes(): void {
  void router.push({
    name: ROUTE_NAMES.stocktakeList,
    query: { status: 'counting' },
  })
}

function goInventoryAlerts(): void {
  void router.push({ name: ROUTE_NAMES.inventoryAlerts })
}

function go(name: string): void {
  void router.push({ name })
}

async function loadOpenAlertCount(): Promise<void> {
  if (!auth.hasPermission('inventory:read') || app.warehouseId == null) {
    openAlertCount.value = null
    return
  }
  try {
    const page = await listInventoryAlerts({
      warehouse_id: app.warehouseId,
      page: 1,
      page_size: 1,
    })
    openAlertCount.value = page.total
  } catch {
    openAlertCount.value = null
  }
}

onMounted(() => {
  void loadOpenAlertCount()
})
</script>

<template>
  <div class="page-panel workbench">
    <div class="page-toolbar">
      <span>工作台</span>
    </div>

    <p class="greeting">
      你好，{{ auth.user?.username }}（{{ auth.user?.role_code }}）。
    </p>

    <p class="warehouse-line">
      <template v-if="app.warehouseName">
        当前仓库：<strong>{{ app.warehouseName }}</strong>
      </template>
      <template v-else-if="app.warehouseReady">
        <el-text type="warning">尚未绑定仓库（需系统中仅有一个启用仓库）。</el-text>
      </template>
      <template v-else>正在确认仓库上下文…</template>
    </p>

    <div
      v-if="
        auth.hasPermission('inbound:read') ||
        auth.hasPermission('outbound:read') ||
        auth.hasPermission('stocktake:read') ||
        (auth.hasPermission('inventory:read') && openAlertCount != null && openAlertCount > 0)
      "
      class="todo-row"
    >
      <span>待办</span>
      <el-button
        v-if="auth.hasPermission('inbound:read')"
        link
        type="primary"
        @click="goPendingInbound"
      >
        待审核入库单
      </el-button>
      <el-button
        v-if="auth.hasPermission('outbound:read')"
        link
        type="primary"
        @click="goPendingOutbound"
      >
        待审核出库单
      </el-button>
      <el-button
        v-if="auth.hasPermission('stocktake:read')"
        link
        type="primary"
        @click="goCountingStocktakes"
      >
        进行中盘点
      </el-button>
      <el-button
        v-if="auth.hasPermission('inventory:read') && openAlertCount != null && openAlertCount > 0"
        link
        type="danger"
        @click="goInventoryAlerts"
      >
        低库存预警 ({{ openAlertCount }})
      </el-button>
    </div>

    <div class="shortcuts">
      <button
        v-for="item in shortcuts"
        :key="item.route"
        type="button"
        class="shortcut"
        @click="go(item.route)"
      >
        <span class="shortcut-title">{{ item.title }}</span>
        <span class="shortcut-desc">{{ item.desc }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.workbench {
  max-width: 720px;
}

.greeting {
  margin: 0 0 8px;
}

.warehouse-line {
  margin: 0 0 16px;
  color: var(--color-muted-foreground);
}

.todo-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.shortcuts {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 8px;
}

.shortcut {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  text-align: left;
  font: inherit;
  color: inherit;
}

.shortcut:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.shortcut-title {
  font-weight: 600;
}

.shortcut-desc {
  font-size: 12px;
  color: var(--color-muted-foreground);
}

.shortcut:hover .shortcut-desc {
  color: inherit;
}
</style>
