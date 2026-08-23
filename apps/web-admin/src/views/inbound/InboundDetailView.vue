<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  approveInboundOrder,
  cancelInboundOrder,
  getInboundOrder,
  putawayInboundOrder,
  submitInboundOrder,
} from '@/api/inboundOrders'
import { listLocations } from '@/api/locations'
import { listSkus } from '@/api/skus'
import { listSuppliers } from '@/api/suppliers'
import CancelReasonDialog from '@/components/CancelReasonDialog.vue'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import {
  INBOUND_ORDER_TYPE_LABEL,
  INBOUND_STATUS_LABEL,
  INBOUND_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { InboundOrder, InboundOrderLine, Location, Sku, Supplier } from '@/types/api'
import {
  buildSkuLabelById,
  buildSupplierLabelById,
  labelFromMap,
} from '@/utils/catalogLabels'
import {
  dictLabelFromMap,
  fetchActiveDictOptions,
  loadDictLabelMap,
  type DictOption,
} from '@/utils/dictOptions'
import { errorMessage } from '@/utils/errorMessage'
import { parseCancelReasonFromRemark } from '@/utils/orderRemark'

const route = useRoute()
const router = useRouter()
const app = useAppStore()

const loading = ref(false)
const actionLoading = ref(false)
const order = ref<InboundOrder | null>(null)
const locationOptions = ref<Location[]>([])
const skuOptions = ref<Sku[]>([])
const supplierOptions = ref<Supplier[]>([])

const cancelDialogVisible = ref(false)
const cancelReasonOptions = ref<DictOption[]>([])
const cancelReasonLoading = ref(false)
const orderTypeLabelMap = ref(new Map<string, string>())

const skuLabelById = computed(() => buildSkuLabelById(skuOptions.value))
const supplierLabelById = computed(() => buildSupplierLabelById(supplierOptions.value))

const remarkParts = computed(() => parseCancelReasonFromRemark(order.value?.remark))

const orderTypeLabel = computed(() => {
  if (!order.value) {
    return '—'
  }
  return dictLabelFromMap(
    orderTypeLabelMap.value,
    order.value.order_type,
    INBOUND_ORDER_TYPE_LABEL,
  )
})

const putawayVisible = ref(false)
const putawaySaving = ref(false)
const putawayFormRef = ref<FormInstance>()
const putawayForm = reactive({
  line_id: 0,
  location_id: undefined as number | undefined,
  qty: '',
})

const putawayRules: FormRules = {
  location_id: [{ required: true, message: '请选择库位', trigger: 'change' }],
  qty: [{ required: true, message: '请输入上架数量', trigger: 'blur' }],
}

const orderId = computed(() => Number(route.params.id))

const canPutaway = computed(
  () => order.value?.status === 'approved' || order.value?.status === 'putaway',
)

async function loadOrder(): Promise<void> {
  if (!Number.isFinite(orderId.value)) {
    ElMessage.error('无效的入库单 ID')
    return
  }

  loading.value = true
  try {
    order.value = await getInboundOrder(orderId.value)
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载入库单失败'))
  } finally {
    loading.value = false
  }
}

async function loadCatalogOptions(): Promise<void> {
  try {
    const [skus, suppliers] = await Promise.all([
      listSkus({ selectable: true, status: 1, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
      listSuppliers({ selectable: true, status: 1, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
    ])
    skuOptions.value = skus.items
    supplierOptions.value = suppliers.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载主数据选项失败'))
  }
}

async function loadLocations(): Promise<void> {
  const warehouseId = order.value?.warehouse_id ?? app.warehouseId
  if (warehouseId == null) {
    locationOptions.value = []
    return
  }

  try {
    const page = await listLocations({
      warehouse_id: warehouseId,
      selectable: true,
      status: 1,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    locationOptions.value = page.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库位失败'))
  }
}

function supplierLabel(supplierId: number | null): string {
  if (supplierId == null) {
    return '—'
  }
  return labelFromMap(supplierLabelById.value, supplierId)
}

async function runAction(
  action: () => Promise<InboundOrder>,
  successMessage: string,
  confirmText?: string,
): Promise<void> {
  if (confirmText) {
    try {
      await ElMessageBox.confirm(confirmText, '确认操作', {
        type: 'warning',
        confirmButtonText: '确认',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
  }

  actionLoading.value = true
  try {
    order.value = await action()
    ElMessage.success(successMessage)
  } catch (error) {
    ElMessage.error(errorMessage(error, '操作失败'))
  } finally {
    actionLoading.value = false
  }
}

function onSubmit(): void {
  void runAction(
    () => submitInboundOrder(orderId.value),
    '已提交审核',
    '确认提交该入库单？',
  )
}

function onApprove(): void {
  void runAction(
    () => approveInboundOrder(orderId.value),
    '审核通过',
    '确认审核该入库单？',
  )
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
    order.value = await cancelInboundOrder(
      orderId.value,
      cancelReasonCode ? { cancel_reason_code: cancelReasonCode } : undefined,
    )
    ElMessage.success('已取消')
  } catch (error) {
    ElMessage.error(errorMessage(error, '取消失败'))
  } finally {
    actionLoading.value = false
  }
}

function openPutaway(line: InboundOrderLine): void {
  putawayForm.line_id = line.id
  putawayForm.location_id = undefined
  const planned = Number(line.planned_qty)
  const putaway = Number(line.putaway_qty)
  const remain = Number.isFinite(planned) && Number.isFinite(putaway) ? planned - putaway : 0
  putawayForm.qty = remain > 0 ? String(remain) : ''
  putawayVisible.value = true
  void loadLocations()
}

async function onPutaway(): Promise<void> {
  const valid = await putawayFormRef.value?.validate().catch(() => false)
  if (!valid || putawayForm.location_id == null) {
    return
  }

  putawaySaving.value = true
  try {
    const result = await putawayInboundOrder(orderId.value, {
      line_id: putawayForm.line_id,
      location_id: putawayForm.location_id,
      qty: putawayForm.qty,
    })
    order.value = result.order
    putawayVisible.value = false
    ElMessage.success(result.replayed ? '上架已幂等重放' : '上架成功')
  } catch (error) {
    ElMessage.error(errorMessage(error, '上架失败'))
  } finally {
    putawaySaving.value = false
  }
}

function goLedgers(lineId: number): void {
  void router.push({
    name: ROUTE_NAMES.inventoryLedgers,
    query: { ref_line_id: String(lineId) },
  })
}

function goEdit(): void {
  void router.push({ name: ROUTE_NAMES.inboundEdit, params: { id: orderId.value } })
}

function goBack(): void {
  void router.push({ name: ROUTE_NAMES.inboundList })
}

watch(
  () => route.params.id,
  () => {
    void loadOrder()
  },
)

onMounted(() => {
  void loadCatalogOptions()
  void loadDictLabelMap('inbound_order_type', INBOUND_ORDER_TYPE_LABEL).then((map) => {
    orderTypeLabelMap.value = map
  })
  void loadOrder()
})
</script>

<template>
  <div v-loading="loading" class="page-panel">
    <div class="page-toolbar">
      <span>入库单详情</span>
      <div class="toolbar-actions">
        <template v-if="order?.status === 'draft'">
          <el-button
            v-permission="'inbound:write'"
            type="primary"
            :loading="actionLoading"
            @click="onSubmit"
          >
            提交
          </el-button>
          <el-button v-permission="'inbound:write'" @click="goEdit">编辑</el-button>
          <el-button
            v-permission="'inbound:write'"
            :loading="actionLoading"
            @click="onCancel"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="order?.status === 'pending'">
          <el-button
            v-permission="'inbound:approve'"
            type="primary"
            :loading="actionLoading"
            @click="onApprove"
          >
            审核
          </el-button>
          <el-button
            v-permission="'inbound:write'"
            :loading="actionLoading"
            @click="onCancel"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="order?.status === 'approved'">
          <el-button
            v-permission="'inbound:write'"
            :loading="actionLoading"
            @click="onCancel"
          >
            取消
          </el-button>
        </template>
        <el-button @click="goBack">返回列表</el-button>
      </div>
    </div>

    <template v-if="order">
      <el-descriptions :column="3" border size="small" class="detail-desc">
        <el-descriptions-item label="单号">
          <span class="font-data">{{ order.order_no }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          {{ orderTypeLabel }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="INBOUND_STATUS_TAG_TYPE[order.status]" size="small">
            {{ INBOUND_STATUS_LABEL[order.status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="仓库 ID">
          <span class="font-data">{{ order.warehouse_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="供应商">
          {{ supplierLabel(order.supplier_id) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          <span class="font-data">{{ order.created_at }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ order.created_by }}
        </el-descriptions-item>
        <el-descriptions-item
          v-if="order.status === 'cancelled' && remarkParts.cancelReason"
          label="取消原因"
        >
          {{ remarkParts.cancelReason }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ remarkParts.userRemark || '—' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-table :data="order.lines" size="small" class="lines-table">
        <el-table-column prop="id" label="行 ID" width="90">
          <template #default="{ row }">
            <span class="font-data">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sku_id" label="SKU" min-width="160">
          <template #default="{ row }">
            {{ labelFromMap(skuLabelById, row.sku_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="planned_qty" label="计划数量" width="120" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.planned_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="putaway_qty" label="已上架" width="120" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.putaway_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-button
              v-if="canPutaway"
              v-permission="'inbound:write'"
              link
              type="primary"
              @click="openPutaway(row)"
            >
              上架
            </el-button>
            <el-button link type="primary" @click="goLedgers(row.id)">查看流水</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <el-dialog v-model="putawayVisible" title="上架" width="440px" destroy-on-close>
      <el-form
        ref="putawayFormRef"
        :model="putawayForm"
        :rules="putawayRules"
        label-width="88px"
      >
        <el-form-item label="行 ID">
          <span class="font-data">{{ putawayForm.line_id }}</span>
        </el-form-item>
        <el-form-item label="库位" prop="location_id">
          <el-select
            v-model="putawayForm.location_id"
            filterable
            placeholder="选择库位"
            style="width: 100%"
          >
            <el-option
              v-for="loc in locationOptions"
              :key="loc.id"
              :value="loc.id"
              :label="loc.location_code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="qty">
          <el-input v-model="putawayForm.qty" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="putawayVisible = false">取消</el-button>
        <el-button type="primary" :loading="putawaySaving" @click="onPutaway">确认上架</el-button>
      </template>
    </el-dialog>

    <CancelReasonDialog
      v-model="cancelDialogVisible"
      title="取消入库单"
      confirm-text="确认取消"
      :loading="cancelReasonLoading || actionLoading"
      :options="cancelReasonOptions"
      @confirm="onConfirmCancel"
    />
  </div>
</template>

<style scoped>
.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.detail-desc {
  margin-bottom: 16px;
}

.lines-table {
  margin-top: 8px;
}
</style>
