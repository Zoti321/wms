<script setup lang="ts">
import { computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { APP_VERSION } from '@/constants/app'
import { ROLE_CODE_LABEL } from '@/constants/labels'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { requireOperatorSession } from '@/utils/sessionGate'

const auth = useAuthStore()
const appStore = useAppStore()

const avatarLetter = computed(() => {
  const name = auth.user?.username?.trim()
  if (!name) {
    return '?'
  }
  return name.charAt(0).toUpperCase()
})

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
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号？',
    success: (res) => {
      if (!res.confirm) {
        return
      }
      auth.logout()
      appStore.clearWarehouse()
      uni.reLaunch({ url: '/pages/login/login' })
    },
  })
}
</script>

<template>
  <view class="page">
    <view class="card profile">
      <view class="avatar">{{ avatarLetter }}</view>
      <view class="profile-meta">
        <view class="value">{{ auth.user?.username ?? '—' }}</view>
        <view class="muted">
          {{ ROLE_CODE_LABEL[auth.user?.role_code ?? ''] ?? auth.user?.role_code ?? '—' }}
        </view>
      </view>
    </view>

    <view class="card">
      <view class="info-row">
        <text class="muted">当前仓库</text>
        <text class="value">{{ appStore.warehouseName ?? '—' }}</text>
      </view>
      <view class="info-row">
        <text class="muted">版本</text>
        <text class="value font-data">{{ APP_VERSION }}</text>
      </view>
    </view>

    <button class="btn-ghost" @click="onLogout">退出登录</button>
  </view>
</template>

<style lang="scss" scoped>
.profile {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: $color-primary;
  color: $color-on-primary;
  font-size: 40rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-meta .value {
  font-size: 32rpx;
  font-weight: 600;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 96rpx;
  border-bottom: 1rpx solid $color-border;

  &:last-child {
    border-bottom: none;
  }
}

.info-row .value {
  font-size: 28rpx;
  font-weight: 600;
}

.btn-ghost {
  margin-top: 48rpx;
  width: 100%;
}
</style>
