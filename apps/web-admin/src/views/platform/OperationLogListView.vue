<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { listOperationLogs } from '@/api/operationLogs'
import { OPERATION_ACTION_LABEL } from '@/constants/labels'
import type { OperationLog } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const ACTION_OPTIONS = Object.keys(OPERATION_ACTION_LABEL)

const loading = ref(false)
const items = ref<OperationLog[]>([])
const total = ref(0)

const filters = reactive({
  operator_id: undefined as number | undefined,
  action: '',
  dateRange: null as [Date, Date] | null,
  page: 1,
  page_size: 20,
})

function formatDateTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

async function loadList(): Promise<void> {
  loading.value = true
  try {
    const page = await listOperationLogs({
      operator_id: filters.operator_id,
      action: filters.action || undefined,
      created_from: filters.dateRange?.[0] ? formatDateTime(filters.dateRange[0]) : undefined,
      created_to: filters.dateRange?.[1] ? formatDateTime(filters.dateRange[1]) : undefined,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载操作日志失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.page = 1
  void loadList()
}

function onReset(): void {
  filters.operator_id = undefined
  filters.action = ''
  filters.dateRange = null
  filters.page = 1
  void loadList()
}

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>操作日志</span>
    </div>

    <el-alert
      class="page-filters"
      type="info"
      :closable="false"
      show-icon
      title="操作日志记录登录、用户管理、字典变更、单据审核等敏感操作；库存变动请查「库存流水」。"
    />

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="操作人 ID">
        <el-input-number
          v-model="filters.operator_id"
          :min="1"
          controls-position="right"
          placeholder="全部"
          style="width: 140px"
        />
      </el-form-item>
      <el-form-item label="动作">
        <el-select v-model="filters.action" clearable placeholder="全部" style="width: 160px">
          <el-option
            v-for="action in ACTION_OPTIONS"
            :key="action"
            :value="action"
            :label="OPERATION_ACTION_LABEL[action] ?? action"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="时间范围">
        <el-date-picker
          v-model="filters.dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始"
          end-placeholder="结束"
          style="width: 360px"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无日志">
      <el-table-column prop="id" label="ID" width="80">
        <template #default="{ row }">
          <span class="font-data">{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" min-width="170">
        <template #default="{ row }">
          <span class="font-data">{{ row.created_at }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="operator_name" label="操作人" width="120" />
      <el-table-column prop="action" label="动作" min-width="120">
        <template #default="{ row }">
          {{ OPERATION_ACTION_LABEL[row.action] ?? row.action }}
        </template>
      </el-table-column>
      <el-table-column prop="resource_type" label="资源类型" width="110">
        <template #default="{ row }">
          <span class="font-data">{{ row.resource_type || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="resource_id" label="资源 ID" width="100">
        <template #default="{ row }">
          <span class="font-data">{{ row.resource_id || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="detail" label="详情" min-width="160" show-overflow-tooltip />
    </el-table>

    <div class="page-pagination">
      <el-pagination
        v-model:current-page="filters.page"
        v-model:page-size="filters.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="loadList"
        @size-change="
          () => {
            filters.page = 1
            loadList()
          }
        "
      />
    </div>
  </div>
</template>
