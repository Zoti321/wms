<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import { listSkus } from '@/api/catalog'
import { getInboundOrder } from '@/api/inboundOrders'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { INBOUND_ORDER_TYPE_LABEL, INBOUND_STATUS_LABEL } from '@/constants/labels'
import type { InboundOrder, InboundOrderLine } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'
import { formatDateTime } from '@/utils/formatDateTime'
import { remainQty } from '@/utils/qty'
import { requireOperatorSession } from '@/utils/sessionGate'

const orderId = ref(0)
const order = ref<InboundOrder | null>(null)
const loading = ref(false)
const skuLabelById = ref<Record<number, string>>({})

const pendingLines = computed(() => {
  const lines = order.value?.lines ?? []
  return lines.filter((line) => Number(remainQty(line.planned_qty, line.putaway_qty)) > 0)
})

async function loadSkuLabels(): Promise<void> {
  try {
    const page = await listSkus({
      status: 1,
      selectable: true,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    const map: Record<number, string> = {}
    for (const sku of page.items) {
      map[sku.id] = `${sku.sku_code} · ${sku.name}`
    }
    skuLabelById.value = map
  } catch {
    skuLabelById.value = {}
  }
}

async function loadOrder(): Promise<void> {
  if (!orderId.value) {
    return
  }
  loading.value = true
  try {
    order.value = await getInboundOrder(orderId.value)
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '加载失败'), icon: 'none' })
  } finally {
    loading.value = false
  }
}

function skuLabel(line: InboundOrderLine): string {
  return skuLabelById.value[line.sku_id] ?? `SKU #${line.sku_id}`
}

function onPutaway(line: InboundOrderLine): void {
  uni.navigateTo({
    url: `/pages/inbound/putaway?orderId=${orderId.value}&lineId=${line.id}`,
  })
}

function backTodo(): void {
  uni.switchTab({ url: '/pages/todo/index' })
}

onLoad((query) => {
  orderId.value = Number(query?.id ?? 0)
})

onShow(async () => {
  const ok = await requireOperatorSession()
  if (!ok) {
    return
  }
  await Promise.all([loadSkuLabels(), loadOrder()])
})
</script>

<template>
  <view class="page">
    <view v-if="loading && !order" class="muted">加载中…</view>
    <template v-else-if="order">
      <view class="card">
        <view class="font-data title">{{ order.order_no }}</view>
        <view class="muted">
          {{ INBOUND_ORDER_TYPE_LABEL[order.order_type] ?? order.order_type }}
          ·
          {{ INBOUND_STATUS_LABEL[order.status] ?? order.status }}
        </view>
        <view v-if="order.remark" class="muted" style="margin-top: 12rpx">
          备注：{{ order.remark }}
        </view>
        <view class="muted" style="margin-top: 12rpx">
          创建于 {{ formatDateTime(order.created_at) }}
        </view>
      </view>

      <view v-if="!pendingLines.length" class="empty">
        <view>本单已处理完成</view>
        <button class="btn-ghost" style="margin-top: 32rpx" @click="backTodo">返回待办</button>
      </view>

      <view v-for="line in pendingLines" :key="line.id" class="card line-card">
        <view class="font-data">{{ skuLabel(line) }}</view>
        <view class="muted qty-row">
          计划 {{ line.planned_qty }} · 已上架 {{ line.putaway_qty }} · 剩余
          {{ remainQty(line.planned_qty, line.putaway_qty) }}
        </view>
        <button class="btn-primary line-btn" @click="onPutaway(line)">上架</button>
      </view>
    </template>
  </view>
</template>

<style lang="scss" scoped>
.title {
  font-size: 34rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.qty-row {
  margin: 16rpx 0 24rpx;
}

.line-btn {
  height: 88rpx;
  line-height: 88rpx;
}
</style>
