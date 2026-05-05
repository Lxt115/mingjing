<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUiStore } from '@/store'
import Button from '@/components/ui/Button.vue'

const route = useRoute()
const ui = useUiStore()

const pageTitle = computed(() => (route.meta.title as string) ?? '')
const pageSubtitle = computed(() => (route.meta.subtitle as string) ?? '')

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
    class="h-[60px] bg-[var(--surface)] border-b border-[var(--border)] flex items-center px-7 gap-4 shrink-0"
  >
    <div class="flex-1">
      <h1 class="text-[17px] font-extrabold text-[var(--text1)] leading-tight">{{ pageTitle }}</h1>
      <p class="text-xs text-[var(--text3)] font-medium mt-px">{{ pageSubtitle }}</p>
    </div>

    <div class="flex items-center gap-2.5">
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
