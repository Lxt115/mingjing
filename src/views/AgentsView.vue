<script setup lang="ts">
import { onMounted } from 'vue'
import { useAgentsStore, useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import type { Agent } from '@/types'

const agentsStore = useAgentsStore()
const ui = useUiStore()
const { isMobile } = useMediaQuery()

function openConfig(agent: Agent) {
  ui.openModal('modal-agent-config', { mode: 'edit', agentId: agent.id })
}

function openManageDevices(agent: Agent) {
  ui.openModal('modal-agent-device', { agentId: agent.id, agentName: agent.name })
}

function openAddDevice(agent: Agent) {
  ui.openModal('modal-add-device', { agentId: agent.id })
}

onMounted(() => {
  agentsStore.fetchAgents()
})
</script>

<template>
  <!-- Desktop Layout -->
  <div v-if="!isMobile" class="animate-[fadeIn_.25s_ease]">
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="stat-card bg-[var(--surface)] rounded-[var(--radius-md)] p-5 border border-[var(--border)] shadow-[var(--shadow-sm)] relative overflow-hidden after:content-[attr(data-icon)] after:absolute after:right-3.5 after:bottom-2.5 after:text-4xl after:opacity-10" data-icon="🤖">
        <div class="text-xs text-[var(--text3)] font-semibold tracking-[.4px] uppercase mb-2">创建角色</div>
        <div class="text-[28px] font-black text-[var(--text1)] leading-none mb-1">{{ agentsStore.agents.length }}</div>
        <div class="text-[11px] text-[var(--text3)] font-medium">共 {{ agentsStore.agents.length }} 个活跃</div>
      </div>
      <div class="stat-card bg-[var(--surface)] rounded-[var(--radius-md)] p-5 border border-[var(--border)] shadow-[var(--shadow-sm)] relative overflow-hidden after:content-[attr(data-icon)] after:absolute after:right-3.5 after:bottom-2.5 after:text-4xl after:opacity-10" data-icon="📱">
        <div class="text-xs text-[var(--text3)] font-semibold tracking-[.4px] uppercase mb-2">绑定设备</div>
        <div class="text-[28px] font-black text-[var(--text1)] leading-none mb-1">2</div>
        <div class="text-[11px] text-[var(--text3)] font-medium">1 台在线</div>
      </div>
      <div class="stat-card bg-[var(--surface)] rounded-[var(--radius-md)] p-5 border border-[var(--border)] shadow-[var(--shadow-sm)] relative overflow-hidden after:content-[attr(data-icon)] after:absolute after:right-3.5 after:bottom-2.5 after:text-4xl after:opacity-10" data-icon="💬">
        <div class="text-xs text-[var(--text3)] font-semibold tracking-[.4px] uppercase mb-2">对话次数</div>
        <div class="text-[28px] font-black text-[var(--text1)] leading-none mb-1">127</div>
        <div class="text-[11px] text-[var(--text3)] font-medium">本月 38 次</div>
      </div>
      <div class="stat-card bg-[var(--surface)] rounded-[var(--radius-md)] p-5 border border-[var(--border)] shadow-[var(--shadow-sm)] relative overflow-hidden after:content-[attr(data-icon)] after:absolute after:right-3.5 after:bottom-2.5 after:text-4xl after:opacity-10" data-icon="⏱️">
        <div class="text-xs text-[var(--text3)] font-semibold tracking-[.4px] uppercase mb-2">陪伴时长</div>
        <div class="text-[28px] font-black text-[var(--text1)] leading-none mb-1">43h</div>
        <div class="text-[11px] text-[var(--text3)] font-medium">较上月 +12h</div>
      </div>
    </div>

    <div class="grid grid-cols-[repeat(auto-fill,minmax(340px,1fr))] gap-4">
      <div
        v-for="agent in agentsStore.agents"
        :key="agent.id"
        class="agent-card bg-[var(--surface)] rounded-[var(--radius-lg)] border-[1.5px] border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden transition-all duration-250 cursor-pointer hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)] hover:border-[rgba(255,107,107,.2)]"
      >
        <div class="flex items-start gap-3.5 p-5 pb-4">
          <div
            class="w-[52px] h-[52px] rounded-2xl flex items-center justify-center text-[26px] shrink-0 shadow-[0_2px_10px_rgba(0,0,0,.1)]"
            :style="{ background: agent.style.gradient }"
          >
            {{ agent.emoji }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-[17px] font-black text-[var(--text1)]">{{ agent.name }}</span>
              <span
                :class="[
                  'inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-extrabold',
                  agent.status === 'online'
                    ? 'bg-[#e8fdf5] text-[var(--teal)]'
                    : 'bg-[#fff0f0] text-[var(--text3)]',
                ]"
              >
                {{ agent.status === 'online' ? '在线' : '离线' }}
              </span>
            </div>
            <div class="text-[13px] text-[var(--text2)] leading-relaxed mb-2.5">{{ agent.description }}</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="tag in agent.tags"
                :key="tag.label"
                class="bg-[var(--bg)] text-[var(--text2)] text-[11px] font-bold px-2 py-0.5 rounded-full"
              >
                {{ tag.icon }} {{ tag.label }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between px-5 py-3 border-t border-[var(--border)] bg-[var(--bg)]">
          <div
            :class="[
              'flex items-center gap-1.5 text-xs font-bold',
              agent.status === 'online' ? 'text-[var(--teal)]' : 'text-[var(--text3)]',
            ]"
          >
            <div
              :class="[
                'w-1.5 h-1.5 rounded-full',
                agent.status === 'online' ? 'bg-[var(--teal)] animate-pulse' : 'bg-[var(--text3)]',
              ]"
            />
            {{ agent.boundDeviceIds.length > 0 ? `设备 101 · ${agent.status === 'online' ? '在线' : '离线'}` : '暂未绑定设备' }}
          </div>
          <div class="flex gap-2">
            <button
            v-if="agent.boundDeviceIds.length > 0"
            class="h-[30px] px-3 rounded-lg bg-[#e8fdf5] text-[var(--teal)] border-none text-xs font-bold cursor-pointer flex items-center gap-1.5 transition-all duration-200 hover:bg-[#c8f5e8]"
            @click="openManageDevices(agent)"
          >
            📱 管理设备（{{ agent.boundDeviceIds.length }}）
          </button>
          <button
            v-else
            class="h-[30px] px-3 rounded-lg bg-[#eef0fc] text-[var(--indigo)] border-none text-xs font-bold cursor-pointer flex items-center gap-1.5 transition-all duration-200 hover:bg-[#dde1f8]"
            @click="openAddDevice(agent)"
          >
            ➕ 添加设备
          </button>
          <button
            class="h-[30px] px-3 rounded-lg bg-[var(--bg2)] text-[var(--text2)] border-none text-xs font-bold cursor-pointer flex items-center gap-1.5 transition-all duration-200 hover:bg-[var(--border)]"
            @click="openConfig(agent)"
          >
            ⚙️ 配置
          </button>
          </div>
        </div>
      </div>

      <div
        class="bg-[var(--surface)] rounded-[var(--radius-lg)] border-2 border-dashed border-[var(--border)] flex flex-col items-center justify-center gap-2.5 py-10 px-5 cursor-pointer transition-all duration-200 min-h-[200px] hover:bg-[var(--bg)] hover:border-[var(--coral-lt)] group"
        @click="ui.openModal('modal-agent-config', { mode: 'create' })"
      >
        <div class="w-12 h-12 rounded-2xl bg-[var(--bg2)] text-[var(--text3)] flex items-center justify-center text-[22px] transition-all duration-200 group-hover:bg-[rgba(255,107,107,.12)] group-hover:text-[var(--coral)]">
          ＋
        </div>
        <div class="text-sm font-bold text-[var(--text3)] transition-colors duration-200 group-hover:text-[var(--coral)]">
          新建角色
        </div>
        <div class="text-xs text-[var(--text3)] text-center max-w-[180px] leading-relaxed">
          自定义 AI 角色，绑定设备后即可开始对话
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div class="flex flex-col gap-3 px-4 pt-2 pb-4">
      <div
        v-for="agent in agentsStore.agents"
        :key="agent.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] p-4 flex items-start justify-between gap-3 cursor-pointer shadow-[var(--shadow-sm)] border-[1.5px] border-transparent transition-all duration-[.22s] active:scale-[.98]"
        :class="agent.status === 'online' ? 'border-[rgba(255,107,107,.18)]' : ''"
        @click="openConfig(agent)"
      >
        <div class="flex items-start gap-3 flex-1 min-w-0">
          <div
            class="w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0 shadow-[0_2px_8px_rgba(0,0,0,.1)]"
            :style="{ background: agent.style.gradient }"
          >
            {{ agent.emoji }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-base font-black text-[var(--text1)] mb-1">{{ agent.name }}</div>
            <div class="text-xs text-[var(--text3)] leading-relaxed mb-2 whitespace-nowrap overflow-hidden text-ellipsis">{{ agent.description }}</div>
            <div class="flex flex-wrap gap-1">
              <span
                v-for="tag in agent.tags"
                :key="tag.label"
                class="bg-[var(--bg2)] text-[var(--text2)] text-[11px] font-bold px-2 py-0.5 rounded-[20px]"
              >
                {{ tag.icon }} {{ tag.label }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex flex-col items-end gap-2 shrink-0">
          <div class="flex items-center gap-1 text-[11px] font-bold text-[var(--teal)]">
            <div class="w-[7px] h-[7px] rounded-full bg-[var(--teal)] animate-pulse" v-if="agent.status === 'online'" />
            {{ agent.status === 'online' ? '在线' : '离线' }}
          </div>
          <button
            v-if="agent.boundDeviceIds.length > 0"
            class="py-1 px-2.5 rounded-[10px] bg-[#e8fdf5] text-[var(--teal)] border-none text-[11px] font-bold cursor-pointer transition-all duration-200 active:scale-[.9]"
            @click.stop="openManageDevices(agent)"
          >
            📱 设备（{{ agent.boundDeviceIds.length }}）
          </button>
          <button
            v-else
            class="py-1 px-2.5 rounded-[10px] bg-[#eef0fc] text-[var(--indigo)] border-none text-[11px] font-bold cursor-pointer transition-all duration-200 active:scale-[.9]"
            @click.stop="openAddDevice(agent)"
          >
            ➕ 添加
          </button>
        </div>
      </div>

      <div
        class="flex flex-col items-center gap-2 py-5 cursor-pointer bg-[var(--surface)] rounded-[var(--radius-md)] border-2 border-dashed border-[var(--border)] transition-all duration-200 active:scale-[.97]"
        @click="ui.openModal('modal-agent-config', { mode: 'create' })"
      >
        <div class="w-10 h-10 rounded-2xl bg-[var(--bg2)] text-[var(--text3)] flex items-center justify-center text-xl">＋</div>
        <div class="text-sm font-bold text-[var(--text3)]">新建角色</div>
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
