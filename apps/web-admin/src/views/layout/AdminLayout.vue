<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { appRoutes } from '@/router/routes'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const menuRoutes = computed(() => {
  const layoutRoute = appRoutes.find((item) => item.path === '/')
  const children = layoutRoute?.children ?? []

  return children.filter((item) => {
    if (!item.meta?.menu || item.meta?.hideInMenu || !item.path) {
      return false
    }
    const permission = item.meta.permission as string | undefined
    return !permission || auth.hasPermission(permission)
  })
})

const activeMenu = computed(() => route.path)

function menuIndex(path: string): string {
  return path.startsWith('/') ? path : `/${path}`
}

function onLogout(): void {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <el-container class="admin-layout">
    <el-aside width="220px" class="admin-aside">
      <div class="brand">仓脉 WMS</div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item
          v-for="item in menuRoutes"
          :key="String(item.name)"
          :index="menuIndex(String(item.path))"
        >
          {{ item.meta?.title }}
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="admin-header">
        <div class="header-left">
          <span>{{ route.meta.title ?? '管理后台' }}</span>
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
  border-right: 1px solid var(--el-border-color-light);
  background: #fff;
}

.brand {
  padding: 20px 16px 12px;
  font-weight: 700;
  font-size: 1.1rem;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--el-border-color-light);
  background: #fff;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  color: var(--el-text-color-secondary);
}

.admin-main {
  background: #f5f7fa;
}
</style>
