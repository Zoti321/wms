<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  approveStocktake,
  cancelStocktake,
  getStocktake,
  recordStocktakeCounts,
} from '@/api/stocktakes'
import { listLocations } from '@/api/locations'
import { listSkus } from '@/api/skus'
import CancelReasonDialog from '@/components/CancelReasonDialog.vue'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import {
  STOCKTAKE_STATUS_LABEL,
  STOCKTAKE_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import type { Location, Sku, StocktakeOrder, StocktakeOrderLine } from '@/types/api'
import {
  buildLocationCodeById,
  buildSkuLabelById,
  labelFromMap,
} from '@/utils/catalogLabels'
import { errorMessage } from '@/utils/errorMessage'
import { fetchActiveDictOptions, type DictOption } from '@/utils/dictOptions'
import { parseCancelReasonFromRemark } from '@/utils/orderRemark'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const app = useAppStore()

const loading = ref(false)
const actionLoading = ref(false)
const savingCounts = ref(false)
const order = ref<StocktakeOrder | null>(null)
const skuOptions = ref<Sku[]>([])
const locationOptions = ref<Location[]>([])

const cancelDialogVisible = ref(false)
const cancelReasonOptions = ref<DictOption[]>([])
const cancelReasonLoading = ref(false)

const skuLabelById = computed(() => buildSkuLabelById(skuOptions.value))
const locationCodeById = computed(() => buildLocationCodeById(locationOptions.value))

const remarkParts = computed(() => parseCancelReasonFromRemark(order.value?.remark))

/** line_id → 编辑中的实盘数量字符串 */
const countDrafts = reactive<Record<number, string>>({})

const orderId = computed(() => Number(route.params.id))

const isCounting = computed(() => order.value?.status === 'counting')

const canEditCounts = computed(
  () => isCounting.value && auth.hasPermission('stocktake:write'),
)

const diffSummary = computed(() => {
  if (!order.value) {
    return { total: 0, withDiff: 0, gain: 0, loss: 0 }
  }
  let withDiff = 0
  let gain = 0
  let loss = 0
  for (const line of order.value.lines) {
    if (line.diff_qty == null) {
      continue
    }
    const diff = Number(line.diff_qty)
    if (!Number.isFinite(diff) || diff === 0) {
      continue
    }
    withDiff += 1
    if (diff > 0) {
      gain += diff
    } else {
      loss += Math.abs(diff)
    }
  }
  return { total: order.value.lines.length, withDiff, gain, loss }
})

function syncCountDrafts(lines: StocktakeOrderLine[]): void {
  for (const key of Object.keys(countDrafts)) {
    delete countDrafts[Number(key)]
  }
  for (const line of lines) {
    countDrafts[line.id] = line.counted_qty ?? ''
  }
}

async function loadCatalogOptions(): Promise<void> {
  const warehouseId = order.value?.warehouse_id ?? app.warehouseId
  try {
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
    ElMessage.error(errorMessage(error, '加载主数据选项失败'))
  }
}

async function loadOrder(): Promise<void> {
  if (!Number.isFinite(orderId.value)) {
    ElMessage.error('无效的盘点单 ID')
    return
  }

  loading.value = true
  try {
    order.value = await getStocktake(orderId.value)
    syncCountDrafts(order.value.lines)
    void loadCatalogOptions()
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载盘点单失败'))
  } finally {
    loading.value = false
  }
}

function linesToSave(): { line_id: number; counted_qty: string }[] {
  if (!order.value) {
    return []
  }
  return order.value.lines
    .filter((line) => {
      const draft = countDrafts[line.id]?.trim() ?? ''
      return draft !== ''
    })
    .map((line) => ({
      line_id: line.id,
      counted_qty: countDrafts[line.id].trim(),
    }))
}

async function onSaveCounts(): Promise<void> {
  const lines = linesToSave()
  if (lines.length === 0) {
    ElMessage.warning('请至少录入一行实盘数量')
    return
  }

  savingCounts.value = true
  try {
    order.value = await recordStocktakeCounts(orderId.value, lines)
    syncCountDrafts(order.value.lines)
    ElMessage.success('实盘数量已保存')
  } catch (error) {
    ElMessage.error(errorMessage(error, '保存实盘失败'))
  } finally {
    savingCounts.value = false
  }
}

function approveConfirmText(): string {
  const { total, withDiff, gain, loss } = diffSummary.value
  const parts = [`共 ${total} 行`, `有差异 ${withDiff} 行`]
  if (gain > 0) {
    parts.push(`盘盈合计 ${gain}`)
  }
  if (loss > 0) {
    parts.push(`盘亏合计 ${loss}`)
  }
  return `确认审核该盘点单？${parts.join('，')}。审核后将调账并释放盘点锁。`
}

async function onApprove(): Promise<void> {
  try {
    await ElMessageBox.confirm(approveConfirmText(), '确认审核', {
      type: 'warning',
      confirmButtonText: '确认审核',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  actionLoading.value = true
  try {
    const result = await approveStocktake(orderId.value)
    order.value = result.order
    syncCountDrafts(order.value.lines)
    ElMessage.success(result.replayed ? '审核已幂等重放' : '审核完成，盘点锁已释放')
  } catch (error) {
    ElMessage.error(errorMessage(error, '审核失败'))
  } finally {
    actionLoading.value = false
  }
}

function onCancel(): void {
  cancelDialogVisible.value = true
  if (cancelReasonOptions.value.length === 0) {
    cancelReasonLoading.value = true
    void fetchActiveDictOptions('cancel_reason')
      .then((options) => {
        cancelReasonOptions.value = options
      })
      .catch(() => {
        cancelReasonOptions.value = []
      })
      .finally(() => {
        cancelReasonLoading.value = false
      })
  }
}

async function onConfirmCancel(cancelReasonCode: string | undefined): Promise<void> {
  actionLoading.value = true
  try {
    const result = await cancelStocktake(
      orderId.value,
      cancelReasonCode ? { cancel_reason_code: cancelReasonCode } : undefined,
    )
    order.value = result.order
    syncCountDrafts(order.value.lines)
    ElMessage.success(result.replayed ? '取消已幂等重放' : '已取消，盘点锁已释放')
  } catch (error) {
    ElMessage.error(errorMessage(error, '取消失败'))
  } finally {
    actionLoading.value = false
  }
}

function goLedgers(lineId: number): void {
  void router.push({
    name: ROUTE_NAMES.inventoryLedgers,
    query: { ref_line_id: String(lineId) },
  })
}

function goStocktakeLedgers(): void {
  void router.push({
    name: ROUTE_NAMES.inventoryLedgers,
    query: { ref_type: 'STOCKTAKE', ref_id: String(orderId.value) },
  })
}

function goBack(): void {
  void router.push({ name: ROUTE_NAMES.stocktakeList })
}

function diffDisplay(line: StocktakeOrderLine): string {
  if (line.diff_qty == null) {
    return '—'
  }
  const diff = Number(line.diff_qty)
  if (!Number.isFinite(diff)) {
    return line.diff_qty
  }
  if (diff > 0) {
    return `+${line.diff_qty}（盘盈）`
  }
  if (diff < 0) {
    return `${line.diff_qty}（盘亏）`
  }
  return '0'
}

watch(
  () => route.params.id,
  () => {
    void loadOrder()
  },
)

onMounted(() => {
  void loadOrder()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>盘点单详情</span>
      <div class="actions">
        <el-button
          v-if="isCounting"
          v-permission="'stocktake:write'"
          type="primary"
          :loading="savingCounts"
          @click="onSaveCounts"
        >
          保存实盘
        </el-button>
        <el-button
          v-if="isCounting"
          v-permission="'stocktake:approve'"
          type="success"
          :loading="actionLoading"
          @click="onApprove"
        >
          审核
        </el-button>
        <el-button
          v-if="isCounting"
          v-permission="'stocktake:write'"
          type="danger"
          :loading="actionLoading"
          @click="onCancel"
        >
          取消
        </el-button>
        <el-button
          v-if="order?.status === 'approved'"
          link
          type="primary"
          @click="goStocktakeLedgers"
        >
          查看流水
        </el-button>
        <el-button @click="goBack">返回列表</el-button>
      </div>
    </div>

    <el-skeleton v-if="loading && !order" :rows="6" animated />

    <template v-else-if="order">
      <el-descriptions :column="2" border size="small" class="meta">
        <el-descriptions-item label="单号">
          <span class="font-data">{{ order.order_no }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="STOCKTAKE_STATUS_TAG_TYPE[order.status]" size="small">
            {{ STOCKTAKE_STATUS_LABEL[order.status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="库区">
          {{ order.zone ?? '全仓' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          <span class="font-data">{{ order.created_at }}</span>
        </el-descriptions-item>
        <el-descriptions-item
          v-if="order.status === 'cancelled' && remarkParts.cancelReason"
          label="取消原因"
        >
          {{ remarkParts.cancelReason }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ remarkParts.userRemark ?? '—' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-alert
        v-if="isCounting"
        type="warning"
        :closable="false"
        show-icon
        title="盘点锁已生效：覆盖库位禁止上架与拣货。审核前库存余额不变。"
        style="margin: 12px 0"
      />

      <el-table :data="order.lines" size="small" style="margin-top: 12px">
        <el-table-column prop="location_id" label="库位" width="120">
          <template #default="{ row }">
            <span class="font-data">{{ labelFromMap(locationCodeById, row.location_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sku_id" label="SKU" min-width="160">
          <template #default="{ row }">
            {{ labelFromMap(skuLabelById, row.sku_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="book_qty" label="账面数量" width="120">
          <template #default="{ row }">
            <span class="font-data">{{ row.book_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="实盘数量" width="160">
          <template #default="{ row }">
            <el-input
              v-if="canEditCounts"
              v-model="countDrafts[row.id]"
              size="small"
              placeholder="录入实盘"
              class="font-data"
            />
            <span v-else class="font-data">{{ row.counted_qty ?? '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="差异" min-width="140">
          <template #default="{ row }">
            <span class="font-data">{{ diffDisplay(row) }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="order.status === 'approved'" label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click="goLedgers(row.id)">流水</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <CancelReasonDialog
      v-model="cancelDialogVisible"
      title="取消盘点单"
      confirm-text="确认取消"
      :loading="cancelReasonLoading || actionLoading"
      :options="cancelReasonOptions"
      @confirm="onConfirmCancel"
    />
  </div>
</template>

<style scoped>
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.meta {
  margin-bottom: 8px;
}
</style>
