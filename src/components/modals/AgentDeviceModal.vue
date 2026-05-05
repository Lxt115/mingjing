<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Device } from '@/types'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { Switch } from '@/components/ui'

const { close } = useModal()
const ui = useUiStore()

const agentName = computed(() => (ui.modalData.agentName as string) ?? '角色')
const agentId = computed(() => (ui.modalData.agentId as string) ?? '')
const agentDevices = ref<Device[]>([])
const loaded = ref(false)

async function loadDevices() {
  const res = await apiService.devices.getList()
  agentDevices.value = res.data.filter((d) => d.boundAgentId === agentId.value)
  loaded.value = true
}

function doAddDevice() {
  close()
  ui.openModal('modal-add-device')
}

function doUnbindDevice(device: Device) {
  close()
  ui.openModal('modal-unbind-confirm', { device })
}

loadDevices()
</script>

<template>
  <div>
    <button
      class="w-full mb-4 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] py-3 px-5 text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px"
      @click="doAddDevice"
    >
      ➕ 添加新设备
    </button>

    <div
      v-for="device in agentDevices"
      :key="device.id"
      class="bg-[var(--surface)] rounded-[var(--radius-lg)] border-[1.5px] border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden mb-3"
    >
      <div class="flex items-center justify-between px-[18px] py-4 border-b border-[var(--border)]">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-2xl flex items-center justify-center text-[22px] bg-gradient-to-br from-[var(--teal)] to-[#0AB4EE] shadow-[0_2px_10px_rgba(0,201,167,.25)]">
            🤖
          </div>
          <div>
            <div class="text-[15px] font-black text-[var(--text1)]">{{ device.name }}</div>
            <div class="text-[11px] text-[var(--text3)] mt-0.5 font-mono">{{ device.mac }}</div>
          </div>
        </div>
        <div class="flex items-center gap-1.5 py-1 px-3 rounded-full text-xs font-bold bg-[#e8fdf5] text-[var(--teal)]">
          <span class="w-1.5 h-1.5 rounded-full bg-[var(--teal)] inline-block animate-pulse"></span>
          在线
        </div>
      </div>

      <div>
        <div class="flex justify-between items-center px-[18px] py-[11px] border-b border-[var(--border)]">
          <span class="text-[13px] font-semibold text-[var(--text2)]">固件版本</span>
          <span class="text-[13px] font-bold text-[var(--text1)] flex items-center gap-1.5">
            {{ device.firmwareVersion }}
            <span
              v-if="device.otaStatus === 'pending'"
              class="text-[10px] font-extrabold bg-[#fff8e6] text-[var(--amber)] px-2 py-0.5 rounded-[10px]"
            > 有更新 </span>
          </span>
        </div>

        <div class="flex justify-between items-center px-[18px] py-[11px]">
          <span class="text-[13px] font-semibold text-[var(--text2)]">OTA 升级</span>
          <Switch
            :model-value="device.autoUpgrade"
            @update:model-value="device.autoUpgrade = !device.autoUpgrade"
          />
        </div>
      </div>

      <div class="px-[18px] py-3.5 border-t border-[var(--border)]">
        <button
          class="w-full py-2 rounded-[var(--radius-sm)] border-[1.5px] border-[var(--coral)] bg-[#fff0f0] text-[var(--coral)] text-[13px] font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--coral)] hover:text-white"
          @click="doUnbindDevice(device)"
        >
          解绑设备
        </button>
      </div>
    </div>

    <div
      v-if="loaded && agentDevices.length === 0"
      class="text-center text-[var(--text3)] py-8 text-sm font-semibold"
    >
      暂无绑定设备
    </div>

    <div class="flex gap-3 mt-2">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        关闭
      </button>
    </div>
  </div>
</template>
