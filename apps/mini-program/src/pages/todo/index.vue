<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { getInboundOrder, listInboundOrders } from '@/api/inboundOrders'
import { getOutboundOrder, listOutboundOrders } from '@/api/outboundOrders'
import { orderTypeLabel, statusLabel, statusTagClass } from '@/constants/labels'
import { formatDateTime } from '@/utils/formatDateTime'
import {
  enrichPendingLineCounts,
  filterTodoTasks,
  mergePendingLineCount,
  mergeTodoTasks,
  toTaskCard,
  type TaskCard,
  type TaskFilter,
} from '@/utils/todoTasks'
import { errorMessage } from '@/utils/errorMessage'
import { requireOperatorSession } from '@/utils/sessionGate'

const loading = ref(false)
const error = ref('')
const filter = ref<TaskFilter>('all')
const tasks = ref<TaskCard[]>([])

let enrichGeneration = 0

const visibleTasks = computed(() => filterTodoTasks(tasks.value, filter.value))
const showSkeleton = computed(() => loading.value && tasks.value.length === 0)

async function enrichCounts(cards: TaskCard[]): Promise<void> {
  const generation = ++enrichGeneration
  const enriched = await enrichPendingLineCounts(cards, {
    fetchInbound: getInboundOrder,
    fetchOutbound: getOutboundOrder,
    concurrency: 5,
  })
  if (generation !== enrichGeneration) {
    return
  }
  // 仅在仍是同一批列表时合并行数（避免覆盖更新的列表）
  const byKey = new Map(enriched.map((c) => [`${c.kind}-${c.orderId}`, c.pendingLineCount]))
  tasks.value = tasks.value.map((card) => {
    const key = `${card.kind}-${card.orderId}`
    if (!byKey.has(key)) {
      return card
    }
    return mergePendingLineCount(card, byKey.get(key))
  })
}

async function loadTasks(silent = false): Promise<void> {
  if (!silent) {
    loading.value = true
  }
  error.value = ''
  try {
    const queryBase = { page: 1, page_size: 50 }
    const [inApproved, inPutaway, outApproved, outPicking] = await Promise.all([
      listInboundOrders({ ...queryBase, status: 'approved' }),
      listInboundOrders({ ...queryBase, status: 'putaway' }),
      listOutboundOrders({ ...queryBase, status: 'approved' }),
      listOutboundOrders({ ...queryBase, status: 'picking' }),
    ])
    const cards = mergeTodoTasks([
      ...inApproved.items.map((item) => toTaskCard('inbound', item)),
      ...inPutaway.items.map((item) => toTaskCard('inbound', item)),
      ...outApproved.items.map((item) => toTaskCard('outbound', item)),
      ...outPicking.items.map((item) => toTaskCard('outbound', item)),
    ])
    tasks.value = cards
    void enrichCounts(cards)
  } catch (e) {
    error.value = errorMessage(e, '加载待办失败')
    if (!silent) {
      uni.showToast({ title: error.value, icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

function onOpen(card: TaskCard): void {
  if (card.kind === 'inbound') {
    uni.navigateTo({ url: `/pages/inbound/detail?id=${card.orderId}` })
  } else {
    uni.navigateTo({ url: `/pages/outbound/detail?id=${card.orderId}` })
  }
}

onShow(async () => {
  const ok = await requireOperatorSession()
  if (!ok) {
    return
  }
  await loadTasks(tasks.value.length > 0)
})

onPullDownRefresh(async () => {
  await loadTasks(true)
  uni.stopPullDownRefresh()
})
</script>

<template>
  <view class="page todo-page">
    <view class="segments">
      <view
        v-for="item in [
          { key: 'all', label: '全部' },
          { key: 'inbound', label: '入库' },
          { key: 'outbound', label: '出库' },
        ]"
        :key="item.key"
        class="segment"
        :class="{ active: filter === item.key }"
        @click="filter = item.key as TaskFilter"
      >
        {{ item.label }}
      </view>
    </view>

    <view v-if="error && !tasks.length" class="error-banner">{{ error }}</view>

    <template v-if="showSkeleton">
      <view v-for="n in 3" :key="n" class="card skeleton-card">
        <view class="sk-line sk-wide" />
        <view class="sk-line sk-mid" />
        <view class="sk-line sk-narrow" />
      </view>
    </template>

    <view v-else-if="!visibleTasks.length" class="empty">
      <view>暂无待办任务</view>
      <view class="muted" style="margin-top: 12rpx">已完成任务请先在网页后台审核</view>
    </view>

    <view
      v-for="card in visibleTasks"
      :key="`${card.kind}-${card.orderId}`"
      class="card task-card"
      @click="onOpen(card)"
    >
      <view class="row">
        <text class="kind">{{ card.kind === 'inbound' ? '入库' : '出库' }}</text>
        <text class="font-data order-no">{{ card.orderNo }}</text>
      </view>
      <view class="row meta">
        <text class="muted">{{ orderTypeLabel(card.kind, card.orderType) }}</text>
        <text class="status-tag" :class="statusTagClass(card.kind, card.status)">
          {{ statusLabel(card.kind, card.status) }}
        </text>
      </view>
      <view v-if="card.pendingLineCount != null" class="muted pending-lines">
        待处理 {{ card.pendingLineCount }} 行
      </view>
      <view class="muted">创建于 {{ formatDateTime(card.updatedAt) }}</view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.todo-page {
  padding-bottom: 120rpx;
}

.segments {
  display: flex;
  gap: 16rpx;
  margin-bottom: $space-lg;
}

.segment {
  flex: 1;
  height: 64rpx;
  line-height: 64rpx;
  text-align: center;
  border-radius: 12rpx;
  background: $color-card;
  border: 1rpx solid $color-border;
  color: $color-muted;
  font-size: 26rpx;

  &.active {
    background: $color-primary;
    border-color: $color-primary;
    color: $color-on-primary;
    font-weight: 600;
  }
}

.task-card {
  min-height: 88rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 12rpx;
}

.kind {
  font-size: 24rpx;
  color: $color-muted;
}

.order-no {
  font-size: 32rpx;
  font-weight: 600;
}

.meta {
  margin-bottom: 8rpx;
}

.pending-lines {
  margin-bottom: 8rpx;
}

.skeleton-card {
  min-height: 140rpx;
}

.sk-line {
  height: 24rpx;
  border-radius: 8rpx;
  background: $color-border;
  margin-bottom: 16rpx;
  opacity: 0.55;

  &:last-child {
    margin-bottom: 0;
  }
}

.sk-wide {
  width: 70%;
}

.sk-mid {
  width: 50%;
}

.sk-narrow {
  width: 40%;
}
</style>
