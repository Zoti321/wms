<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { downloadDailyReportCsv, getDailyReport } from '@/api/reports'
import { useAppStore } from '@/stores/app'
import type { DailyReport } from '@/types/api'
import { saveBlobAsFile } from '@/utils/download'
import { errorMessage } from '@/utils/errorMessage'

const app = useAppStore()

const loading = ref(false)
const exporting = ref(false)
const report = ref<DailyReport | null>(null)

const filters = reactive({
  business_date: new Date().toISOString().slice(0, 10),
})

async function loadReport(): Promise<void> {
  if (app.warehouseId == null) {
    report.value = null
    return
  }

  loading.value = true
  try {
    report.value = await getDailyReport({
      warehouse_id: app.warehouseId,
      business_date: filters.business_date,
    })
  } catch (error) {
    report.value = null
    ElMessage.error(errorMessage(error, '加载日报失败'))
  } finally {
    loading.value = false
  }
}

function onSearch(): void {
  void loadReport()
}

async function onExportCsv(): Promise<void> {
  if (app.warehouseId == null) {
    ElMessage.warning('请先确认仓库上下文')
    return
  }

  exporting.value = true
  try {
    const blob = await downloadDailyReportCsv({
      warehouse_id: app.warehouseId,
      business_date: filters.business_date,
    })
    const filename = `daily-report-${filters.business_date}-wh${app.warehouseId}.csv`
    saveBlobAsFile(blob, filename)
    ElMessage.success('CSV 已开始下载')
  } catch (error) {
    ElMessage.error(errorMessage(error, '导出 CSV 失败'))
  } finally {
    exporting.value = false
  }
}

watch(
  () => app.warehouseId,
  () => {
    void loadReport()
  },
)

onMounted(() => {
  void loadReport()
})
</script>

<template>
  <div class="page-panel">
    <div class="page-toolbar">
      <span>日报</span>
      <el-button
        v-permission="'report:read'"
        type="primary"
        :loading="exporting"
        :disabled="app.warehouseId == null"
        @click="onExportCsv"
      >
        导出 CSV
      </el-button>
    </div>

    <el-form class="page-filters" :inline="true" @submit.prevent="onSearch">
      <el-form-item label="业务日">
        <el-date-picker
          v-model="filters.business_date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          style="width: 160px"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :disabled="app.warehouseId == null"
          @click="onSearch"
        >
          查询
        </el-button>
      </el-form-item>
    </el-form>

    <el-alert
      v-if="app.warehouseId == null"
      type="warning"
      :closable="false"
      show-icon
      title="尚未绑定仓库，无法查询日报。"
    />

    <el-table
      v-else
      v-loading="loading"
      :data="report ? [report] : []"
      size="small"
      empty-text="暂无数据，请选择业务日后查询"
    >
      <el-table-column prop="business_date" label="业务日" width="120">
        <template #default="{ row }">
          <span class="font-data">{{ row.business_date }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="inbound_order_count" label="入库单数" width="100" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.inbound_order_count }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="putaway_qty" label="上架量" min-width="100" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.putaway_qty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="outbound_order_count" label="出库单数" width="100" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.outbound_order_count }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="picked_qty" label="拣货量" min-width="100" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.picked_qty }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="sku_count" label="有货 SKU" width="100" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.sku_count }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="total_available" label="总可用量" min-width="110" align="right">
        <template #default="{ row }">
          <span class="qty-cell">{{ row.total_available }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="open_alert_count" label="有效预警" width="100" align="right">
        <template #default="{ row }">
          <span class="font-data">{{ row.open_alert_count }}</span>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>
