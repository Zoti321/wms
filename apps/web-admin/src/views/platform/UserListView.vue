<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  assignUserRole,
  createUser,
  deactivateUser,
  listUsers,
  resetUserPassword,
} from '@/api/users'
import { ACTIVE_STATUS_LABEL, ROLE_CODE_LABEL } from '@/constants/labels'
import type { CreateUserRequest, PlatformUser } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'

const ROLE_OPTIONS = ['admin', 'supervisor', 'operator', 'viewer'] as const

const loading = ref(false)
const items = ref<PlatformUser[]>([])
const total = ref(0)

const filters = reactive({
  page: 1,
  page_size: 20,
})

const createVisible = ref(false)
const createSaving = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({
  username: '',
  password: '',
  role_code: '',
})

const createRules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 8, message: '密码至少 8 位', trigger: 'blur' },
  ],
  role_code: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const roleDialogVisible = ref(false)
const roleSaving = ref(false)
const roleTarget = ref<PlatformUser | null>(null)
const roleCode = ref('')

async function loadList(): Promise<void> {
  loading.value = true
  try {
    const page = await listUsers({
      page: filters.page,
      page_size: filters.page_size,
    })
    items.value = page.items
    total.value = page.total
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载用户列表失败'))
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  createForm.username = ''
  createForm.password = ''
  createForm.role_code = ''
  createFormRef.value?.clearValidate()
  createVisible.value = true
}

async function onCreate(): Promise<void> {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) {
    return
  }

  createSaving.value = true
  try {
    const payload: CreateUserRequest = {
      username: createForm.username.trim(),
      password: createForm.password,
      role_code: createForm.role_code,
    }
    await createUser(payload)
    ElMessage.success('用户创建成功')
    createVisible.value = false
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '创建用户失败'))
  } finally {
    createSaving.value = false
  }
}

async function onDeactivate(row: PlatformUser): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认停用用户「${row.username}」？`, '停用确认', {
      type: 'warning',
      confirmButtonText: '停用',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await deactivateUser(row.id)
    ElMessage.success('已停用')
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '停用失败'))
  }
}

async function onResetPassword(row: PlatformUser): Promise<void> {
  let password = ''
  try {
    const { value } = await ElMessageBox.prompt('请输入新密码（至少 8 位）', '重置密码', {
      confirmButtonText: '确认重置',
      cancelButtonText: '取消',
      inputType: 'password',
      inputValidator: (val) => {
        if (!val || val.length < 8) {
          return '密码至少 8 位'
        }
        return true
      },
    })
    password = value
  } catch {
    return
  }

  try {
    await ElMessageBox.confirm(`确认重置用户「${row.username}」的密码？`, '二次确认', {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }

  try {
    await resetUserPassword(row.id, { password })
    ElMessage.success('密码已重置')
  } catch (error) {
    ElMessage.error(errorMessage(error, '重置密码失败'))
  }
}

function openRoleDialog(row: PlatformUser): void {
  roleTarget.value = row
  roleCode.value = row.role_code
  roleDialogVisible.value = true
}

async function onAssignRole(): Promise<void> {
  if (!roleTarget.value || !roleCode.value) {
    return
  }

  roleSaving.value = true
  try {
    await assignUserRole(roleTarget.value.id, { role_code: roleCode.value })
    ElMessage.success('角色已更新')
    roleDialogVisible.value = false
    await loadList()
  } catch (error) {
    ElMessage.error(errorMessage(error, '变更角色失败'))
  } finally {
    roleSaving.value = false
  }
}

onMounted(() => {
  void loadList()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>用户管理</span>
      <el-button v-permission="'user:write'" type="primary" @click="openCreate">
        新建用户
      </el-button>
    </div>

    <el-table v-loading="loading" :data="items" size="small" empty-text="暂无用户">
      <el-table-column prop="id" label="ID" width="80">
        <template #default="{ row }">
          <span class="font-data">{{ row.id }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="username" label="用户名" min-width="140">
        <template #default="{ row }">
          <span class="font-data">{{ row.username }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="role_code" label="角色" width="120">
        <template #default="{ row }">
          {{ ROLE_CODE_LABEL[row.role_code] ?? row.role_code }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ ACTIVE_STATUS_LABEL[row.status] ?? row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button
            v-permission="'user:write'"
            link
            type="primary"
            @click="openRoleDialog(row)"
          >
            改角色
          </el-button>
          <el-button
            v-permission="'user:write'"
            link
            type="primary"
            @click="onResetPassword(row)"
          >
            重置密码
          </el-button>
          <el-button
            v-if="row.status === 1"
            v-permission="'user:write'"
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

    <el-dialog v-model="createVisible" title="新建用户" width="480px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="88px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input v-model="createForm.password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="角色" prop="role_code">
          <el-select v-model="createForm.role_code" placeholder="选择角色" style="width: 100%">
            <el-option
              v-for="code in ROLE_OPTIONS"
              :key="code"
              :value="code"
              :label="ROLE_CODE_LABEL[code] ?? code"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSaving" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="roleDialogVisible" title="变更角色" width="400px" destroy-on-close>
      <el-form label-width="72px">
        <el-form-item label="用户">
          <span>{{ roleTarget?.username }}</span>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="roleCode" placeholder="选择角色" style="width: 100%">
            <el-option
              v-for="code in ROLE_OPTIONS"
              :key="code"
              :value="code"
              :label="ROLE_CODE_LABEL[code] ?? code"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="roleDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="roleSaving" @click="onAssignRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
