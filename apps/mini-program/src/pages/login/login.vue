<script setup lang="ts">
import { computed, ref } from 'vue'

import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'
import { errorMessage } from '@/utils/errorMessage'

const auth = useAuthStore()
const appStore = useAppStore()

const username = ref('')
const password = ref('')
const formError = ref('')

const showDenied = computed(() => auth.denied)

async function onLogin(): Promise<void> {
  formError.value = ''
  if (!username.value.trim() || !password.value) {
    formError.value = '请输入用户名和密码'
    return
  }
  try {
    await auth.login(username.value.trim(), password.value)
    if (auth.denied) {
      return
    }
    try {
      await appStore.ensureWarehouse()
    } catch {
      // 仓库拉取失败不阻断进入待办
    }
    uni.reLaunch({ url: '/pages/todo/index' })
  } catch (error) {
    formError.value = errorMessage(error, '登录失败')
  }
}

function onLogout(): void {
  auth.logout()
  appStore.clearWarehouse()
  formError.value = ''
  password.value = ''
}
</script>

<template>
  <view class="page login-page">
    <view v-if="showDenied" class="denied card">
      <view class="denied-title">无权使用作业端</view>
      <view class="muted denied-desc">
        请使用网页后台，或联系管理员分配仓管员账号。
      </view>
      <button class="btn-primary" @click="onLogout">退出登录</button>
    </view>

    <view v-else class="login-form">
      <image class="logo" src="/static/logo.png" mode="aspectFit" />
      <view class="brand">仓脉 WMS 作业</view>

      <view v-if="formError" class="error-banner">{{ formError }}</view>

      <text class="field-label">用户名</text>
      <input
        v-model="username"
        class="field-input"
        type="text"
        placeholder="请输入用户名"
        :disabled="auth.loading"
      />

      <text class="field-label" style="margin-top: 24rpx">密码</text>
      <input
        v-model="password"
        class="field-input"
        password
        placeholder="请输入密码"
        :disabled="auth.loading"
      />

      <button
        class="btn-primary login-btn"
        :loading="auth.loading"
        :disabled="auth.loading"
        @click="onLogin"
      >
        登录
      </button>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.login-page {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
}

.logo {
  width: 120rpx;
  height: 120rpx;
  margin: 0 auto 24rpx;
  display: block;
}

.brand {
  text-align: center;
  font-size: 40rpx;
  font-weight: 700;
  margin-bottom: 64rpx;
  color: $color-foreground;
}

.login-btn {
  margin-top: 48rpx;
}

.denied {
  text-align: center;
}

.denied-title {
  font-size: 36rpx;
  font-weight: 600;
  margin-bottom: 16rpx;
}

.denied-desc {
  margin-bottom: 48rpx;
  line-height: 1.5;
}
</style>
