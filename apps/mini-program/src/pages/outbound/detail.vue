<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import { listSkus } from '@/api/catalog'
import { getLocation } from '@/api/locations'
import { getOutboundOrder } from '@/api/outboundOrders'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import { OUTBOUND_ORDER_TYPE_LABEL, OUTBOUND_STATUS_LABEL } from '@/constants/labels'
import type { OutboundOrder, OutboundOrderLine } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'
import { formatDateTime } from '@/utils/formatDateTime'
import { remainQty } from '@/utils/qty'
import { requireOperatorSession } from '@/utils/sessionGate'

const orderId = ref(0)
const order = ref<OutboundOrder | null>(null)
const loading = ref(false)
const skuLabelById = ref<Record<number, string>>({})
const locationCodeById = ref<Record<number, string>>({})

const pendingLines = computed(() => {
  const lines = order.value?.lines ?? []
  return lines.filter((line) => Number(remainQty(line.allocated_qty, line.picked_qty)) > 0)
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

async function resolveLocations(lines: OutboundOrderLine[]): Promise<void> {
  const ids = [
    ...new Set(
      lines
        .map((line) => line.location_id)
        .filter((id): id is number => typeof id === 'number'),
    ),
  ]
  const map: Record<number, string> = { ...locationCodeById.value }
  await Promise.all(
    ids.map(async (id) => {
      if (map[id]) {
        return
      }
      try {
        const loc = await getLocation(id)
        map[id] = loc.location_code
      } catch {
        map[id] = `#${id}`
      }
    }),
  )
  locationCodeById.value = map
}

async function loadOrder(): Promise<void> {
  if (!orderId.value) {
    return
  }
  loading.value = true
  try {
    order.value = await getOutboundOrder(orderId.value)
    await resolveLocations(order.value.lines)
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '加载失败'), icon: 'none' })
  } finally {
    loading.value = false
  }
}

function skuLabel(line: OutboundOrderLine): string {
  return skuLabelById.value[line.sku_id] ?? `SKU #${line.sku_id}`
}

function locationLabel(line: OutboundOrderLine): string {
  if (line.location_id == null) {
    return '未分配'
  }
  return locationCodeById.value[line.location_id] ?? `#${line.location_id}`
}

function onPick(line: OutboundOrderLine): void {
  uni.navigateTo({
    url: `/pages/outbound/pick?orderId=${orderId.value}&lineId=${line.id}`,
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
          {{ OUTBOUND_ORDER_TYPE_LABEL[order.order_type] ?? order.order_type }}
          ·
          {{ OUTBOUND_STATUS_LABEL[order.status] ?? order.status }}
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

      <view v-for="line in pendingLines" :key="line.id" class="card">
        <view class="font-data">{{ skuLabel(line) }}</view>
        <view class="muted qty-row">
          已分配 {{ line.allocated_qty }} · 已拣 {{ line.picked_qty }} · 剩余
          {{ remainQty(line.allocated_qty, line.picked_qty) }}
        </view>
        <view class="muted" style="margin-bottom: 24rpx">
          分配库位：<text class="font-data">{{ locationLabel(line) }}</text>
        </view>
        <button class="btn-primary line-btn" @click="onPick(line)">拣货</button>
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
  margin: 16rpx 0 8rpx;
}

.line-btn {
  height: 88rpx;
  line-height: 88rpx;
}
</style>
