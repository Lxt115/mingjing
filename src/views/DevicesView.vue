<script setup lang="ts">
import { onMounted } from 'vue'
import { useDevicesStore, useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import type { Device } from '@/types'

const devicesStore = useDevicesStore()
const ui = useUiStore()
const { isMobile } = useMediaQuery()

function openUnbind(device: Device) {
  ui.openModal('modal-unbind-confirm', { deviceId: device.id, deviceName: device.name })
}

function triggerOTA(device: Device) {
  ui.showToast(`📡 已触发 ${device.name} 固件升级`)
}

function updateRole(deviceId: string, event: Event) {
  const role = (event.target as HTMLSelectElement).value
  ui.showToast(`✅ 角色已切换`)
  devicesStore.updateRole(deviceId, role)
}

onMounted(() => {
  devicesStore.fetchDevices()
})
</script>

<template>
  <!-- Desktop Layout -->
  <div v-if="!isMobile" class="animate-[fadeIn_.25s_ease]">
    <div class="grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-4">
      <div
        v-for="device in devicesStore.devices"
        :key="device.id"
        class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden p-5 transition-all duration-250 cursor-pointer hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]"
      >
        <div class="flex justify-between items-start mb-4">
          <div class="flex items-center gap-3">
            <div
              :class="[
                'w-10 h-10 rounded-xl flex items-center justify-center text-[20px] shrink-0',
                device.status === 'online' ? 'bg-[#e8fdf5]' : 'bg-[#fff0f0]',
              ]"
            >
              {{ device.emoji }}
            </div>
            <div>
              <div class="text-[15px] font-black text-[var(--text1)]">{{ device.name }}</div>
              <div class="text-xs text-[var(--text3)]">ID: {{ device.id }}</div>
            </div>
          </div>
          <span
            :class="[
              'inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-extrabold',
              device.status === 'online'
                ? 'bg-[#e8fdf5] text-[var(--teal)]'
                : 'bg-[#fff0f0] text-[var(--text3)]',
            ]"
          >
            {{ device.status === 'online' ? '● 在线' : '○ 离线' }}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-4">
          <div>
            <div class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.4px] uppercase mb-1">固件版本</div>
            <div class="text-sm font-black text-[var(--text1)]">{{ device.firmwareVersion }}</div>
          </div>
          <div>
            <div class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.4px] uppercase mb-1">绑定角色</div>
            <select
              class="text-sm font-bold border border-[var(--border)] rounded-lg py-1.5 px-2.5 bg-[var(--bg)] text-[var(--text1)] cursor-pointer outline-none focus:border-[var(--coral)] w-full"
              :value="device.assignedRole"
              @change="updateRole(device.id, $event)"
            >
              <option value="unknown">未指定</option>
              <option value="笃笃">笃笃</option>
              <option value="故事大王">故事大王</option>
            </select>
          </div>
        </div>

        <div class="flex gap-2">
          <button
            v-if="device.hasOTA"
            class="flex-1 h-9 rounded-lg bg-[#e8fdf5] text-[var(--teal)] border-none text-xs font-extrabold cursor-pointer flex items-center justify-center gap-1.5 transition-all duration-200 hover:bg-[#c8f5e8]"
            @click="triggerOTA(device)"
          >
            🔄 升级固件
          </button>
          <button
            class="flex-1 h-9 rounded-lg bg-[#fff0f0] text-[var(--coral)] border-none text-xs font-extrabold cursor-pointer flex items-center justify-center gap-1.5 transition-all duration-200 hover:bg-[#ffe0e0]"
            @click="openUnbind(device)"
          >
            🔓 解除绑定
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div class="flex flex-col gap-3 px-4 pt-2 pb-4">
      <div
        v-for="device in devicesStore.devices"
        :key="device.id"
        class="dev-card bg-[var(--surface)] rounded-[var(--radius-md)] p-4 shadow-[var(--shadow-sm)] transition-all duration-200 active:scale-[.98] border-[1.5px] border-transparent"
        :class="device.status === 'online' ? 'border-[rgba(255,107,107,.18)]' : ''"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-2.5">
            <div
              :class="[
                'w-12 h-12 rounded-[14px] flex items-center justify-center text-xl shrink-0',
                device.status === 'online' ? 'bg-[#e8fdf5]' : 'bg-[#fff0f0]',
              ]"
            >
              {{ device.emoji }}
            </div>
            <div>
              <div class="text-base font-black text-[var(--text1)]">{{ device.name }}</div>
              <div class="text-xs text-[var(--text3)] mt-px font-semibold">{{ device.id }}</div>
            </div>
          </div>
          <div
            :class="[
              'text-xs font-extrabold px-2.5 py-1 rounded-full',
              device.status === 'online'
                ? 'bg-[#e8fdf5] text-[var(--teal)]'
                : 'bg-[#fff0f0] text-[var(--text3)]',
            ]"
          >
            {{ device.status === 'online' ? '在线' : '离线' }}
          </div>
        </div>

        <div class="flex items-center justify-between mb-3 py-2.5 px-3 bg-[var(--bg)] rounded-[10px]">
          <div>
            <div class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.4px] mb-[3px]">固件</div>
            <div class="text-[13px] font-black text-[var(--text1)]">{{ device.firmwareVersion }}</div>
          </div>
          <div>
            <div class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.4px] mb-[3px]">角色</div>
            <select
              class="text-[13px] font-bold bg-transparent border-none text-[var(--text1)] cursor-pointer outline-none"
              :value="device.assignedRole"
              @change="updateRole(device.id, $event)"
            >
              <option value="unknown">未指定</option>
              <option value="笃笃">笃笃</option>
              <option value="故事大王">故事大王</option>
            </select>
          </div>
        </div>

        <div class="flex gap-2">
          <button
            v-if="device.hasOTA"
            class="flex-1 h-9 rounded-[10px] bg-[#e8fdf5] text-[var(--teal)] border-none text-xs font-extrabold cursor-pointer transition-all duration-200 active:scale-[.95]"
            @click="triggerOTA(device)"
          >
            🔄 升级固件
          </button>
          <button
            class="flex-1 h-9 rounded-[10px] bg-[#fff0f0] text-[var(--coral)] border-none text-xs font-extrabold cursor-pointer transition-all duration-200 active:scale-[.95]"
            @click="openUnbind(device)"
          >
            🔓 解除绑定
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
