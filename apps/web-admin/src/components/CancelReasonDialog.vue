<script setup lang="ts">
import { ref, watch } from 'vue'

import type { DictOption } from '@/utils/dictOptions'

const props = defineProps<{
  modelValue: boolean
  title?: string
  confirmText?: string
  loading?: boolean
  options: DictOption[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [cancelReasonCode: string | undefined]
}>()

const selectedCode = ref<string | undefined>(undefined)

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      selectedCode.value = undefined
    }
  },
)

function onClose(): void {
  emit('update:modelValue', false)
}

function onConfirm(): void {
  emit('confirm', selectedCode.value)
  emit('update:modelValue', false)
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    :title="title ?? '确认取消'"
    width="420px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <p class="cancel-hint">取消后单据将不可继续作业。取消原因为可选项，便于后续审计分析。</p>
    <el-form label-width="88px">
      <el-form-item label="取消原因">
        <el-select
          v-model="selectedCode"
          clearable
          placeholder="可选"
          style="width: 100%"
          :loading="loading"
        >
          <el-option
            v-for="option in options"
            :key="option.code"
            :label="option.name"
            :value="option.code"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="onClose">返回</el-button>
      <el-button type="warning" :loading="loading" @click="onConfirm">
        {{ confirmText ?? '确认取消' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.cancel-hint {
  margin: 0 0 16px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
}
</style>
