<script setup lang="ts">
import { computed, ref } from 'vue'
import { onPullDownRefresh, onShow } from '@dcloudio/uni-app'

import { listInboundOrders } from '@/api/inboundOrders'
import { listOutboundOrders } from '@/api/outboundOrders'
import { orderTypeLabel, statusLabel, statusTagClass } from '@/constants/labels'
import { formatDateTime } from '@/utils/formatDateTime'
import {
  filterTodoTasks,
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

const visibleTasks = computed(() => filterTodoTasks(tasks.value, filter.value))

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
    const cards = [
      ...inApproved.items.map((item) => toTaskCard('inbound', item)),
      ...inPutaway.items.map((item) => toTaskCard('inbound', item)),
      ...outApproved.items.map((item) => toTaskCard('outbound', item)),
      ...outPicking.items.map((item) => toTaskCard('outbound', item)),
    ]
    tasks.value = mergeTodoTasks(cards)
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

    <view v-if="loading && !tasks.length" class="muted">加载中…</view>

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
</style>
