<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { listInventoryAlerts } from '@/api/inventories'
import { listSkus } from '@/api/skus'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import {
  INVENTORY_ALERT_STATUS_LABEL,
  INVENTORY_ALERT_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { useAppStore } from '@/stores/app'
import type { InventoryAlert, Sku } from '@/types/api'
import { buildSkuLabelById, labelFromMap } from '@/utils/catalogLabels'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()

const loading = ref(false)
const optionsLoading = ref(false)
const items = ref<InventoryAlert[]>([])
const total = ref(0)
const skuOptions = ref<Sku[]>([])

const filters = reactive({
  page: 1,
  page_size: 20,
})

const skuLabelById = computed(() => buildSkuLabelById(skuOptions.value))

async function loadCatalogOptions(): Promise<void> {
  optionsLoading.value = true
  try {
    const skus = await listSkus({
      selectable: true,
      status: 1,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    skuOptions.value = skus.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载 SKU 选项失败'))
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
    const page = await listInventoryAlerts({
      warehouse_id: app.warehouseId,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库存预警失败'))
  } finally {
    loading.value = false
  }
}

function skuLabel(skuId: number): string {
  return labelFromMap(skuLabelById.value, skuId)
}

watch(
  () => app.warehouseId,
  () => {
    filters.page = 1
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
      <span>库存预警</span>
    </div>

    <el-alert
      class="page-filters"
      type="info"
      :closable="false"
      show-icon
      title="展示当前仓库汇总可用量低于安全库存的有效预警；补货或入库上架后可用量回升，预警将自动解除。"
    />

    <el-table
      v-loading="loading"
      :data="items"
      size="small"
      :empty-text="app.warehouseId == null ? '请先确认仓库上下文' : '当前无低库存预警'"
    >
      <el-table-column prop="id" label="ID" width="80">
        <template #default="{ row }">
          <span class="font-data">{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column label="SKU" min-width="200">
        <template #default="{ row }">
          {{ skuLabel(row.sku_id) }}
        </template>
      </el-table-column>
      <el-table-column prop="qty_available" label="可用数量" min-width="120" align="right">
        <template #default="{ row }">
          <el-tag size="small" type="danger">{{ row.qty_available }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="safety_stock" label="安全库存" min-width="120" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.safety_stock }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag
            size="small"
            :type="INVENTORY_ALERT_STATUS_TAG_TYPE[row.status] ?? 'info'"
          >
            {{ INVENTORY_ALERT_STATUS_LABEL[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="触发时间" min-width="170">
        <template #default="{ row }">
          <span class="font-data">{{ row.created_at }}</span>
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
