<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

import { listSkus } from '@/api/catalog'
import { getLocation } from '@/api/locations'
import { getOutboundOrder, pickOutboundOrder } from '@/api/outboundOrders'
import { MAX_LIST_PAGE_SIZE } from '@/constants/api'
import type { OutboundOrder, OutboundOrderLine } from '@/types/api'
import { errorMessage } from '@/utils/errorMessage'
import { nextIdempotencyKey } from '@/utils/idempotency'
import { isPositiveQty, remainQty } from '@/utils/qty'
import { reportJobConflict } from '@/utils/reportJobConflict'
import { requireOperatorSession } from '@/utils/sessionGate'

const orderId = ref(0)
const lineId = ref(0)
const order = ref<OutboundOrder | null>(null)
const line = ref<OutboundOrderLine | null>(null)
const skuLabel = ref('')
const locationCode = ref('')
const qty = ref('0.000')
const submitting = ref(false)
const formError = ref('')

let idemKey: string | null = null
let idemFingerprint: string | null = null

const remain = computed(() =>
  line.value ? remainQty(line.value.allocated_qty, line.value.picked_qty) : '0.000',
)

const allocatedLocationId = computed(() => line.value?.location_id ?? null)

const fingerprint = computed(
  () => `line=${lineId.value}|loc=${allocatedLocationId.value ?? ''}|qty=${qty.value}`,
)

watch(fingerprint, () => {
  if (idemFingerprint != null && idemFingerprint !== fingerprint.value) {
    idemKey = null
  }
})

async function load(): Promise<void> {
  order.value = await getOutboundOrder(orderId.value)
  line.value = order.value.lines.find((item) => item.id === lineId.value) ?? null
  if (!line.value) {
    formError.value = '出库单行不存在'
    return
  }
  if (line.value.location_id == null) {
    formError.value = '该行尚未分配库位，请先在网页后台审核分配'
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
  try {
    const loc = await getLocation(line.value.location_id)
    locationCode.value = loc.location_code
  } catch {
    locationCode.value = `#${line.value.location_id}`
  }
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
  if (allocatedLocationId.value == null) {
    formError.value = '该行尚未分配库位'
    return
  }
  if (!isPositiveQty(qty.value)) {
    formError.value = '数量必须大于 0'
    return
  }
  if (Number(qty.value) > Number(remain.value)) {
    formError.value = '数量超过剩余可拣'
    return
  }
  const rotated = nextIdempotencyKey(idemKey, fingerprint.value, idemFingerprint)
  idemKey = rotated.key
  idemFingerprint = rotated.fingerprint

  submitting.value = true
  try {
    const result = await pickOutboundOrder(
      orderId.value,
      {
        line_id: lineId.value,
        location_id: allocatedLocationId.value,
        qty: qty.value,
      },
      idemKey,
    )
    uni.showToast({
      title: result.replayed ? '拣货已幂等重放' : '拣货成功',
      icon: 'success',
    })
    setTimeout(() => {
      uni.navigateBack()
    }, 400)
  } catch (error) {
    const report = reportJobConflict(error, '拣货失败')
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
        已分配 {{ line?.allocated_qty ?? '—' }} · 已拣 {{ line?.picked_qty ?? '—' }} · 剩余
        {{ remain }}
      </view>
    </view>

    <view class="card">
      <text class="field-label">实拣库位（审核分配，只读）</text>
      <view class="readonly font-data">{{ locationCode || '—' }}</view>
    </view>

    <view class="card">
      <text class="field-label">本次拣货数量</text>
      <view class="stepper">
        <button class="step-btn" @click="bumpQty(-1)">−</button>
        <input v-model="qty" class="field-input qty-input font-data" type="digit" />
        <button class="step-btn" @click="bumpQty(1)">+</button>
      </view>
    </view>

    <view class="cta-bar">
      <button class="btn-primary" :loading="submitting" :disabled="submitting" @click="onSubmit">
        确认拣货
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.readonly {
  min-height: 88rpx;
  line-height: 88rpx;
  padding: 0 24rpx;
  background: $color-background;
  border-radius: 12rpx;
  border: 1rpx solid $color-border;
  font-size: 28rpx;
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
