<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUiStore, useUserStore } from '@/store'

const route = useRoute()
const router = useRouter()
const ui = useUiStore()
const user = useUserStore()

interface NavItemConfig {
  path: string
  label: string
  icon: string
  badge?: number
}

const mainNav: NavItemConfig[] = [
  { path: '/agents', label: 'AI 伙伴', icon: '🤖' },
  { path: '/history', label: '历史记录', icon: '💬' },
  { path: '/devices', label: '设备管理', icon: '📱' },
]

const configNav: NavItemConfig[] = [
  { path: '/voice-library', label: '声音库', icon: '🔊' },
  { path: '/knowledge', label: '知识库', icon: '📚' },
  { path: '/voiceprint', label: '声纹识别', icon: '🎙️' },
]

const accountNav: NavItemConfig[] = [{ path: '/profile', label: '我的', icon: '👤' }]

function isActive(path: string): boolean {
  return route.path === path || route.path.startsWith(path + '/')
}

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <nav
    :class="[
      'bg-[var(--sidebar)] flex flex-col shrink-0 h-screen relative overflow-hidden transition-all duration-300',
      ui.sidebarCollapsed ? 'w-0' : 'w-[var(--sidebar-w)]',
    ]"
  >
    <div
      class="absolute -top-20 -right-20 w-60 h-60 rounded-full bg-[radial-gradient(circle,rgba(255,107,107,.18)_0%,transparent_70%)] pointer-events-none"
    ></div>
    <div
      class="absolute bottom-10 -left-[60px] w-[180px] h-[180px] rounded-full bg-[radial-gradient(circle,rgba(0,201,167,.1)_0%,transparent_70%)] pointer-events-none"
    ></div>

    <div class="flex items-center gap-3 px-6 pt-7 pb-6 border-b border-white/7">
      <div
        class="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] flex items-center justify-center text-lg shadow-[0_4px_12px_rgba(255,107,107,.4)] shrink-0"
      >
        🪞
      </div>
      <div>
        <div class="text-lg font-extrabold text-white tracking-[.5px]">明境</div>
        <div class="text-[10px] text-white/35 font-medium tracking-[.8px]">AI COMPANION v4.0</div>
      </div>
    </div>

    <div class="flex-1 flex flex-col gap-1 px-3 py-5 overflow-y-auto">
      <template v-for="(item, idx) in mainNav" :key="item.path">
        <div
          v-if="idx === 0"
          class="text-[10px] font-bold text-white/30 tracking-[1.2px] uppercase px-3 pt-[14px] pb-1.5"
        >
          主功能
        </div>
        <button
          :class="[
            'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-sm)] cursor-pointer border-none text-left w-full transition-all duration-200 relative bg-transparent',
            isActive(item.path) ? 'bg-[rgba(255,107,107,.16)]' : 'hover:bg-white/6',
          ]"
          @click="navigate(item.path)"
        >
          <div
            v-if="isActive(item.path)"
            class="absolute left-0 top-1/5 bottom-1/5 w-[3px] rounded-[2px] bg-[var(--coral)]"
          ></div>
          <div
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center text-[15px] shrink-0 transition-all duration-200',
              isActive(item.path) ? 'bg-[rgba(255,107,107,.25)]' : 'bg-white/6',
            ]"
          >
            {{ item.icon }}
          </div>
          <span
            :class="[
              'text-[13.5px] font-semibold transition-colors duration-200',
              isActive(item.path) ? 'text-white/90' : 'text-white/55',
            ]"
          >
            {{ item.label }}
          </span>
        </button>
      </template>

      <div
        class="text-[10px] font-bold text-white/30 tracking-[1.2px] uppercase px-3 pt-[14px] pb-1.5"
      >
        配置
      </div>
      <button
        v-for="item in configNav"
        :key="item.path"
        :class="[
          'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-sm)] cursor-pointer border-none text-left w-full transition-all duration-200 relative bg-transparent',
          isActive(item.path) ? 'bg-[rgba(255,107,107,.16)]' : 'hover:bg-white/6',
        ]"
        @click="navigate(item.path)"
      >
        <div
          v-if="isActive(item.path)"
          class="absolute left-0 top-1/5 bottom-1/5 w-[3px] rounded-[2px] bg-[var(--coral)]"
        ></div>
        <div
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center text-[15px] shrink-0 transition-all duration-200',
            isActive(item.path) ? 'bg-[rgba(255,107,107,.25)]' : 'bg-white/6',
          ]"
        >
          {{ item.icon }}
        </div>
        <span
          :class="[
            'text-[13.5px] font-semibold transition-colors duration-200',
            isActive(item.path) ? 'text-white/90' : 'text-white/55',
          ]"
        >
          {{ item.label }}
        </span>
      </button>

      <div
        class="text-[10px] font-bold text-white/30 tracking-[1.2px] uppercase px-3 pt-[14px] pb-1.5"
      >
        账号
      </div>
      <button
        v-for="item in accountNav"
        :key="item.path"
        :class="[
          'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-sm)] cursor-pointer border-none text-left w-full transition-all duration-200 relative bg-transparent',
          isActive(item.path) ? 'bg-[rgba(255,107,107,.16)]' : 'hover:bg-white/6',
        ]"
        @click="navigate(item.path)"
      >
        <div
          v-if="isActive(item.path)"
          class="absolute left-0 top-1/5 bottom-1/5 w-[3px] rounded-[2px] bg-[var(--coral)]"
        ></div>
        <div
          :class="[
            'w-8 h-8 rounded-lg flex items-center justify-center text-[15px] shrink-0 transition-all duration-200',
            isActive(item.path) ? 'bg-[rgba(255,107,107,.25)]' : 'bg-white/6',
          ]"
        >
          {{ item.icon }}
        </div>
        <span
          :class="[
            'text-[13.5px] font-semibold transition-colors duration-200',
            isActive(item.path) ? 'text-white/90' : 'text-white/55',
          ]"
        >
          {{ item.label }}
        </span>
      </button>
    </div>

    <div
      class="flex items-center gap-2.5 px-5 py-4 border-t border-white/7 cursor-pointer hover:bg-white/4 transition-colors duration-200"
      @click="navigate('/profile')"
    >
      <div
        class="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[var(--indigo)] to-[var(--teal)] flex items-center justify-center text-lg shrink-0"
      >
        {{ user.profile.avatarEmoji }}
      </div>
      <div>
        <div class="text-[13px] font-bold text-white/80">{{ user.profile.name }}</div>
        <div class="text-[11px] text-white/30 mt-px">ID: {{ user.profile.userId }}</div>
      </div>
    </div>
  </nav>
</template>
