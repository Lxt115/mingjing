<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { Voice } from '@/types'
import { apiService } from '@/services'
import { useUiStore } from '@/store'
import { Tabs } from '@/components/ui'

const ui = useUiStore()

const voiceTabs = [
  { id: 'female' as const, label: '女声', icon: '🎀' },
  { id: 'male' as const, label: '男声', icon: '🎵' },
  { id: 'other' as const, label: '其他语言', icon: '🌍' },
  { id: 'cloned' as const, label: '我的声音', icon: '⭐' },
]

const activeTab = ref<'female' | 'male' | 'other' | 'cloned'>('female')
const voices = ref<Voice[]>([])
const selectedVoiceId = ref<string | null>(null)

async function loadVoices() {
  const res = await apiService.voices.getList()
  voices.value = res.data
  const selected = voices.value.find((v) => v.isSelected)
  if (selected) selectedVoiceId.value = selected.id
}

const filteredVoices = computed(() => {
  if (activeTab.value === 'female') return voices.value.filter((v) => v.category === 'female')
  if (activeTab.value === 'male') return voices.value.filter((v) => v.category === 'male')
  if (activeTab.value === 'other') return voices.value.filter((v) => ['english', 'japanese', 'korean'].includes(v.category))
  return voices.value.filter((v) => v.category === 'cloned')
})

function selectVoice(voice: Voice) {
  selectedVoiceId.value = voice.id
  voices.value.forEach((v) => (v.isSelected = v.id === voice.id))
  ui.showToast('✅ 已选择音色')
}

function openClone() {
  ui.openModal('modal-clone-voice')
}

onMounted(() => {
  loadVoices()
})
</script>

<template>
  <div class="animate-[fadeIn_.25s_ease]">
    <div
      class="mb-5 bg-gradient-to-br from-[var(--indigo)] to-[var(--teal)] rounded-[var(--radius-lg)] p-[22px] flex items-center gap-4 cursor-pointer shadow-[0_6px_24px_rgba(92,107,192,.25)] transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_10px_32px_rgba(92,107,192,.35)]"
      @click="openClone"
    >
      <div class="w-[52px] h-[52px] rounded-2xl bg-white/20 flex items-center justify-center text-[26px] shrink-0">🎤</div>
      <div class="flex-1">
        <div class="text-[17px] font-black text-white mb-1">克隆我的声音</div>
        <div class="text-[13px] text-white/80">只需 30 秒录音，让 AI 伙伴用你的声音与孩子对话</div>
      </div>
      <div class="bg-white text-[var(--indigo)] px-5 py-2.5 rounded-[10px] text-[13px] font-extrabold whitespace-nowrap shrink-0">
        立即克隆 →
      </div>
    </div>

    <Tabs
      v-model="activeTab"
      :tabs="voiceTabs"
      class="mb-4"
    />

    <div v-if="filteredVoices.length > 0" class="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-3">
      <div
        v-for="voice in filteredVoices"
        :key="voice.id"
        :class="[
          'bg-[var(--surface)] rounded-[var(--radius-md)] p-[14px] flex items-center gap-3 border-[1.5px] cursor-pointer transition-all duration-200 shadow-[var(--shadow-sm)]',
          selectedVoiceId === voice.id
            ? 'border-[var(--teal)] shadow-[0_4px_16px_rgba(0,201,167,.15)]'
            : 'border-[var(--border)] hover:border-[var(--teal-lt)] hover:-translate-y-px',
        ]"
        @click="selectVoice(voice)"
      >
        <div
          class="w-11 h-11 rounded-[13px] flex items-center justify-center text-base font-black text-white shrink-0"
          :style="{ background: voice.gradient }"
        >
          {{ voice.character }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-bold text-[var(--text1)]">{{ voice.name }}</div>
          <div class="text-xs text-[var(--text3)] mt-0.5">{{ voice.description }}</div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <button
            class="w-8 h-8 rounded-full bg-[var(--bg2)] border-none flex items-center justify-center text-[11px] text-[var(--text2)] cursor-pointer transition-all duration-200 hover:bg-[var(--teal)] hover:text-white"
            @click.stop="ui.showToast('▶ 试听中…')"
          >
            ▶
          </button>
          <div
            v-if="selectedVoiceId === voice.id"
            class="w-[22px] h-[22px] rounded-full bg-[var(--teal)] text-white flex items-center justify-center text-xs font-black"
          >
            ✓
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="activeTab === 'cloned' && filteredVoices.length === 0"
      class="max-w-[400px] min-h-[140px] bg-[var(--surface)] rounded-[var(--radius-lg)] border-2 border-dashed border-[var(--border)] flex flex-col items-center justify-center gap-2.5 py-10 px-5 cursor-pointer transition-all duration-200 hover:bg-[var(--bg)] hover:border-[var(--coral-lt)] group"
      @click="openClone"
    >
      <div class="w-12 h-12 rounded-2xl bg-[var(--bg2)] text-[var(--text3)] flex items-center justify-center text-[22px] transition-all duration-200 group-hover:bg-[rgba(255,107,107,.12)] group-hover:text-[var(--coral)]">
        🎤
      </div>
      <div class="text-sm font-bold text-[var(--text3)] transition-colors duration-200 group-hover:text-[var(--coral)]">克隆你的声音</div>
      <div class="text-xs text-[var(--text3)]">点击开始 30 秒录音</div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
