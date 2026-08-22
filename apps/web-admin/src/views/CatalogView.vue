<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <el-card shadow="never">
    <template #header>主数据</template>
    <p>占位页：后续对接仓库 / SKU / 库位 CRUD。</p>
    <el-button v-permission="'catalog:write'" type="primary">新建 SKU（需 catalog:write）</el-button>
    <el-button @click="router.push({ name: 'dashboard' })">返回工作台</el-button>
  </el-card>
</template>
