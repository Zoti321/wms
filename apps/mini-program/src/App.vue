<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
</script>

<style lang="scss">
page {
  background-color: $color-background;
  color: $color-foreground;
  font-size: 28rpx;
  box-sizing: border-box;
}

.font-data {
  font-variant-numeric: tabular-nums;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

.page {
  min-height: 100vh;
  padding: $space-lg;
  box-sizing: border-box;
}

.card {
  background: $color-card;
  border-radius: 16rpx;
  padding: $space-lg;
  margin-bottom: $space-md;
  border: 1rpx solid $color-border;
}

.muted {
  color: $color-muted;
  font-size: 24rpx;
}

.btn-primary {
  height: 96rpx;
  line-height: 96rpx;
  background: $color-primary;
  color: $color-on-primary;
  border-radius: 12rpx;
  font-size: 32rpx;
  font-weight: 600;
  text-align: center;
  border: none;

  &[disabled] {
    opacity: 0.55;
  }
}

.btn-ghost {
  height: 88rpx;
  line-height: 88rpx;
  background: transparent;
  color: $color-primary;
  border: 2rpx solid $color-primary;
  border-radius: 12rpx;
  font-size: 28rpx;
  text-align: center;
}

.field-label {
  display: block;
  margin-bottom: 12rpx;
  color: $color-muted;
  font-size: 24rpx;
}

.field-input {
  height: 88rpx;
  padding: 0 24rpx;
  background: $color-card;
  border: 1rpx solid $color-border;
  border-radius: 12rpx;
  font-size: 28rpx;
}

.empty {
  padding: 120rpx 48rpx;
  text-align: center;
  color: $color-muted;
}

.status-tag {
  display: inline-block;
  padding: 4rpx 12rpx;
  border-radius: 8rpx;
  font-size: 22rpx;
  line-height: 1.4;
  background: #e2e8f0;
  color: $color-foreground;

  &.warning {
    background: #ffedd5;
    color: $color-warning;
  }

  &.primary {
    background: #dbeafe;
    color: $color-primary;
  }

  &.success {
    background: #dcfce7;
    color: $color-success;
  }
}

.cta-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: $space-md $space-lg calc(#{$space-lg} + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  border-top: 1rpx solid $color-border;
}

.page-with-cta {
  padding-bottom: 180rpx;
}

.error-banner {
  margin-bottom: $space-md;
  padding: $space-md;
  background: #fef2f2;
  color: $color-danger;
  border-radius: 12rpx;
  font-size: 26rpx;
}
</style>
