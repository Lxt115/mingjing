<script setup lang="ts">
import { useUiStore, useUserStore } from '@/store'
import { Switch } from '@/components/ui'

const ui = useUiStore()
const user = useUserStore()
</script>

<template>
  <div class="animate-[fadeIn_.25s_ease] grid grid-cols-[320px_1fr] gap-5 items-start">
    <div>
      <div class="relative overflow-hidden bg-gradient-to-br from-[var(--indigo)] to-[var(--teal)] rounded-[var(--radius-lg)] p-7 mb-5 shadow-[0_8px_32px_rgba(92,107,192,.2)]">
        <div class="absolute -top-[60px] -right-[60px] w-[200px] h-[200px] rounded-full bg-white/8 pointer-events-none"></div>
        <div class="absolute -bottom-10 -left-5 w-[120px] h-[120px] rounded-full bg-white/6 pointer-events-none"></div>

        <div class="w-[72px] h-[72px] rounded-[22px] bg-white/20 flex items-center justify-center text-4xl mb-3.5 relative z-[1] border-2 border-white/30">
          {{ user.profile.avatarEmoji }}
        </div>
        <div class="text-[22px] font-black text-white mb-1 relative z-[1]">{{ user.profile.name }}</div>
        <div class="text-xs text-white/60 relative z-[1] mb-5">ID: {{ user.profile.userId }} · v{{ user.profile.version }}</div>

        <div class="grid grid-cols-3 gap-3 relative z-[1]">
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.totalConversations }}</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">对话次数</div>
          </div>
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.totalHours }}h</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">陪伴时长</div>
          </div>
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.boundDeviceCount }}</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">绑定设备</div>
          </div>
        </div>
      </div>
    </div>

    <div>
      <div class="mb-5">
        <div class="text-[11px] font-extrabold text-[var(--text3)] tracking-[.8px] uppercase mb-2.5 pl-0.5">账号设置</div>
        <div class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden">
          <div class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)] cursor-pointer transition-colors duration-150 hover:bg-[var(--bg)]" @click="ui.showToast('功能开发中…')">
            <div class="flex items-center gap-3">
              <div class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#e8fdf5]">🔒</div>
              <div class="text-sm font-bold text-[var(--text1)]">隐私设置</div>
            </div>
            <span class="text-[var(--text3)] text-base">›</span>
          </div>

          <div class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)]">
            <div class="flex items-center gap-3">
              <div class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#fff8e6]">🔔</div>
              <div class="text-sm font-bold text-[var(--text1)]">消息通知</div>
            </div>
            <Switch :model-value="user.notificationEnabled" @update:model-value="user.toggleNotification" />
          </div>

          <div class="flex justify-between items-center px-[18px] py-3.5 cursor-pointer transition-colors duration-150 hover:bg-[var(--bg)]" @click="ui.showToast('当前版本 v4.0.0')">
            <div class="flex items-center gap-3">
              <div class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#eef0fc]">ℹ️</div>
              <div>
                <div class="text-sm font-bold text-[var(--text1)]">关于明境</div>
                <div class="text-xs text-[var(--text3)] mt-px">版本 v{{ user.profile.version }}</div>
              </div>
            </div>
            <span class="text-[var(--text3)] text-base">›</span>
          </div>
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
