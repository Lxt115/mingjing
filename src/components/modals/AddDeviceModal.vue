<script setup lang="ts">
import { useModal, useDeviceBind } from '@/composables'
import { InfoTip } from '@/components/ui'

const { close } = useModal()
const { deviceCode, isSubmitting, submitBind } = useDeviceBind()
</script>

<template>
  <div>
    <InfoTip>请先开启设备电源，等待设备报出6位验证码</InfoTip>
    <div class="mt-4">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">验证码 *</label>
      <input
        v-model="deviceCode"
        class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
        placeholder="请输入6位数字验证码"
        maxlength="6"
        inputmode="numeric"
      />
    </div>

    <div class="flex gap-3 mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        class="flex-1 py-3 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)]"
        :disabled="isSubmitting"
        @click="submitBind()"
      >
        {{ isSubmitting ? '绑定中…' : '确认绑定' }}
      </button>
    </div>
  </div>
</template>
