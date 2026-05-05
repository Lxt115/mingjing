<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

interface TabItem {
  path: string
  label: string
  icon: string
  matchRoutes: string[]
}

const tabs: TabItem[] = [
  { path: '/agents', label: '伙伴', icon: '🤖', matchRoutes: ['/agents'] },
  { path: '/history', label: '历史', icon: '💬', matchRoutes: ['/history'] },
  { path: '/profile', label: '我的', icon: '👤', matchRoutes: ['/profile'] },
]

function isActive(tab: TabItem): boolean {
  return tab.matchRoutes.some((p) => route.path === p || route.path.startsWith(p + '/'))
}

function navigate(path: string) {
  router.push(path)
}
</script>

<template>
  <nav
    class="h-[72px] bg-white/95 backdrop-blur-[16px] border-t border-[var(--border)] flex items-center justify-around shrink-0 pb-1.5"
  >
    <div
      v-for="tab in tabs"
      :key="tab.path"
      :class="['flex flex-col items-center gap-1 cursor-pointer py-1.5 px-0 transition-all duration-200']"
      @click="navigate(tab.path)"
    >
      <div
        :class="[
          'w-7 h-7 rounded-[10px] flex items-center justify-center text-base transition-all duration-250',
          isActive(tab)
            ? 'bg-[var(--coral)] scale-110'
            : 'bg-[var(--bg2)]',
        ]"
      >
        {{ tab.icon }}
      </div>
      <span
        :class="[
          'text-[10px] font-bold tracking-[.3px]',
          isActive(tab) ? 'text-[var(--coral)]' : 'text-[var(--text3)]',
        ]"
      >
        {{ tab.label }}
      </span>
    </div>
  </nav>
</template>
