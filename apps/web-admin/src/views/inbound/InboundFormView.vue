<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'

import { createInboundOrder } from '@/api/inboundOrders'
import { listSkus } from '@/api/skus'
import { listSuppliers } from '@/api/suppliers'
import { INBOUND_ORDER_TYPE_LABEL } from '@/constants/labels'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import type { InboundOrderType, Sku, Supplier } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

interface LineForm {
  sku_id: number | undefined
  planned_qty: string
}

const app = useAppStore()
const router = useRouter()

const formRef = ref<FormInstance>()
const saving = ref(false)
const skuOptions = ref<Sku[]>([])
const supplierOptions = ref<Supplier[]>([])

const form = reactive({
  order_type: 'purchase' as InboundOrderType,
  supplier_id: undefined as number | undefined,
  remark: '',
  lines: [{ sku_id: undefined, planned_qty: '' }] as LineForm[],
})

const formRules: FormRules = {
  order_type: [{ required: true, message: '请选择入库类型', trigger: 'change' }],
}

async function loadOptions(): Promise<void> {
  try {
    const [skus, suppliers] = await Promise.all([
      listSkus({ selectable: true, status: 1, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
      listSuppliers({ selectable: true, status: 1, page: 1, page_size: MAX_LIST_PAGE_SIZE }),
    ])
    skuOptions.value = skus.items
    supplierOptions.value = suppliers.items
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载选项失败'))
  }
}

function addLine(): void {
  form.lines.push({ sku_id: undefined, planned_qty: '' })
}

function removeLine(index: number): void {
  if (form.lines.length <= 1) {
    return
  }
  form.lines.splice(index, 1)
}

async function onSubmit(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  if (app.warehouseId == null) {
    ElMessage.warning('请先绑定仓库')
    return
  }

  const lines = form.lines
    .filter((line) => line.sku_id != null && line.planned_qty.trim() !== '')
    .map((line) => ({
      sku_id: line.sku_id as number,
      planned_qty: line.planned_qty.trim(),
    }))

  if (lines.length === 0) {
    ElMessage.warning('请至少添加一行有效明细')
    return
  }

  saving.value = true
  try {
    const order = await createInboundOrder({
      warehouse_id: app.warehouseId,
      order_type: form.order_type,
      supplier_id: form.supplier_id ?? null,
      remark: form.remark.trim() || null,
      lines,
    })
    ElMessage.success('创建成功')
    await router.replace({ name: ROUTE_NAMES.inboundDetail, params: { id: order.id } })
  } catch (error) {
    ElMessage.error(errorMessage(error, '创建失败'))
  } finally {
    saving.value = false
  }
}

function goBack(): void {
  void router.push({ name: ROUTE_NAMES.inboundList })
}

onMounted(() => {
  void loadOptions()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>新建入库单</span>
      <el-button @click="goBack">返回列表</el-button>
    </div>

    <el-alert
      v-if="app.warehouseReady && app.warehouseId == null"
      type="warning"
      :closable="false"
      show-icon
      title="未绑定仓库，无法创建入库单。"
      style="margin-bottom: 12px"
    />

    <el-form
      ref="formRef"
      :model="form"
      :rules="formRules"
      label-width="96px"
      style="max-width: 880px"
    >
      <el-form-item label="入库类型" prop="order_type">
        <el-select v-model="form.order_type" style="width: 240px">
          <el-option
            v-for="(label, value) in INBOUND_ORDER_TYPE_LABEL"
            :key="value"
            :value="value"
            :label="label"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="供应商">
        <el-select
          v-model="form.supplier_id"
          clearable
          filterable
          placeholder="可选"
          style="width: 240px"
        >
          <el-option
            v-for="item in supplierOptions"
            :key="item.id"
            :value="item.id"
            :label="`${item.supplier_code} · ${item.name}`"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>

      <el-form-item label="明细行">
        <div class="lines">
          <div v-for="(line, index) in form.lines" :key="index" class="line-row">
            <el-select
              v-model="line.sku_id"
              filterable
              clearable
              placeholder="选择 SKU"
              style="width: 280px"
            >
              <el-option
                v-for="sku in skuOptions"
                :key="sku.id"
                :value="sku.id"
                :label="`${sku.sku_code} · ${sku.name}`"
              />
            </el-select>
            <el-input
              v-model="line.planned_qty"
              placeholder="计划数量"
              style="width: 140px"
            />
            <el-button
              :icon="Delete"
              :disabled="form.lines.length <= 1"
              @click="removeLine(index)"
            />
          </div>
          <el-button :icon="Plus" @click="addLine">添加行</el-button>
        </div>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="app.warehouseId == null"
          @click="onSubmit"
        >
          创建草稿
        </el-button>
        <el-button @click="goBack">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.line-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
</style>
