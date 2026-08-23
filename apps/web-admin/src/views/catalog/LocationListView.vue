<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createLocation,
  deactivateLocation,
  listLocations,
  updateLocation,
} from '@/api/locations'
import { ACTIVE_STATUS_LABEL, SPACE_STATUS_LABEL } from '@/constants/labels'
import { useAppStore } from '@/stores/app'
import type { Location } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()

const loading = ref(false)
const items = ref<Location[]>([])
const total = ref(0)

const filters = reactive({
  code: '',
  status: undefined as number | undefined,
  space_status: undefined as string | undefined,
  page: 1,
  page_size: 20,
})

const dialogVisible = ref(false)
const dialogSaving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  location_code: '',
  zone: '',
  aisle: '',
  bin: '',
  space_status: 'idle' as 'idle' | 'occupied' | 'frozen',
})

const formRules: FormRules = {
  location_code: [{ required: true, message: '请输入库位编码', trigger: 'blur' }],
  space_status: [{ required: true, message: '请选择空间状态', trigger: 'change' }],
}

async function loadList(): Promise<void> {
  if (app.warehouseId == null) {
    items.value = []
    total.value = 0
    return
  }

  loading.value = true
  try {
    const page = await listLocations({
      warehouse_id: app.warehouseId,
      code: filters.code || undefined,
      status: filters.status,
      space_status: filters.space_status,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库位失败'))
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
  filters.status = undefined
  filters.space_status = undefined
  filters.page = 1
  void loadList()
}

function resetForm(): void {
  form.location_code = ''
  form.zone = ''
  form.aisle = ''
  form.bin = ''
  form.space_status = 'idle'
  formRef.value?.clearValidate()
}

function openCreate(): void {
  if (app.warehouseId == null) {
    ElMessage.warning('请先绑定仓库')
    return
  }
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: Location): void {
  editingId.value = row.id
  form.location_code = row.location_code
  form.zone = row.zone ?? ''
  form.aisle = row.aisle ?? ''
  form.bin = row.bin ?? ''
  form.space_status = row.space_status
  dialogVisible.value = true
}

async function onSave(): Promise<void> {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid || app.warehouseId == null) {
    return
  }

  dialogSaving.value = true
  try {
    if (editingId.value == null) {
      await createLocation({
        warehouse_id: app.warehouseId,
        location_code: form.location_code.trim(),
        zone: form.zone.trim() || null,
        aisle: form.aisle.trim() || null,
        bin: form.bin.trim() || null,
        space_status: form.space_status,
      })
      ElMessage.success('创建成功')
    } else {
      await updateLocation(editingId.value, {
        zone: form.zone.trim() || null,
        aisle: form.aisle.trim() || null,
        bin: form.bin.trim() || null,
        space_status: form.space_status,
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

async function onDeactivate(row: Location): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认停用库位「${row.location_code}」？`, '停用确认', {
      type: 'warning',
      confirmButtonText: '停用',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deactivateLocation(row.id)
    ElMessage.success('已停用')
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '停用失败'))
  }
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
      <span>库位列表</span>
      <el-button
        v-permission="'catalog:write'"
        type="primary"
        :disabled="app.warehouseId == null"
        @click="openCreate"
      >
        新建库位
      </el-button>
    </div>

    <el-alert
      v-if="app.warehouseReady && app.warehouseId == null"
      class="page-filters"
      type="warning"
      :closable="false"
      show-icon
      title="未绑定仓库，无法查询或维护库位。请确认系统中仅有一个启用仓库。"
    />

    <template v-else>
      <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
        <el-form-item label="编码">
          <el-input v-model="filters.code" clearable placeholder="库位编码" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.status" clearable placeholder="全部" style="width: 120px">
            <el-option :value="1" label="启用" />
            <el-option :value="0" label="停用" />
          </el-select>
        </el-form-item>
        <el-form-item label="空间状态">
          <el-select
            v-model="filters.space_status"
            clearable
            placeholder="全部"
            style="width: 120px"
          >
            <el-option
              v-for="(label, value) in SPACE_STATUS_LABEL"
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

      <el-table v-loading="loading" :data="items" size="small" empty-text="暂无数据">
        <el-table-column prop="location_code" label="库位编码" min-width="120">
          <template #default="{ row }">
            <span class="font-data">{{ row.location_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="zone" label="库区" width="100" />
        <el-table-column prop="aisle" label="巷道" width="100" />
        <el-table-column prop="bin" label="货位" width="100" />
        <el-table-column prop="space_status" label="空间状态" width="100">
          <template #default="{ row }">
            {{ SPACE_STATUS_LABEL[row.space_status] ?? row.space_status }}
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
          <el-empty description="暂无库位">
            <el-button v-permission="'catalog:write'" type="primary" @click="openCreate">
              新建库位
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
    </template>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId == null ? '新建库位' : '编辑库位'"
      width="520px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="96px">
        <el-form-item label="库位编码" prop="location_code">
          <el-input v-model="form.location_code" :disabled="editingId != null" />
        </el-form-item>
        <el-form-item label="库区" prop="zone">
          <el-input v-model="form.zone" />
        </el-form-item>
        <el-form-item label="巷道" prop="aisle">
          <el-input v-model="form.aisle" />
        </el-form-item>
        <el-form-item label="货位" prop="bin">
          <el-input v-model="form.bin" />
        </el-form-item>
        <el-form-item label="空间状态" prop="space_status">
          <el-select v-model="form.space_status" style="width: 100%">
            <el-option
              v-for="(label, value) in SPACE_STATUS_LABEL"
              :key="value"
              :value="value"
              :label="label"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
