<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { listInventoryBalances } from '@/api/inventories'
import { listLocations } from '@/api/locations'
import { listSkus } from '@/api/skus'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { useAppStore } from '@/stores/app'
import type { InventoryBalance, Location, Sku } from '@/types/api'
import {
  buildLocationCodeById,
  buildSkuLabelById,
  labelFromMap,
  skuOptionLabel,
} from '@/utils/catalogLabels'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()

const loading = ref(false)
const optionsLoading = ref(false)
const items = ref<InventoryBalance[]>([])
const total = ref(0)
const skuOptions = ref<Sku[]>([])
const locationOptions = ref<Location[]>([])

const filters = reactive({
  sku_id: undefined as number | undefined,
  location_id: undefined as number | undefined,
  page: 1,
  page_size: 20,
})

const skuLabelById = computed(() => buildSkuLabelById(skuOptions.value))
const locationCodeById = computed(() => buildLocationCodeById(locationOptions.value))

const hasActiveFilters = computed(
  () => filters.sku_id != null || filters.location_id != null,
)

const emptyText = computed(() => {
  if (app.warehouseId == null) {
    return '请先确认仓库上下文'
  }
  if (hasActiveFilters.value) {
    return '未找到符合条件的库存余额，请调整筛选条件'
  }
  return '暂无数据'
})

async function loadCatalogOptions(): Promise<void> {
  optionsLoading.value = true
  try {
    const warehouseId = app.warehouseId
    const [skus, locations] = await Promise.all([
      listSkus({ selectable: true, status: 1, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
      warehouseId != null
        ? listLocations({
            warehouse_id: warehouseId,
            selectable: true,
            status: 1,
            page: 1,
            page_size: MAX_LIST_PAGE_SIZE,
          })
        : Promise.resolve({ items: [], total: 0, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
    ])
    skuOptions.value = skus.items
    locationOptions.value = locations.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载筛选选项失败'))
  } finally {
    optionsLoading.value = false
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
  filters.page = 1
  void loadList()
}

function onReset(): void {
  filters.sku_id = undefined
  filters.location_id = undefined
  filters.page = 1
  void loadList()
}

function skuLabel(skuId: number): string {
  return labelFromMap(skuLabelById.value, skuId)
}

function locationLabel(locationId: number): string {
  return labelFromMap(locationCodeById.value, locationId)
}

watch(
  () => app.warehouseId,
  () => {
    filters.location_id = undefined
    filters.page = 1
    void loadCatalogOptions()
    void loadList()
  },
)

onMounted(() => {
  void loadCatalogOptions()
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
      <el-form-item label="SKU">
        <el-select
          v-model="filters.sku_id"
          clearable
          filterable
          placeholder="全部"
          :loading="optionsLoading"
          style="width: 280px"
        >
          <el-option
            v-for="sku in skuOptions"
            :key="sku.id"
            :value="sku.id"
            :label="skuOptionLabel(sku)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="库位">
        <el-select
          v-model="filters.location_id"
          clearable
          filterable
          placeholder="全部"
          :loading="optionsLoading"
          :disabled="app.warehouseId == null"
          style="width: 200px"
        >
          <el-option
            v-for="loc in locationOptions"
            :key="loc.id"
            :value="loc.id"
            :label="loc.location_code"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" :empty-text="emptyText">
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
      <el-table-column label="SKU" min-width="200">
        <template #default="{ row }">
          {{ skuLabel(row.sku_id) }}
        </template>
      </el-table-column>
      <el-table-column label="库位" width="120">
        <template #default="{ row }">
          <span class="font-data">{{ locationLabel(row.location_id) }}</span>
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
