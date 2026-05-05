<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Device } from '@/types'
import { apiService } from '@/services'
import { useUiStore, useAgentsStore } from '@/store'
import { Switch, InfoTip } from '@/components/ui'

const ui = useUiStore()
const agentsStore = useAgentsStore()
const devices = ref<Device[]>([])
const loading = ref(false)

async function loadDevices() {
  loading.value = true
  try {
    const res = await apiService.devices.getList()
    devices.value = res.data
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDevices()
  agentsStore.fetchAgents()
})

function openAddDevice() {
  ui.openModal('modal-add-device')
}

function openUnbindConfirm(device: Device) {
  ui.openModal('modal-unbind-confirm', { device })
}

function toggleAutoUpgrade(index: number) {
  const d = devices.value[index]
  d.autoUpgrade = !d.autoUpgrade
  const msg = d.autoUpgrade ? '✅ 自动升级已开启' : '🔒 自动升级已关闭'
  ui.showToast(msg)
}

async function changeRole(index: number, agentId: string) {
  const d = devices.value[index]
  if (!agentId) return
  try {
    await apiService.devices.assignRole(d.id, agentId)
    d.boundAgentId = agentId
    const agent = agentsStore.agents.find((a) => a.id === agentId)
    d.boundAgentName = agent?.name ?? null
    ui.showToast(`✅ 已切换为「${agent?.name ?? agentId}」`)
  } catch {
    ui.showToast('❌ 角色切换失败', 'error')
  }
}

async function upgradeFirmware(index: number) {
  const d = devices.value[index]
  try {
    const res = await apiService.devices.upgradeFirmware(d.id)
    const idx = devices.value.findIndex((dev) => dev.id === d.id)
    if (idx !== -1) devices.value[idx] = res.data
    ui.showToast('✅ 固件升级中…')
  } catch {
    ui.showToast('❌ 固件升级失败', 'error')
  }
}
</script>

<template>
  <div class="animate-[fadeIn_.25s_ease]">
    <div class="grid grid-cols-[repeat(auto-fill,minmax(360px,1fr))] gap-4">
      <div v-if="loading" class="col-span-full text-center text-[var(--text3)] py-10 text-sm font-semibold">
        加载中…
      </div>

      <div
        v-for="(device, idx) in devices"
        :key="device.id"
        class="bg-[var(--surface)] rounded-[var(--radius-lg)] border-[1.5px] border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden transition-all duration-200 hover:shadow-[var(--shadow-md)] hover:-translate-y-0.5"
      >
        <div class="flex items-center justify-between px-[18px] py-4 border-b border-[var(--border)]">
          <div class="flex items-center gap-3">
            <div
              :class="[
                'w-11 h-11 rounded-2xl flex items-center justify-center text-[22px] shadow-[0_2px_10px_rgba(0,201,167,.25)]',
                device.status === 'online'
                  ? 'bg-gradient-to-br from-[var(--teal)] to-[#0AB4EE]'
                  : 'bg-gradient-to-br from-[#a78bfa] to-[#7c3aed]',
              ]"
            >
              🤖
            </div>
            <div>
              <div class="text-[15px] font-black text-[var(--text1)]">{{ device.name }}</div>
              <div class="text-[11px] text-[var(--text3)] mt-0.5 font-mono tracking-[.4px]">{{ device.mac }}</div>
            </div>
          </div>
          <div
            :class="[
              'flex items-center gap-1.5 py-1 px-3 rounded-full text-xs font-bold',
              device.status === 'online'
                ? 'bg-[#e8fdf5] text-[var(--teal)]'
                : 'bg-[var(--bg2)] text-[var(--text3)]',
            ]"
          >
            <div
              :class="[
                'w-1.5 h-1.5 rounded-full',
                device.status === 'online' ? 'bg-[var(--teal)] animate-pulse' : 'bg-[var(--text3)]',
              ]"
            />
            {{ device.status === 'online' ? '在线' : '离线' }}
          </div>
        </div>

        <div class="py-1">
          <div
            v-if="device.lastConversation"
            class="flex justify-between items-center px-[18px] py-[11px] border-b border-[var(--border)]"
          >
            <span class="text-[13px] font-semibold text-[var(--text2)]">最近对话</span>
            <span class="text-[13px] font-bold text-[var(--text3)]">{{ device.lastConversation }}</span>
          </div>

          <div class="flex justify-between items-center px-[18px] py-[11px] border-b border-[var(--border)]">
            <span class="text-[13px] font-semibold text-[var(--text2)]">固件版本</span>
            <span class="text-[13px] font-bold text-[var(--text1)] flex items-center gap-1.5">
              {{ device.firmwareVersion }}
              <span
                v-if="device.otaStatus === 'pending'"
                class="text-[10px] font-extrabold bg-[#fff8e6] text-[var(--amber)] px-2 py-0.5 rounded-[10px] cursor-pointer hover:bg-[var(--amber)] hover:text-white transition-colors"
                @click="upgradeFirmware(idx)"
              >
                有更新
              </span>
              <span
                v-else-if="device.otaStatus === 'latest'"
                class="text-[10px] font-extrabold bg-[#e8fdf5] text-[var(--teal)] px-2 py-0.5 rounded-[10px]"
              >
                最新
              </span>
            </span>
          </div>

          <div class="flex justify-between items-center px-[18px] py-[11px] border-b border-[var(--border)]">
            <span class="text-[13px] font-semibold text-[var(--text2)]">自动升级</span>
            <Switch :model-value="device.autoUpgrade" @update:model-value="toggleAutoUpgrade(idx)" />
          </div>

          <div class="flex justify-between items-center px-[18px] py-[11px]">
            <span class="text-[13px] font-semibold text-[var(--text2)]">角色配置</span>
            <select
              class="text-[13px] font-bold text-[var(--text1)] bg-[var(--bg2)] border-none rounded-lg px-2.5 py-1 cursor-pointer outline-none"
              :value="device.boundAgentId ?? ''"
              @change="changeRole(idx, ($event.target as HTMLSelectElement).value)"
            >
              <option
                v-for="agent in agentsStore.agents"
                :key="agent.id"
                :value="agent.id"
                :selected="agent.id === device.boundAgentId"
              >
                {{ agent.name }}
              </option>
            </select>
          </div>
        </div>

        <div class="px-[18px] py-3.5 border-t border-[var(--border)]">
          <button
            class="w-full py-2 rounded-[var(--radius-sm)] border-[1.5px] border-[var(--coral)] bg-[#fff0f0] text-[var(--coral)] text-[13px] font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--coral)] hover:text-white"
            @click="openUnbindConfirm(device)"
          >
            解绑设备
          </button>
        </div>
      </div>

      <div
        class="bg-[var(--surface)] rounded-[var(--radius-lg)] border-2 border-dashed border-[var(--border)] flex flex-col items-center justify-center gap-2.5 py-10 px-5 cursor-pointer transition-all duration-200 min-h-[200px] hover:bg-[var(--bg)] hover:border-[var(--coral-lt)] group"
        @click="openAddDevice"
      >
        <div class="w-12 h-12 rounded-2xl bg-[var(--bg2)] text-[var(--text3)] flex items-center justify-center text-[22px] transition-all duration-200 group-hover:bg-[rgba(255,107,107,.12)] group-hover:text-[var(--coral)]">
          ＋
        </div>
        <div class="text-sm font-bold text-[var(--text3)] transition-colors duration-200 group-hover:text-[var(--coral)]">
          添加新设备
        </div>
        <div class="text-xs text-[var(--text3)] text-center max-w-[200px] leading-relaxed">
          开启设备电源，通过6位验证码绑定
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
