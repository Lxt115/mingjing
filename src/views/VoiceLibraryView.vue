<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import { apiService } from '@/services'
import { Tabs } from '@/components/ui'
import type { Voice } from '@/types'

const ui = useUiStore()
const { isMobile } = useMediaQuery()
const voices = ref<Voice[]>([])
const activeTab = ref('system')
const tabs = [
  { id: 'system', label: '系统音色' },
  { id: 'cloned', label: '我的克隆' },
  { id: 'fav', label: '收藏' },
]

function selectVoice(voice: Voice) {
  voice.selected = !voice.selected
  ui.showToast(voice.selected ? `✅ 已选中 ${voice.name}` : `已取消 ${voice.name}`)
}

function playPreview(voice: Voice) {
  ui.showToast(`🔊 试听中：${voice.name}`)
}

function confirmSelection() {
  ui.showToast('✅ 已确认使用当前选择的音色')
}

onMounted(async () => {
  const res = await apiService.voices.getList()
  voices.value = res.data
})
</script>

<template>
  <!-- Desktop Layout -->
  <div v-if="!isMobile" class="animate-[fadeIn_.25s_ease]">
    <div class="mb-5">
      <div
        class="clone-banner border border-[var(--border)] py-5 px-6 rounded-[var(--radius-lg)] bg-[var(--surface)] flex items-center justify-between gap-4 mb-5 cursor-pointer shadow-[var(--shadow-sm)] transition-all duration-200 hover:shadow-[var(--shadow-md)] hover:border-[rgba(255,107,107,.15)]"
        @click="ui.openModal('modal-clone-voice')"
      >
        <div class="flex items-center gap-4">
          <div
            class="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] flex items-center justify-center text-[22px]"
          >
            🎤
          </div>
          <div>
            <div class="text-base font-black text-[var(--text1)] mb-1">克隆我的声音</div>
            <div class="text-xs text-[var(--text3)] leading-relaxed">
              录制 3 段短文本，AI 即可学习你的音色
            </div>
          </div>
        </div>
        <div
          class="text-[var(--coral)] text-xs font-extrabold px-4 py-2 rounded-lg bg-[rgba(255,107,107,.1)]"
        >
          开始录制 →
        </div>
      </div>

      <Tabs v-model="activeTab" :tabs="tabs" />

      <div class="mt-4 grid grid-cols-3 gap-3">
        <div
          v-for="voice in voices"
          :key="voice.id"
          :class="[
            'bg-[var(--surface)] rounded-[var(--radius-md)] border-[1.5px] border-[var(--border)] p-4 cursor-pointer transition-all duration-[.22s] hover:shadow-[var(--shadow-md)] hover:-translate-y-[2px]',
            voice.selected ? 'border-[var(--coral)] shadow-[0_0_0_3px_rgba(255,107,107,.12)]' : '',
          ]"
          @click="selectVoice(voice)"
        >
          <div class="flex items-center gap-3 mb-3">
            <div
              class="w-[42px] h-[42px] rounded-xl flex items-center justify-center text-xl shrink-0 shadow-[0_2px_10px_rgba(0,0,0,.1)]"
              :style="{ background: voice.gradient }"
            >
              {{ voice.emoji }}
            </div>
            <div class="flex-1 min-w-0">
              <div
                class="text-sm font-extrabold text-[var(--text1)] whitespace-nowrap overflow-hidden text-ellipsis"
              >
                {{ voice.name }}
              </div>
              <div class="text-[11px] text-[var(--text3)]">{{ voice.category }}</div>
            </div>
            <div
              v-if="voice.selected"
              class="w-6 h-6 rounded-full bg-[var(--coral)] text-white flex items-center justify-center text-[11px] font-extrabold shrink-0"
            >
              ✓
            </div>
          </div>

          <div class="flex flex-wrap gap-1 mb-3">
            <span
              class="bg-[var(--bg)] text-[var(--text3)] text-[11px] font-bold px-2 py-0.5 rounded-full"
            >
              {{ voice.language }}
            </span>
            <span
              class="bg-[var(--bg)] text-[var(--text3)] text-[11px] font-bold px-2 py-0.5 rounded-full"
            >
              {{ voice.style }}
            </span>
          </div>

          <button
            class="w-full h-9 rounded-lg bg-[var(--bg2)] text-[var(--text2)] border-none text-xs font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
            @click.stop="playPreview(voice)"
          >
            ▶ 试听
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div
      class="clone-banner-mobile flex items-center justify-between py-3.5 px-4 bg-gradient-to-r from-[var(--coral)]/10 to-transparent active:scale-[.98] transition-transform duration-200"
      @click="ui.openModal('modal-clone-voice')"
    >
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl bg-[var(--coral)] flex items-center justify-center text-lg"
        >
          🎤
        </div>
        <div>
          <div class="text-sm font-extrabold text-[var(--text1)]">克隆我的声音</div>
          <div class="text-xs text-[var(--text3)]">录制 3 段短文本即可学习你的音色</div>
        </div>
      </div>
      <div
        class="text-[var(--coral)] text-xs font-extrabold px-3 py-1.5 rounded-[20px] bg-[rgba(255,107,107,.12)]"
      >
        录制 →
      </div>
    </div>

    <div class="tabs-mobile flex gap-1 px-4 pt-3 pb-4">
      <div
        v-for="tab in tabs"
        :key="tab.id"
        :class="[
          'flex-1 py-2 px-0 rounded-[20px] text-center text-xs font-extrabold transition-all duration-200 cursor-pointer',
          activeTab === tab.id
            ? 'bg-[var(--coral)] text-white'
            : 'bg-[var(--bg2)] text-[var(--text2)]',
        ]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-4">
      <div
        v-for="voice in voices"
        :key="voice.id"
        :class="[
          'bg-[var(--surface)] rounded-[var(--radius-md)] py-3.5 px-4 mb-2.5 cursor-pointer shadow-[var(--shadow-sm)] transition-all duration-[.22s] active:scale-[.98] border-[1.5px]',
          voice.selected ? 'border-[var(--coral)]' : 'border-transparent',
        ]"
        @click="selectVoice(voice)"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5 flex-1 min-w-0">
            <div
              class="w-[42px] h-[42px] rounded-[14px] flex items-center justify-center text-xl shrink-0 shadow-[0_2px_8px_rgba(0,0,0,.08)]"
              :style="{ background: voice.gradient }"
            >
              {{ voice.emoji }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-[3px]">
                <span class="text-[15px] font-extrabold text-[var(--text1)]">{{ voice.name }}</span>
                <span
                  class="text-[11px] font-bold text-[var(--text3)] bg-[var(--bg)] px-2 py-0.5 rounded-[20px]"
                  >{{ voice.category }}</span
                >
              </div>
              <div class="flex gap-1">
                <span
                  class="text-[11px] text-[var(--text3)] bg-[var(--bg2)] px-2 py-0.5 rounded-[20px] font-bold"
                  >{{ voice.language }}</span
                >
                <span
                  class="text-[11px] text-[var(--text3)] bg-[var(--bg2)] px-2 py-0.5 rounded-[20px] font-bold"
                  >{{ voice.style }}</span
                >
              </div>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button
              class="w-8 h-8 rounded-full bg-[var(--bg2)] border-none cursor-pointer flex items-center justify-center text-xs text-[var(--text2)] transition-all duration-200 active:scale-[.9]"
              @click.stop="playPreview(voice)"
            >
              ▶
            </button>
            <div
              v-if="voice.selected"
              class="w-6 h-6 rounded-full bg-[var(--coral)] text-white flex items-center justify-center text-[11px] font-extrabold"
            >
              ✓
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="voices.some((v) => v.selected)"
      class="fixed bottom-20 left-0 right-0 px-4 py-3 bg-white/95 backdrop-blur-[12px] border-t border-[var(--border)] flex items-center justify-between z-40"
    >
      <span class="text-sm font-extrabold text-[var(--text1)]"
        >已选 {{ voices.filter((v) => v.selected).length }} 个声音</span
      >
      <button
        class="py-2 px-5 rounded-[10px] bg-[var(--coral)] text-white border-none text-sm font-extrabold cursor-pointer transition-all duration-200 active:scale-[.95]"
        @click="confirmSelection"
      >
        确认使用
      </button>
    </div>
  </div>
</template>
