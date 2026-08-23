<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import { listInventoryBalances } from '@/api/inventories'
import { listLocations } from '@/api/locations'
import {
  approveOutboundOrder,
  cancelOutboundOrder,
  getOutboundOrder,
  pickOutboundOrder,
  submitOutboundOrder,
} from '@/api/outboundOrders'
import {
  OUTBOUND_ORDER_TYPE_LABEL,
  OUTBOUND_STATUS_LABEL,
  OUTBOUND_STATUS_TAG_TYPE,
} from '@/constants/labels'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { Location, OutboundOrder, OutboundOrderLine } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

interface ApproveLineRow {
  line_id: number
  sku_id: number
  planned_qty: string
  location_id: number | undefined
  available_qty: string | null
  loading_available: boolean
}

const route = useRoute()
const router = useRouter()
const app = useAppStore()

const loading = ref(false)
const actionLoading = ref(false)
const order = ref<OutboundOrder | null>(null)
const locationOptions = ref<Location[]>([])
const locationLabelById = computed(() => {
  const map = new Map<number, string>()
  for (const loc of locationOptions.value) {
    map.set(loc.id, loc.location_code)
  }
  return map
})

const approveVisible = ref(false)
const approveSaving = ref(false)
const approveRows = ref<ApproveLineRow[]>([])

const pickVisible = ref(false)
const pickSaving = ref(false)
const pickFormRef = ref<FormInstance>()
const pickForm = reactive({
  line_id: 0,
  location_id: 0,
  qty: '',
})

const pickRules: FormRules = {
  qty: [{ required: true, message: '请输入拣货数量', trigger: 'blur' }],
}

const orderId = computed(() => Number(route.params.id))

const canPick = computed(
  () => order.value?.status === 'approved' || order.value?.status === 'picking',
)

const canCancel = computed(() => {
  const status = order.value?.status
  return (
    status === 'draft' ||
    status === 'pending' ||
    status === 'approved' ||
    status === 'picking'
  )
})

function lineRemainQty(line: OutboundOrderLine): number {
  const allocated = Number(line.allocated_qty)
  const picked = Number(line.picked_qty)
  if (!Number.isFinite(allocated) || !Number.isFinite(picked)) {
    return 0
  }
  return allocated - picked
}

function canPickLine(line: OutboundOrderLine): boolean {
  return canPick.value && lineRemainQty(line) > 0
}

async function loadOrder(): Promise<void> {
  if (!Number.isFinite(orderId.value)) {
    ElMessage.error('无效的出库单 ID')
    return
  }

  loading.value = true
  try {
    order.value = await getOutboundOrder(orderId.value)
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载出库单失败'))
  } finally {
    loading.value = false
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
      page_size: 200,
    })
    locationOptions.value = page.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库位失败'))
  }
}

async function loadAvailableQty(row: ApproveLineRow): Promise<void> {
  if (row.location_id == null || order.value == null) {
    row.available_qty = null
    return
  }

  row.loading_available = true
  try {
    const page = await listInventoryBalances({
      warehouse_id: order.value.warehouse_id,
      sku_id: row.sku_id,
      location_id: row.location_id,
      page: 1,
      page_size: 1,
    })
    row.available_qty = page.items[0]?.qty_available ?? '0'
  } catch {
    row.available_qty = null
  } finally {
    row.loading_available = false
  }
}

async function runOrderAction(
  action: () => Promise<OutboundOrder>,
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
  void runOrderAction(
    () => submitOutboundOrder(orderId.value),
    '已提交审核',
    '确认提交该出库单？',
  )
}

