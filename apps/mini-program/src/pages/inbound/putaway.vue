<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { listSkus } from '@/api/catalog'
import { getInboundOrder, putawayInboundOrder } from '@/api/inboundOrders'
import { listLocations } from '@/api/locations'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import type { InboundOrder, InboundOrderLine, Location } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'
import { nextIdempotencyKey } from '@/utils/idempotency'
import { isLocationSelectable, spaceStatusLabel } from '@/utils/locationSpace'
import { isPositiveQty, remainQty } from '@/utils/qty'
import { reportJobConflict } from '@/utils/reportJobConflict'
import { requireOperatorSession } from '@/utils/sessionGate'

const orderId = ref(0)
const lineId = ref(0)
const order = ref<InboundOrder | null>(null)
const line = ref<InboundOrderLine | null>(null)
const skuLabel = ref('')
const locationKeyword = ref('')
const locations = ref<Location[]>([])
const selectedLocation = ref<Location | null>(null)
const qty = ref('0.000')
const submitting = ref(false)
const searching = ref(false)
const formError = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null
let idemKey: string | null = null
let idemFingerprint: string | null = null

const remain = computed(() =>
  line.value ? remainQty(line.value.planned_qty, line.value.putaway_qty) : '0.000',
)

const fingerprint = computed(() => {
  const locId = selectedLocation.value?.id ?? ''
  return `line=${lineId.value}|loc=${locId}|qty=${qty.value}`
})

watch(fingerprint, () => {
  // 字段变更时下次提交换新 key
  if (idemFingerprint != null && idemFingerprint !== fingerprint.value) {
    idemKey = null
  }
})

async function load(): Promise<void> {
  order.value = await getInboundOrder(orderId.value)
  line.value = order.value.lines.find((item) => item.id === lineId.value) ?? null
  if (!line.value) {
    formError.value = '入库单行不存在'
    return
  }
  qty.value = remain.value
  try {
    const page = await listSkus({
      status: 1,
      selectable: true,
      page: 1,
      page_size: MAX_LIST_PAGE_SIZE,
    })
    const sku = page.items.find((item) => item.id === line.value!.sku_id)
    skuLabel.value = sku ? `${sku.sku_code} · ${sku.name}` : `SKU #${line.value.sku_id}`
  } catch {
    skuLabel.value = `SKU #${line.value.sku_id}`
  }
}

function onKeywordInput(event: { detail: { value: string } }): void {
  locationKeyword.value = event.detail.value
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    void searchLocations()
  }, 300)
}

async function searchLocations(): Promise<void> {
  if (!order.value || !locationKeyword.value.trim()) {
    locations.value = []
    return
  }
  searching.value = true
  try {
    const page = await listLocations({
      warehouse_id: order.value.warehouse_id,
      code: locationKeyword.value.trim(),
      status: 1,
      selectable: true,
      page: 1,
      page_size: 20,
    })
    locations.value = page.items
  } catch (error) {
    uni.showToast({ title: errorMessage(error, '库位搜索失败'), icon: 'none' })
  } finally {
    searching.value = false
  }
}

function selectLocation(loc: Location): void {
  if (!isLocationSelectable(loc.space_status)) {
    uni.showToast({ title: '该库位已冻结，不可上架', icon: 'none' })
    return
  }
  selectedLocation.value = loc
  locationKeyword.value = loc.location_code
  locations.value = []
}

function bumpQty(delta: number): void {
  const current = Number(qty.value)
  const max = Number(remain.value)
  if (!Number.isFinite(current) || !Number.isFinite(max)) {
    return
  }
  const next = Math.min(max, Math.max(0.001, Number((current + delta).toFixed(3))))
  qty.value = next.toFixed(3)
}

