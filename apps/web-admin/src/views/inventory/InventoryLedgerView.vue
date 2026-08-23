<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listInventoryLedgers } from '@/api/inventories'
import { useAppStore } from '@/stores/app'
import type { InventoryLedger } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()
const route = useRoute()

const loading = ref(false)
const items = ref<InventoryLedger[]>([])
const total = ref(0)

const filters = reactive({
  sku_id: undefined as number | undefined,
  ref_line_id: undefined as number | undefined,
  ref_type: '',
  page: 1,
  page_size: 20,
})

const skuIdInput = ref('')
const refLineIdInput = ref('')

function parseOptionalId(raw: string): number | undefined {
  const trimmed = raw.trim()
  if (!trimmed) {
    return undefined
  }
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : undefined
}

function applyQuery(): void {
  const fromQuery = route.query.ref_line_id
  if (typeof fromQuery === 'string' && fromQuery.trim()) {
    refLineIdInput.value = fromQuery
    filters.ref_line_id = parseOptionalId(fromQuery)
  }
}

async function loadList(): Promise<void> {
  if (app.warehouseId == null) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const page = await listInventoryLedgers({
      warehouse_id: app.warehouseId,
      sku_id: filters.sku_id,
      ref_line_id: filters.ref_line_id,
      ref_type: filters.ref_type || undefined,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库存流水失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.sku_id = parseOptionalId(skuIdInput.value)
  filters.ref_line_id = parseOptionalId(refLineIdInput.value)
  if (
    (skuIdInput.value.trim() && filters.sku_id == null) ||
    (refLineIdInput.value.trim() && filters.ref_line_id == null)
  ) {
    ElMessage.warning('SKU / 行 ID 须为数字')
    return
  }
  filters.page = 1
  void loadList()
}

function onReset(): void {
  skuIdInput.value = ''
  refLineIdInput.value = ''
  filters.sku_id = undefined
  filters.ref_line_id = undefined
  filters.ref_type = ''
  filters.page = 1
  void loadList()
}

watch(
  () => app.warehouseId,
  () => {
    filters.page = 1
    void loadList()
  },
)

watch(
  () => route.query.ref_line_id,
  () => {
    applyQuery()
    filters.page = 1
    void loadList()
  },
)

onMounted(() => {
  applyQuery()
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>库存流水</span>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="SKU ID">
        <el-input v-model="skuIdInput" clearable placeholder="可选" style="width: 140px" />
      </el-form-item>
      <el-form-item label="业务行 ID">
        <el-input
          v-model="refLineIdInput"
          clearable
          placeholder="ref_line_id"
          style="width: 140px"
        />
      </el-form-item>
      <el-form-item label="来源类型">
        <el-input v-model="filters.ref_type" clearable placeholder="如 inbound" style="width: 140px" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无数据">
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
      <el-table-column prop="sku_id" label="SKU" width="90">
        <template #default="{ row }">
          <span class="font-data">{{ row.sku_id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="location_id" label="库位" width="90">
        <template #default="{ row }">
          <span class="font-data">{{ row.location_id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="change_qty" label="变动" width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.change_qty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="bal_qty" label="结余" width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.bal_qty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="ref_type" label="来源" width="100" />
      <el-table-column prop="ref_no" label="单号" min-width="140">
        <template #default="{ row }">
          <span class="font-data">{{ row.ref_no || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="ref_line_id" label="业务行" width="90">
        <template #default="{ row }">
          <span class="font-data">{{ row.ref_line_id ?? '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="operator_id" label="操作人" width="90">
        <template #default="{ row }">
          {{ row.operator_id ?? '—' }}
        </template>
      </el-table-column>
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
