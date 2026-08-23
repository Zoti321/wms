<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { listInventoryBalances } from '@/api/inventories'
import { useAppStore } from '@/stores/app'
import type { InventoryBalance } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()

const loading = ref(false)
const items = ref<InventoryBalance[]>([])
const total = ref(0)

const filters = reactive({
  sku_id: undefined as number | undefined,
  location_id: undefined as number | undefined,
  page: 1,
  page_size: 20,
})

const skuIdInput = ref('')
const locationIdInput = ref('')

function parseOptionalId(raw: string): number | undefined {
  const trimmed = raw.trim()
  if (!trimmed) {
    return undefined
  }
  const value = Number(trimmed)
  return Number.isFinite(value) ? value : undefined
}

async function loadList(): Promise<void> {
  if (app.warehouseId == null) {
    items.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const page = await listInventoryBalances({
      warehouse_id: app.warehouseId,
      sku_id: filters.sku_id,
      location_id: filters.location_id,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库存余额失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.sku_id = parseOptionalId(skuIdInput.value)
  filters.location_id = parseOptionalId(locationIdInput.value)
  if (
    (skuIdInput.value.trim() && filters.sku_id == null) ||
    (locationIdInput.value.trim() && filters.location_id == null)
  ) {
    ElMessage.warning('SKU / 库位 ID 须为数字')
    return
  }
  filters.page = 1
  void loadList()
}

function onReset(): void {
  skuIdInput.value = ''
  locationIdInput.value = ''
  filters.sku_id = undefined
  filters.location_id = undefined
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

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>库存余额</span>
    </div>

    <el-alert
      v-if="app.warehouseReady && app.warehouseId == null"
      class="page-filters"
      type="warning"
      :closable="false"
      show-icon
      title="未绑定仓库，结果可能跨仓混合；建议先确认仓库上下文。"
    />

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="SKU ID">
        <el-input v-model="skuIdInput" clearable placeholder="可选" style="width: 140px" />
      </el-form-item>
      <el-form-item label="库位 ID">
        <el-input
          v-model="locationIdInput"
          clearable
          placeholder="可选"
          style="width: 140px"
        />
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
      <el-table-column prop="warehouse_id" label="仓库" width="90">
        <template #default="{ row }">
          <span class="font-data">{{ row.warehouse_id }}</span>
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
      <el-table-column prop="qty_on_hand" label="在库" min-width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.qty_on_hand }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="qty_frozen" label="冻结" min-width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.qty_frozen }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="qty_available" label="可用" min-width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.qty_available }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="version" label="版本" width="80" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.version }}</span>
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
