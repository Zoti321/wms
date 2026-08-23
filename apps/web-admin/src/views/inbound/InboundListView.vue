<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listInboundOrders } from '@/api/inboundOrders'
import {
  INBOUND_ORDER_TYPE_LABEL,
  INBOUND_STATUS_LABEL,
  INBOUND_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { InboundOrderListItem, InboundStatus } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const items = ref<InboundOrderListItem[]>([])
const total = ref(0)

const statusValues = Object.keys(INBOUND_STATUS_LABEL) as InboundStatus[]

function statusFromQuery(): InboundStatus | undefined {
  const raw = route.query.status
  return typeof raw === 'string' && statusValues.includes(raw as InboundStatus)
    ? (raw as InboundStatus)
    : undefined
}

const filters = reactive({
  status: statusFromQuery(),
  page: 1,
  page_size: 20,
})

const emptyText = computed(() => {
  if (app.warehouseId == null) {
    return '请先确认仓库上下文'
  }
  if (filters.status != null) {
    return '未找到符合条件的入库单，请调整筛选条件'
  }
  return '暂无数据'
})

async function loadList(): Promise<void> {
  if (app.warehouseId == null) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const page = await listInboundOrders({
      warehouse_id: app.warehouseId,
      status: filters.status,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载入库单失败'))
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
  void router.push({ name: ROUTE_NAMES.inboundCreate })
}

function goDetail(id: number): void {
  void router.push({ name: ROUTE_NAMES.inboundDetail, params: { id } })
}

function statusLabel(status: InboundStatus): string {
  return INBOUND_STATUS_LABEL[status]
}

function statusTagType(status: InboundStatus) {
  return INBOUND_STATUS_TAG_TYPE[status]
}

function orderTypeLabel(orderType: string): string {
  return INBOUND_ORDER_TYPE_LABEL[orderType] ?? orderType
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
      <span>入库单</span>
      <el-button v-permission="'inbound:write'" type="primary" @click="goCreate">
        新建入库单
      </el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
          <el-option
            v-for="(label, value) in INBOUND_STATUS_LABEL"
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

    <el-table v-loading="loading" :data="items" size="small" :empty-text="emptyText">
      <el-table-column prop="order_no" label="单号" min-width="160">
        <template #default="{ row }">
          <el-button link type="primary" class="font-data" @click="goDetail(row.id)">
            {{ row.order_no }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column prop="order_type" label="类型" width="120">
        <template #default="{ row }">
          {{ orderTypeLabel(row.order_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)" size="small">
            {{ statusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="supplier_id" label="供应商" width="100">
        <template #default="{ row }">
          {{ row.supplier_id ?? '—' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" min-width="170">
        <template #default="{ row }">
          <span class="font-data">{{ row.created_at }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="goDetail(row.id)">详情</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无入库单">
          <el-button v-permission="'inbound:write'" type="primary" @click="goCreate">
            新建入库单
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
