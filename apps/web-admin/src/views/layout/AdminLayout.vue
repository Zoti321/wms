<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Box,
  DataAnalysis,
  Document,
  Goods,
  HomeFilled,
  OfficeBuilding,
  Sell,
  Setting,
  TakeawayBox,
  User,
} from '@element-plus/icons-vue'

import { SIDE_MENU, type SideMenuEntry } from '@/router/menu'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const app = useAppStore()
const router = useRouter()
const route = useRoute()

const iconMap: Record<string, typeof HomeFilled> = {
  '/dashboard': HomeFilled,
  主数据: OfficeBuilding,
  '/inbound': TakeawayBox,
  '/outbound': Sell,
  库存: Box,
  系统管理: Setting,
  '/catalog/skus': Goods,
  '/catalog/locations': OfficeBuilding,
  '/inventory': Box,
  '/inventory/ledgers': Box,
  '/platform/users': User,
  '/platform/dictionaries': Document,
  '/platform/operation-logs': Document,
  '/platform/reports/daily': DataAnalysis,
}

function visible(permission?: string): boolean {
  return !permission || auth.hasPermission(permission)
}

const menuEntries = computed(() => {
  const result: SideMenuEntry[] = []
  for (const entry of SIDE_MENU) {
    if (!visible(entry.permission)) {
      continue
    }
    if (entry.kind === 'item') {
      result.push(entry)
      continue
    }
    const children = entry.children.filter((child) => visible(child.permission))
    if (children.length === 0) {
      continue
    }
    result.push({ ...entry, children })
  }
  return result
})

const activeMenu = computed(() => route.path)

function onLogout(): void {
  auth.logout()
  app.clearWarehouse()
  void router.push({ name: 'login' })
}

onMounted(() => {
  void app.ensureWarehouse()
})
</script>

<template>
  <el-container class="admin-layout">
    <el-aside :width="'var(--sidebar-width)'" class="admin-aside">
      <div class="brand">仓脉 WMS</div>
      <el-menu :default-active="activeMenu" router>
        <template v-for="entry in menuEntries" :key="entry.title">
          <el-sub-menu v-if="entry.kind === 'group'" :index="entry.title">
            <template #title>
              <el-icon><component :is="iconMap[entry.title] ?? Box" /></el-icon>
              <span>{{ entry.title }}</span>
            </template>
            <el-menu-item
              v-for="child in entry.children"
              :key="child.path"
              :index="child.path"
            >
              <el-icon><component :is="iconMap[child.path] ?? Goods" /></el-icon>
              <span>{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>
          <el-menu-item v-else :index="entry.path">
            <el-icon><component :is="iconMap[entry.path] ?? HomeFilled" /></el-icon>
            <span>{{ entry.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header" height="var(--header-height)">
        <div class="header-left">
          <span class="page-title">{{ route.meta.title ?? '管理后台' }}</span>
          <el-tag v-if="app.warehouseName" type="info" effect="plain" size="small">
            当前仓库：{{ app.warehouseName }}
          </el-tag>
          <el-tag v-else-if="app.warehouseReady" type="warning" effect="plain" size="small">
            未绑定仓库
          </el-tag>
        </div>
        <div class="header-right">
          <span class="username">{{ auth.user?.username }}</span>
          <el-button link type="primary" @click="onLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.admin-layout {
  min-height: 100vh;
}

.admin-aside {
  border-right: 1px solid var(--color-border);
  background: var(--color-card);
}

.brand {
  padding: 20px 16px 12px;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-primary);
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-card);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  color: var(--color-muted-foreground);
}

.admin-main {
  background: var(--color-background);
  padding: var(--content-padding);
}
</style>
