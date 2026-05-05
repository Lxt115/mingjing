<script setup lang="ts">
import { computed } from 'vue'
import type { Device } from '@/types'
import { useModal } from '@/composables'
import { useUiStore, useDevicesStore } from '@/store'

const { close } = useModal()
const ui = useUiStore()
const devicesStore = useDevicesStore()

const device = computed(() => ui.modalData.device as Device | undefined)

async function confirmUnbind() {
  if (!device.value) return
  try {
    await devicesStore.unbindDevice(device.value.id)
    close()
    ui.showToast(`✅ 「${device.value.name}」已解绑`)
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 解绑失败', 'error')
  }
}
</script>

<template>
  <div>
    <p class="text-sm text-[var(--text2)] leading-relaxed font-medium">
      确定要解绑「{{ device?.name }}」吗？解绑后该设备将无法使用当前账号的角色和数据。
    </p>

    <div class="flex gap-3 mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] border-none text-sm font-extrabold cursor-pointer bg-gradient-to-br from-[var(--coral)] to-[#FF4D4D] text-white shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.5)]"
        @click="confirmUnbind"
      >
        确认解绑
      </button>
    </div>
  </div>
</template>
