<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import { createSku, deactivateSku, listSkus, updateSku } from '@/api/skus'
import { ACTIVE_STATUS_LABEL } from '@/constants/labels'
import type { Sku, SkuCreate } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const loading = ref(false)
const items = ref<Sku[]>([])
const total = ref(0)

const filters = reactive({
  code: '',
  name: '',
  status: undefined as number | undefined,
  page: 1,
  page_size: 20,
})

const dialogVisible = ref(false)
const dialogSaving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  sku_code: '',
  name: '',
  unit: '',
  spec: '',
  barcode: '',
  safety_stock: '0',
})

const formRules: FormRules = {
  sku_code: [{ required: true, message: '请输入 SKU 编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  unit: [{ required: true, message: '请输入单位', trigger: 'blur' }],
  safety_stock: [{ required: true, message: '请输入安全库存', trigger: 'blur' }],
}

async function loadList(): Promise<void> {
  loading.value = true
  try {
    const page = await listSkus({
      code: filters.code || undefined,
      name: filters.name || undefined,
      status: filters.status,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载 SKU 失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.page = 1
  void loadList()
}

function onReset(): void {
  filters.code = ''
  filters.name = ''
  filters.status = undefined
  filters.page = 1
  void loadList()
}

function resetForm(): void {
  form.sku_code = ''
  form.name = ''
  form.unit = ''
  form.spec = ''
  form.barcode = ''
  form.safety_stock = '0'
  formRef.value?.clearValidate()
}

function openCreate(): void {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Sku): void {
  editingId.value = row.id
  form.sku_code = row.sku_code
  form.name = row.name
  form.unit = row.unit
  form.spec = row.spec ?? ''
  form.barcode = row.barcode ?? ''
  form.safety_stock = row.safety_stock
  dialogVisible.value = true
}

async function onSave(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  dialogSaving.value = true
  try {
    if (editingId.value == null) {
      const payload: SkuCreate = {
        sku_code: form.sku_code.trim(),
        name: form.name.trim(),
        unit: form.unit.trim(),
        spec: form.spec.trim() || null,
        barcode: form.barcode.trim() || null,
        safety_stock: form.safety_stock,
      }
      await createSku(payload)
      ElMessage.success('创建成功')
    } else {
      await updateSku(editingId.value, {
        name: form.name.trim(),
        unit: form.unit.trim(),
        spec: form.spec.trim() || null,
        barcode: form.barcode.trim() || null,
        safety_stock: form.safety_stock,
      })
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '保存失败'))
  } finally {
    dialogSaving.value = false
  }
}

async function onDeactivate(row: Sku): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认停用 SKU「${row.sku_code}」？`, '停用确认', {
      type: 'warning',
      confirmButtonText: '停用',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deactivateSku(row.id)
    ElMessage.success('已停用')
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '停用失败'))
  }
}

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>SKU 列表</span>
      <el-button v-permission="'catalog:write'" type="primary" @click="openCreate">新建 SKU</el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="编码">
        <el-input v-model="filters.code" clearable placeholder="SKU 编码" />
      </el-form-item>
      <el-form-item label="名称">
        <el-input v-model="filters.name" clearable placeholder="名称" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="filters.status" clearable placeholder="全部" style="width: 120px">
          <el-option :value="1" label="启用" />
          <el-option :value="0" label="停用" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无数据">
      <el-table-column prop="sku_code" label="编码" min-width="120">
        <template #default="{ row }">
          <span class="font-data">{{ row.sku_code }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="spec" label="规格" min-width="100" show-overflow-tooltip />
      <el-table-column prop="barcode" label="条码" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="font-data">{{ row.barcode || '—' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="safety_stock" label="安全库存" width="100" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.safety_stock }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ ACTIVE_STATUS_LABEL[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button
            v-permission="'catalog:write'"
            link
            type="primary"
            @click="openEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-if="row.status === 1"
            v-permission="'catalog:write'"
            link
            type="danger"
            @click="onDeactivate(row)"
          >
            停用
          </el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无 SKU">
          <el-button v-permission="'catalog:write'" type="primary" @click="openCreate">
            新建 SKU
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId == null ? '新建 SKU' : '编辑 SKU'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px">
        <el-form-item label="SKU 编码" prop="sku_code">
          <el-input v-model="form.sku_code" :disabled="editingId != null" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="form.unit" />
        </el-form-item>
        <el-form-item label="规格" prop="spec">
          <el-input v-model="form.spec" />
        </el-form-item>
        <el-form-item label="条码" prop="barcode">
          <el-input v-model="form.barcode" />
        </el-form-item>
        <el-form-item label="安全库存" prop="safety_stock">
          <el-input v-model="form.safety_stock" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
