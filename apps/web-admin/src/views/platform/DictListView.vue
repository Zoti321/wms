<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  createDictItem,
  deactivateDictItem,
  listDictItems,
  updateDictItem,
} from '@/api/dictionaries'
import { ACTIVE_STATUS_LABEL, DICT_TYPE_LABEL } from '@/constants/labels'
import type { CreateDictItemRequest, DictItem } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const DICT_TYPE_OPTIONS = [
  'unit',
  'inbound_order_type',
  'outbound_order_type',
  'cancel_reason',
] as const

const loading = ref(false)
const items = ref<DictItem[]>([])
const total = ref(0)

const filters = reactive({
  dict_type: '',
  page: 1,
  page_size: 20,
})

const dialogVisible = ref(false)
const dialogSaving = ref(false)
const editingId = ref<number | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  dict_type: '',
  code: '',
  name: '',
  sort_order: 0,
})

const formRules: FormRules = {
  dict_type: [{ required: true, message: '请选择字典类型', trigger: 'change' }],
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

async function loadList(): Promise<void> {
  loading.value = true
  try {
    const page = await listDictItems({
      dict_type: filters.dict_type || undefined,
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载字典失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  filters.page = 1
  void loadList()
}

function onReset(): void {
  filters.dict_type = ''
  filters.page = 1
  void loadList()
}

function resetForm(): void {
  form.dict_type = filters.dict_type || ''
  form.code = ''
  form.name = ''
  form.sort_order = 0
  formRef.value?.clearValidate()
}

function openCreate(): void {
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: DictItem): void {
  editingId.value = row.id
  form.dict_type = row.dict_type
  form.code = row.code
  form.name = row.name
  form.sort_order = row.sort_order
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
      const payload: CreateDictItemRequest = {
        dict_type: form.dict_type,
        code: form.code.trim(),
        name: form.name.trim(),
        sort_order: form.sort_order,
      }
      await createDictItem(payload)
      ElMessage.success('创建成功')
    } else {
      await updateDictItem(editingId.value, {
        name: form.name.trim(),
        sort_order: form.sort_order,
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

async function onDeactivate(row: DictItem): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认停用字典项「${row.code} - ${row.name}」？`, '停用确认', {
      type: 'warning',
      confirmButtonText: '停用',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deactivateDictItem(row.id)
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
      <span>字典管理</span>
      <el-button v-permission="'dict:write'" type="primary" @click="openCreate">
        新建字典项
      </el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="字典类型">
        <el-select
          v-model="filters.dict_type"
          clearable
          placeholder="全部"
          style="width: 160px"
        >
          <el-option
            v-for="type in DICT_TYPE_OPTIONS"
            :key="type"
            :value="type"
            :label="DICT_TYPE_LABEL[type] ?? type"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="onReset">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无字典项">
      <el-table-column prop="dict_type" label="类型" width="120">
        <template #default="{ row }">
          {{ DICT_TYPE_LABEL[row.dict_type] ?? row.dict_type }}
        </template>
      </el-table-column>
      <el-table-column prop="code" label="编码" min-width="100">
        <template #default="{ row }">
          <span class="font-data">{{ row.code }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="140" />
      <el-table-column prop="sort_order" label="排序" width="80" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.sort_order }}</span>
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
            v-permission="'dict:write'"
            link
            type="primary"
            @click="openEdit(row)"
          >
            编辑
          </el-button>
          <el-button
            v-if="row.status === 1"
            v-permission="'dict:write'"
            link
            type="danger"
            @click="onDeactivate(row)"
          >
            停用
          </el-button>
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

    <el-dialog
      v-model="dialogVisible"
      :title="editingId == null ? '新建字典项' : '编辑字典项'"
      width="480px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="88px">
        <el-form-item label="字典类型" prop="dict_type">
          <el-select
            v-model="form.dict_type"
            :disabled="editingId != null"
            placeholder="选择类型"
            style="width: 100%"
          >
            <el-option
              v-for="type in DICT_TYPE_OPTIONS"
              :key="type"
              :value="type"
              :label="DICT_TYPE_LABEL[type] ?? type"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" :disabled="editingId != null" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="dialogSaving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
