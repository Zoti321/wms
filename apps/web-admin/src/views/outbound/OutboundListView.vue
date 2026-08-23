<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listOutboundOrders } from '@/api/outboundOrders'
import {
  OUTBOUND_ORDER_TYPE_LABEL,
  OUTBOUND_STATUS_LABEL,
  OUTBOUND_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { OutboundOrderListItem, OutboundOrderType, OutboundStatus } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const items = ref<OutboundOrderListItem[]>([])
const total = ref(0)

const statusValues = Object.keys(OUTBOUND_STATUS_LABEL) as OutboundStatus[]

function statusFromQuery(): OutboundStatus | undefined {
  const raw = route.query.status
  return typeof raw === 'string' && statusValues.includes(raw as OutboundStatus)
    ? (raw as OutboundStatus)
    : undefined
}

const filters = reactive({
  status: statusFromQuery(),
  order_no: '',
  order_type: undefined as OutboundOrderType | undefined,
  page: 1,
  page_size: 20,
})

const hasActiveFilters = computed(
  () =>
    filters.status != null ||
    filters.order_no.trim() !== '' ||
    filters.order_type != null,
)

const emptyText = computed(() => {
  if (app.warehouseId == null) {
    return '请先确认仓库上下文'
  }
  if (hasActiveFilters.value) {
    return '未找到符合条件的出库单，请调整筛选条件'
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
    const page = await listOutboundOrders({
      warehouse_id: app.warehouseId,
      status: filters.status,
      order_no: filters.order_no.trim() || undefined,
      order_type: filters.order_type,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载出库单失败'))
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
  filters.order_no = ''
  filters.order_type = undefined
  filters.page = 1
  void loadList()
}

function goCreate(): void {
  void router.push({ name: ROUTE_NAMES.outboundCreate })
}

function goDetail(id: number): void {
  void router.push({ name: ROUTE_NAMES.outboundDetail, params: { id } })
}

function statusLabel(status: OutboundStatus): string {
  return OUTBOUND_STATUS_LABEL[status]
}

function statusTagType(status: OutboundStatus) {
  return OUTBOUND_STATUS_TAG_TYPE[status]
}

function orderTypeLabel(orderType: string): string {
  return OUTBOUND_ORDER_TYPE_LABEL[orderType] ?? orderType
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
      <span>出库单</span>
      <el-button v-permission="'outbound:write'" type="primary" @click="goCreate">
        新建出库单
      </el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="单号">
        <el-input
          v-model="filters.order_no"
          clearable
          placeholder="单号关键字"
          style="width: 180px"
        />
      </el-form-item>
      <el-form-item label="类型">
        <el-select
          v-model="filters.order_type"
          clearable
          placeholder="全部"
          style="width: 140px"
        >
          <el-option
            v-for="(label, value) in OUTBOUND_ORDER_TYPE_LABEL"
            :key="value"
            :value="value"
            :label="label"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 140px">
          <el-option
            v-for="(label, value) in OUTBOUND_STATUS_LABEL"
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
        <el-empty description="暂无出库单">
          <el-button v-permission="'outbound:write'" type="primary" @click="goCreate">
            新建出库单
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
