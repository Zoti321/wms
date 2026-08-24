<script setup lang="ts">
import { onShow } from '@dcloudio/uni-app'

import { ROLE_CODE_LABEL } from '@/constants/labels'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { requireOperatorSession } from '@/utils/sessionGate'

const auth = useAuthStore()
const appStore = useAppStore()

onShow(async () => {
  const ok = await requireOperatorSession()
  if (!ok) {
    return
  }
  if (!appStore.warehouseName) {
    try {
      await appStore.ensureWarehouse()
    } catch {
      // ignore
    }
  }
})

function onLogout(): void {
  auth.logout()
  appStore.clearWarehouse()
  uni.reLaunch({ url: '/pages/login/login' })
}
</script>

<template>
  <view class="page">
    <view class="card">
      <view class="label muted">用户名</view>
      <view class="value">{{ auth.user?.username ?? '—' }}</view>
      <view class="label muted">角色</view>
      <view class="value">
        {{ ROLE_CODE_LABEL[auth.user?.role_code ?? ''] ?? auth.user?.role_code ?? '—' }}
      </view>
      <view class="label muted">当前仓库</view>
      <view class="value">{{ appStore.warehouseName ?? '—' }}</view>
    </view>

    <button class="btn-ghost" @click="onLogout">退出登录</button>
  </view>
</template>

<style lang="scss" scoped>
.label {
  margin-top: 20rpx;
}

.label:first-child {
  margin-top: 0;
}

.value {
  margin-top: 8rpx;
  font-size: 32rpx;
  font-weight: 600;
}

.btn-ghost {
  margin-top: 48rpx;
  width: 100%;
}
</style>
