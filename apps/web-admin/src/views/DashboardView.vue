<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <el-card shadow="never">
    <template #header>工作台</template>
    <p>欢迎，{{ auth.user?.username }}（{{ auth.user?.role_code }}）。</p>
    <p class="hint">网页后台骨架已就绪，后续在此对接各业务模块列表与表单。</p>
  </el-card>
</template>

<style scoped>
.hint {
  color: var(--el-text-color-secondary);
}
</style>
