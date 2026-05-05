<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const ui = useUiStore()
const { isMobile } = useMediaQuery()

const pageTitle = computed(() => (route.meta.title as string) ?? '')
const pageSubtitle = computed(() => (route.meta.subtitle as string) ?? '')

function toggleSidebar() {
  ui.toggleSidebar()
}

function openNewAgent() {
  ui.openModal('modal-agent-config', { mode: 'create' })
}

function openAddDevice() {
  ui.openModal('modal-add-device')
}

function openKbUpload() {
  ui.openModal('modal-kb-new')
}

function openAddSpeaker() {
  ui.openModal('modal-add-speaker')
}
</script>

<template>
  <header
    :class="[
      'flex items-center gap-4 shrink-0 bg-[var(--surface)] border-b border-[var(--border)]',
      isMobile ? 'h-[48px] px-4' : 'h-[60px] px-7',
    ]"
  >
    <button
      v-if="!isMobile"
      class="w-9 h-9 rounded-[10px] bg-[var(--bg2)] flex items-center justify-center text-base cursor-pointer border-none shrink-0 transition-all duration-200 hover:bg-[var(--border)]"
      @click="toggleSidebar"
    >
      ☰
    </button>

    <div class="flex-1 min-w-0">
      <h1
        :class="[
          'font-extrabold text-[var(--text1)] leading-tight',
          isMobile ? 'text-[15px]' : 'text-[17px]',
        ]"
      >
        {{ pageTitle }}
      </h1>
      <p
        v-if="!isMobile"
        class="text-xs text-[var(--text3)] font-medium mt-px"
      >
        {{ pageSubtitle }}
      </p>
    </div>

    <div v-if="!isMobile" class="flex items-center gap-2.5">
      <Button
        v-if="route.path === '/agents'"
        @click="openNewAgent"
      >
        ＋ 新建角色
      </Button>
      <Button
        v-else-if="route.path === '/devices'"
        @click="openAddDevice"
      >
        ➕ 添加设备
      </Button>
      <Button
        v-else-if="route.path === '/knowledge'"
        @click="openKbUpload"
      >
        ＋ 上传知识库
      </Button>
      <Button
        v-else-if="route.path === '/voiceprint'"
        @click="openAddSpeaker"
      >
        ＋ 添加说话人
      </Button>
      <Button
        v-else-if="route.path === '/voice-library'"
        variant="secondary"
        @click="ui.showToast('✅ 已确认使用')"
      >
        确认使用
      </Button>
    </div>
  </header>
</template>