function onCancel(): void {
  void (async () => {
    try {
      await ElMessageBox.confirm('确认取消该出库单？', '确认操作', {
        type: 'warning',
        confirmButtonText: '确认',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }

    actionLoading.value = true
    try {
      const result = await cancelOutboundOrder(orderId.value)
      order.value = result.order
      if (result.note) {
        ElMessage.warning(result.note)
      } else {
        ElMessage.success(result.replayed ? '取消已幂等重放' : '已取消')
      }
    } catch (error) {
      ElMessage.error(errorMessage(error, '取消失败'))
    } finally {
      actionLoading.value = false
    }
  })()
}

function openApprove(): void {
  if (!order.value) {
    return
  }
  approveRows.value = order.value.lines.map((line) => ({
    line_id: line.id,
    sku_id: line.sku_id,
    planned_qty: line.planned_qty,
    location_id: undefined,
    available_qty: null,
    loading_available: false,
  }))
  approveVisible.value = true
  void loadLocations()
}

async function onApproveLocationChange(row: ApproveLineRow): Promise<void> {
  await loadAvailableQty(row)
}

async function onApprove(): Promise<void> {
  if (approveRows.value.some((row) => row.location_id == null)) {
    ElMessage.warning('请为每一行选择分配库位')
    return
  }

  approveSaving.value = true
  try {
    const result = await approveOutboundOrder(orderId.value, {
      allocations: approveRows.value.map((row) => ({
        line_id: row.line_id,
        location_id: row.location_id as number,
      })),
    })
    order.value = result.order
    approveVisible.value = false
    ElMessage.success(result.replayed ? '审核已幂等重放' : '审核通过，分配完成')
  } catch (error) {
    ElMessage.error(errorMessage(error, '审核失败'))
  } finally {
    approveSaving.value = false
  }
}

function openPick(line: OutboundOrderLine): void {
  if (line.location_id == null) {
    ElMessage.warning('该行尚未分配库位')
    return
  }
  pickForm.line_id = line.id
  pickForm.location_id = line.location_id
  const remain = lineRemainQty(line)
  pickForm.qty = remain > 0 ? String(remain) : ''
  pickVisible.value = true
}

async function onPick(): Promise<void> {
  const valid = await pickFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  pickSaving.value = true
  try {
    const result = await pickOutboundOrder(orderId.value, {
      line_id: pickForm.line_id,
      location_id: pickForm.location_id,
      qty: pickForm.qty,
    })
    order.value = result.order
    pickVisible.value = false
    ElMessage.success(result.replayed ? '拣货已幂等重放' : '拣货成功')
  } catch (error) {
    ElMessage.error(errorMessage(error, '拣货失败'))
  } finally {
    pickSaving.value = false
  }
}

function goEdit(): void {
  void router.push({ name: ROUTE_NAMES.outboundEdit, params: { id: orderId.value } })
}

function goLedgers(lineId: number): void {
  void router.push({
    name: ROUTE_NAMES.inventoryLedgers,
    query: { ref_line_id: String(lineId) },
  })
}

function goBack(): void {
  void router.push({ name: ROUTE_NAMES.outboundList })
}

function locationLabel(locationId: number | null): string {
  if (locationId == null) {
    return '—'
  }
  return locationLabelById.value.get(locationId) ?? String(locationId)
}

watch(
  () => route.params.id,
  () => {
    void loadOrder()
  },
)

onMounted(() => {
  void loadOrder()
  void loadLocations()
})
</script>

<template>
  <div v-loading="loading" class="page-panel">
    <div class="page-toolbar">
      <span>出库单详情</span>
      <div class="toolbar-actions">
        <template v-if="order?.status === 'draft'">
          <el-button
            v-permission="'outbound:write'"
            type="primary"
            :loading="actionLoading"
            @click="onSubmit"
          >
            提交
          </el-button>
          <el-button v-permission="'outbound:write'" @click="goEdit">编辑</el-button>
          <el-button
            v-permission="'outbound:write'"
            :loading="actionLoading"
            @click="onCancel"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="order?.status === 'pending'">
          <el-button
            v-permission="'outbound:approve'"
            type="primary"
            :loading="actionLoading"
            @click="openApprove"
          >
            审核
          </el-button>
          <el-button
            v-permission="'outbound:write'"
            :loading="actionLoading"
            @click="onCancel"
          >
            取消
          </el-button>
        </template>
        <template v-else-if="canCancel">
          <el-button
            v-permission="'outbound:write'"
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
          {{ OUTBOUND_ORDER_TYPE_LABEL[order.order_type] ?? order.order_type }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="OUTBOUND_STATUS_TAG_TYPE[order.status]" size="small">
            {{ OUTBOUND_STATUS_LABEL[order.status] }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="仓库 ID">
          <span class="font-data">{{ order.warehouse_id }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="客户">
          {{ order.customer_id ?? '—' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          <span class="font-data">{{ order.created_at }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="创建人">
          {{ order.created_by }}
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ order.remark || '—' }}
        </el-descriptions-item>
      </el-descriptions>

      <el-table :data="order.lines" size="small" class="lines-table">
        <el-table-column prop="id" label="行 ID" width="90">
          <template #default="{ row }">
            <span class="font-data">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sku_id" label="SKU ID" width="100">
          <template #default="{ row }">
            <span class="font-data">{{ row.sku_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_qty" label="计划数量" width="110" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.planned_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="allocated_qty" label="已分配" width="100" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.allocated_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="picked_qty" label="已拣" width="100" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.picked_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分配库位" width="120">
          <template #default="{ row }">
            <span class="font-data">{{ locationLabel(row.location_id) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-button
              v-if="canPickLine(row)"
              v-permission="'outbound:write'"
              link
              type="primary"
              @click="openPick(row)"
            >
              拣货
            </el-button>
            <el-button link type="primary" @click="goLedgers(row.id)">查看流水</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <el-dialog v-model="approveVisible" title="审核（分配）" width="720px" destroy-on-close>
      <p class="approve-hint">请为每一行出库单行指定分配库位，可用量不足时整单审核将失败。</p>
      <el-table :data="approveRows" size="small">
        <el-table-column prop="line_id" label="行 ID" width="80">
          <template #default="{ row }">
            <span class="font-data">{{ row.line_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="sku_id" label="SKU ID" width="90">
          <template #default="{ row }">
            <span class="font-data">{{ row.sku_id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="planned_qty" label="计划数量" width="100" align="right">
          <template #default="{ row }">
            <span class="qty-cell">{{ row.planned_qty }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分配库位" min-width="180">
          <template #default="{ row }">
            <el-select
              v-model="row.location_id"
              filterable
              placeholder="选择库位"
              style="width: 100%"
              @change="onApproveLocationChange(row)"
            >
              <el-option
                v-for="loc in locationOptions"
                :key="loc.id"
                :value="loc.id"
                :label="loc.location_code"
              />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="可用量" width="120" align="right">
          <template #default="{ row }">
            <span v-if="row.loading_available" class="font-data">…</span>
            <span v-else-if="row.available_qty != null" class="qty-cell">
              {{ row.available_qty }}
            </span>
            <span v-else>—</span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="approveVisible = false">取消</el-button>
        <el-button type="primary" :loading="approveSaving" @click="onApprove">
          确认审核
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pickVisible" title="拣货" width="440px" destroy-on-close>
      <el-form
        ref="pickFormRef"
        :model="pickForm"
        :rules="pickRules"
        label-width="88px"
      >
        <el-form-item label="行 ID">
          <span class="font-data">{{ pickForm.line_id }}</span>
        </el-form-item>
        <el-form-item label="库位">
          <span class="font-data">{{ locationLabel(pickForm.location_id) }}</span>
        </el-form-item>
        <el-form-item label="数量" prop="qty">
          <el-input v-model="pickForm.qty" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pickVisible = false">取消</el-button>
        <el-button type="primary" :loading="pickSaving" @click="onPick">确认拣货</el-button>
      </template>
    </el-dialog>
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

.approve-hint {
  margin: 0 0 12px;
  color: var(--color-muted-foreground);
  font-size: 13px;
}
</style>
