<script setup lang="ts">
import { useRouter } from 'vue-router'

import { ROUTE_NAMES } from '@/router/routes'

const router = useRouter()
</script>

<template>
  <el-result icon="warning" title="404" sub-title="页面不存在或已被移除">
    <template #extra>
      <el-button type="primary" @click="router.push({ name: ROUTE_NAMES.dashboard })">
        返回工作台
      </el-button>
    </template>
  </el-result>
</template>
