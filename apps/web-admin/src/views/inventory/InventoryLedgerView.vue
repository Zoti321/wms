<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listInventoryLedgers } from '@/api/inventories'
import { listLocations } from '@/api/locations'
import { listSkus } from '@/api/skus'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { INVENTORY_REF_TYPE_LABEL } from '@/constants/labels'
import { useAppStore } from '@/stores/app'
import type { InventoryLedger, Location, Sku } from '@/types/api'
import {
  buildLocationCodeById,
  buildSkuLabelById,
  labelFromMap,
  skuOptionLabel,
} from '@/utils/catalogLabels'
import { errorMessage } from '@/utils/errorMessage'
import { formatDateTime } from '@/utils/formatDateTime'
import { resolveLedgerRefRoute } from '@/utils/inventoryLedger'

const app = useAppStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)
const optionsLoading = ref(false)
const items = ref<InventoryLedger[]>([])
const total = ref(0)
const skuOptions = ref<Sku[]>([])
const locationOptions = ref<Location[]>([])

const filters = reactive({
  sku_id: undefined as number | undefined,
  ref_line_id: undefined as number | undefined,
  ref_id: undefined as number | undefined,
  ref_type: undefined as string | undefined,
  page: 1,
  page_size: 20,
})

const refLineIdInput = ref('')
const refIdInput = ref('')

const skuLabelById = computed(() => buildSkuLabelById(skuOptions.value))
const locationCodeById = computed(() => buildLocationCodeById(locationOptions.value))

const hasActiveFilters = computed(
  () =>
    filters.sku_id != null ||
    filters.ref_line_id != null ||
    filters.ref_id != null ||
    filters.ref_type != null,
)

const emptyText = computed(() => {
  if (app.warehouseId == null) {
    return '请先确认仓库上下文'
  }
  if (hasActiveFilters.value) {
    return '未找到符合条件的流水记录，请调整筛选条件'
  }
  return '暂无数据'
})

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
    const page = await listInventoryLedgers({
      warehouse_id: app.warehouseId,
      sku_id: filters.sku_id,
      ref_line_id: filters.ref_line_id,
      ref_id: filters.ref_id,
      ref_type: filters.ref_type,
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
  filters.ref_line_id = parseOptionalId(refLineIdInput.value)
  filters.ref_id = parseOptionalId(refIdInput.value)
  if (refLineIdInput.value.trim() && filters.ref_line_id == null) {
    ElMessage.warning('单据行 ID 须为数字')
    return
  }
  if (refIdInput.value.trim() && filters.ref_id == null) {
    ElMessage.warning('关联单据 ID 须为数字')
    return
  }
  filters.page = 1
  void loadList()
}

function onReset(): void {
  refLineIdInput.value = ''
  refIdInput.value = ''
  filters.sku_id = undefined
  filters.ref_line_id = undefined
  filters.ref_id = undefined
  filters.ref_type = undefined
  filters.page = 1
  void loadList()
}

function skuLabel(skuId: number): string {
  return labelFromMap(skuLabelById.value, skuId)
}

function locationLabel(locationId: number): string {
  return labelFromMap(locationCodeById.value, locationId)
}

function refTypeLabel(refType: string): string {
  return INVENTORY_REF_TYPE_LABEL[refType] ?? refType
}

function goRefDetail(row: InventoryLedger): void {
  const target = resolveLedgerRefRoute(row)
  if (target == null) {
    return
  }
  void router.push(target)
}

watch(
  () => app.warehouseId,
  () => {
    filters.page = 1
    void loadCatalogOptions()
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
  void loadCatalogOptions()
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>库存流水</span>
    </div>

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
      <el-form-item label="单据行 ID">
        <el-input
          v-model="refLineIdInput"
          clearable
          placeholder="单据行 ID"
          style="width: 140px"
        />
      </el-form-item>
      <el-form-item label="关联单据 ID">
        <el-input
          v-model="refIdInput"
          clearable
          placeholder="入库/出库/盘点单 ID"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item label="来源类型">
        <el-select
          v-model="filters.ref_type"
          clearable
          placeholder="全部"
          style="width: 140px"
        >
          <el-option
            v-for="(label, value) in INVENTORY_REF_TYPE_LABEL"
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
      <el-table-column prop="id" label="ID" width="80">
        <template #default="{ row }">
          <span class="font-data">{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" min-width="170">
        <template #default="{ row }">
          <span class="font-data">{{ formatDateTime(row.created_at) }}</span>
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
      <el-table-column prop="ref_type" label="来源" width="100">
        <template #default="{ row }">
          {{ refTypeLabel(row.ref_type) }}
        </template>
      </el-table-column>
      <el-table-column prop="ref_no" label="单号" min-width="140">
        <template #default="{ row }">
          <el-button
            v-if="resolveLedgerRefRoute(row)"
            link
            type="primary"
            class="font-data"
            @click="goRefDetail(row)"
          >
            {{ row.ref_no }}
          </el-button>
          <span v-else class="font-data">{{ row.ref_no || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="ref_line_id" label="单据行" width="90">
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
