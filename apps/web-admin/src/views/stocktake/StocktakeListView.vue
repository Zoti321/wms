<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listStocktakes } from '@/api/stocktakes'
import {
  STOCKTAKE_STATUS_LABEL,
  STOCKTAKE_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { StocktakeOrderListItem, StocktakeStatus } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'
import { formatDateTime } from '@/utils/formatDateTime'

const app = useAppStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const items = ref<StocktakeOrderListItem[]>([])
const total = ref(0)

const statusValues = Object.keys(STOCKTAKE_STATUS_LABEL) as StocktakeStatus[]

function statusFromQuery(): StocktakeStatus | undefined {
  const raw = route.query.status
  return typeof raw === 'string' && statusValues.includes(raw as StocktakeStatus)
    ? (raw as StocktakeStatus)
    : undefined
}

const filters = reactive({
  status: statusFromQuery(),
  page: 1,
  page_size: 20,
})

async function loadList(): Promise<void> {
  if (app.warehouseId == null) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const page = await listStocktakes({
      warehouse_id: app.warehouseId,
      status: filters.status,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载盘点单失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.page = 1
  void loadList()
}

function onReset(): void {
  filters.status = undefined
  filters.page = 1
  void loadList()
}

function goCreate(): void {
  void router.push({ name: ROUTE_NAMES.stocktakeCreate })
}

function goDetail(id: number): void {
  void router.push({ name: ROUTE_NAMES.stocktakeDetail, params: { id } })
}

function statusLabel(status: StocktakeStatus): string {
  return STOCKTAKE_STATUS_LABEL[status]
}

function statusTagType(status: StocktakeStatus) {
  return STOCKTAKE_STATUS_TAG_TYPE[status]
}

watch(
  () => app.warehouseId,
  () => {
    filters.page = 1
    void loadList()
  },
)

watch(
  () => route.query.status,
  () => {
    filters.status = statusFromQuery()
    filters.page = 1
    void loadList()
  },
)

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>盘点单</span>
      <el-button v-permission="'stocktake:write'" type="primary" @click="goCreate">
        发起盘点
      </el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
          <el-option
            v-for="(label, value) in STOCKTAKE_STATUS_LABEL"
            :key="value"
            :value="value"
            :label="label"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无数据">
      <el-table-column prop="order_no" label="单号" min-width="160">
        <template #default="{ row }">
          <el-button link type="primary" class="font-data" @click="goDetail(row.id)">
            {{ row.order_no }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="170">
        <template #default="{ row }">
          <span class="font-data">{{ formatDateTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无盘点单">
          <el-button v-permission="'stocktake:write'" type="primary" @click="goCreate">
            发起盘点
          </el-button>
        </el-empty>
      </template>
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
