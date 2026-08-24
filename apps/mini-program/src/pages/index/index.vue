<template>
  <view class="content">
    <image class="logo" src="/static/logo.png" mode="aspectFit" />
    <view class="text-area">
      <text class="title">WMS 仓管作业</text>
      <text class="subtitle">uni-app · 微信小程序</text>
    </view>
  </view>
</template>

<script setup lang="ts">
</script>

<style>
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.logo {
  height: 200rpx;
  width: 200rpx;
  margin-top: 200rpx;
  margin-bottom: 50rpx;
}

.text-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
}

.title {
  font-size: 40rpx;
  font-weight: 600;
  color: #303133;
}

.subtitle {
  font-size: 28rpx;
  color: #909399;
}
</style>