async function onSubmit(): Promise<void> {
  formError.value = ''
  if (!selectedLocation.value) {
    formError.value = '请选择库位'
    return
  }
  if (!isPositiveQty(qty.value)) {
    formError.value = '数量必须大于 0'
    return
  }
  if (Number(qty.value) > Number(remain.value)) {
    formError.value = '数量超过剩余可上'
    return
  }
  const rotated = nextIdempotencyKey(idemKey, fingerprint.value, idemFingerprint)
  idemKey = rotated.key
  idemFingerprint = rotated.fingerprint

  submitting.value = true
  try {
    const result = await putawayInboundOrder(
      orderId.value,
      {
        line_id: lineId.value,
        location_id: selectedLocation.value.id,
        qty: qty.value,
      },
      idemKey,
    )
    uni.showToast({
      title: result.replayed ? '上架已幂等重放' : '上架成功',
      icon: 'success',
    })
    setTimeout(() => {
      uni.navigateBack()
    }, 400)
  } catch (error) {
    const report = reportJobConflict(error, '上架失败')
    if (!report.usedStocktakeLockModal) {
      formError.value = report.message
    }
  } finally {
    submitting.value = false
  }
}

onLoad(async (query) => {
  const ok = await requireOperatorSession()
  if (!ok) {
    return
  }
  orderId.value = Number(query?.orderId ?? 0)
  lineId.value = Number(query?.lineId ?? 0)
  try {
    await load()
  } catch (error) {
    formError.value = errorMessage(error, '加载失败')
  }
})
</script>

<template>
  <view class="page page-with-cta">
    <view v-if="formError" class="error-banner">{{ formError }}</view>

    <view class="card">
      <view class="font-data">{{ skuLabel || '—' }}</view>
      <view class="muted" style="margin-top: 12rpx">
        计划 {{ line?.planned_qty ?? '—' }} · 已上架 {{ line?.putaway_qty ?? '—' }} · 剩余
        {{ remain }}
      </view>
    </view>

    <view class="card">
      <text class="field-label">库位</text>
      <input
        class="field-input"
        :value="locationKeyword"
        placeholder="输入库位编码搜索"
        @input="onKeywordInput"
      />
      <view v-if="selectedLocation" class="muted" style="margin-top: 12rpx">
        已选：{{ selectedLocation.location_code }}
      </view>
      <view v-if="searching" class="muted" style="margin-top: 12rpx">搜索中…</view>
      <view
        v-else-if="locationKeyword && !locations.length && !selectedLocation"
        class="muted"
        style="margin-top: 12rpx"
      >
        未找到库位，请检查编码
      </view>
      <view
        v-for="loc in locations"
        :key="loc.id"
        class="loc-item"
        :class="{ disabled: !isLocationSelectable(loc.space_status) }"
        @click="selectLocation(loc)"
      >
        <text class="font-data">{{ loc.location_code }}</text>
        <text class="muted loc-status">{{ spaceStatusLabel(loc.space_status) }}</text>
      </view>
    </view>

    <view class="card">
      <text class="field-label">本次上架数量</text>
      <view class="stepper">
        <button class="step-btn" @click="bumpQty(-1)">−</button>
        <input v-model="qty" class="field-input qty-input font-data" type="digit" />
        <button class="step-btn" @click="bumpQty(1)">+</button>
      </view>
    </view>

    <view class="cta-bar">
      <button class="btn-primary" :loading="submitting" :disabled="submitting" @click="onSubmit">
        确认上架
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.loc-item {
  margin-top: 16rpx;
  padding: 20rpx;
  border-radius: 12rpx;
  background: $color-background;
  min-height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;

  &.disabled {
    opacity: 0.45;
  }
}

.loc-status {
  font-size: 24rpx;
  flex-shrink: 0;
}

.stepper {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.step-btn {
  width: 88rpx;
  height: 88rpx;
  line-height: 88rpx;
  padding: 0;
  background: $color-background;
  border: 1rpx solid $color-border;
  border-radius: 12rpx;
  font-size: 40rpx;
}

.qty-input {
  flex: 1;
  text-align: center;
}
</style>
