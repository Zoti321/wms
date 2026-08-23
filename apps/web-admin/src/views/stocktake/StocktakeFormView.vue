<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { listLocations } from '@/api/locations'
import { createStocktake } from '@/api/stocktakes'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { ROUTE_NAMES } from '@/router/routes'
import { useAppStore } from '@/stores/app'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()
const router = useRouter()

const saving = ref(false)
const zoneOptions = ref<string[]>([])

const form = reactive({
  zone: undefined as string | undefined,
  remark: '',
})

const zoneLabel = computed(() => {
  if (form.zone == null || form.zone === '') {
    return '全仓'
  }
  return form.zone
})

async function loadZoneOptions(): Promise<void> {
  if (app.warehouseId == null) {
    zoneOptions.value = []
    return
  }

  try {
    const page = await listLocations({
      warehouse_id: app.warehouseId,
      selectable: true,
      status: 1,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    const zones = new Set<string>()
    for (const loc of page.items) {
      if (loc.zone) {
        zones.add(loc.zone)
      }
    }
    zoneOptions.value = [...zones].sort()
  } catch (error) {
    ElMessage.error(errorMessage(error, '加载库区选项失败'))
  }
}

async function onSubmit(): Promise<void> {
  if (app.warehouseId == null) {
    ElMessage.warning('请先绑定仓库')
    return
  }

  saving.value = true
  try {
    const result = await createStocktake({
      warehouse_id: app.warehouseId,
      zone: form.zone ?? null,
      remark: form.remark.trim() || null,
    })
    ElMessage.success(result.replayed ? '盘点单已幂等重放' : '盘点已发起，相关库位已加盘点锁')
    await router.replace({
      name: ROUTE_NAMES.stocktakeDetail,
      params: { id: result.order.id },
    })
  } catch (error) {
    ElMessage.error(errorMessage(error, '发起盘点失败'))
  } finally {
    saving.value = false
  }
}

function goBack(): void {
  void router.push({ name: ROUTE_NAMES.stocktakeList })
}

onMounted(() => {
  void loadZoneOptions()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>发起盘点</span>
      <el-button @click="goBack">返回列表</el-button>
    </div>

    <el-alert
      v-if="app.warehouseReady && app.warehouseId == null"
      type="warning"
      :closable="false"
      show-icon
      title="未绑定仓库，无法发起盘点。"
      style="margin-bottom: 12px"
    />

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="发起盘点后将立即对覆盖库位施加盘点锁，禁止上架与拣货，直至审核完成或取消。"
      style="margin-bottom: 12px"
    />

    <el-form :model="form" label-width="96px" style="max-width: 560px">
      <el-form-item label="盘点范围">
        <el-select
          v-model="form.zone"
          clearable
          filterable
          placeholder="全仓（留空）"
          style="width: 240px"
        >
          <el-option
            v-for="zone in zoneOptions"
            :key="zone"
            :value="zone"
            :label="zone"
          />
        </el-select>
        <span class="hint">当前选择：{{ zoneLabel }}</span>
      </el-form-item>
      <el-form-item label="备注">
        <el-input v-model="form.remark" type="textarea" :rows="2" />
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          :loading="saving"
          :disabled="app.warehouseId == null"
          @click="onSubmit"
        >
          发起盘点
        </el-button>
        <el-button @click="goBack">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--color-muted-foreground);
}
</style>
