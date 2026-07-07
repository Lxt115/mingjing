<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'
import type { VoiceprintSpeaker } from '@/types'

const ui = useUiStore()
const { isMobile } = useMediaQuery()
const speakers = ref<VoiceprintSpeaker[]>([])

function removeSpeaker(speaker: VoiceprintSpeaker) {
  ui.showToast(`🗑️ 已移除说话人：${speaker.name}`)
}

function addSpeaker() {
  ui.openModal('modal-add-speaker')
}

onMounted(async () => {
  const res = await apiService.voiceprint.getList()
  speakers.value = res.data
})
</script>

<template>
  <!-- Desktop Layout -->
  <div v-if="!isMobile" class="animate-[fadeIn_.25s_ease]">
    <InfoTip> 通过声纹识别区分不同说话人，实现多用户安全访问 </InfoTip>

    <div class="grid grid-cols-3 gap-3 mt-4">
      <div
        v-for="speaker in speakers"
        :key="speaker.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] p-4 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[var(--shadow-md)]"
      >
        <div class="flex items-center gap-3 mb-3">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-lg shrink-0"
            :style="{ background: speaker.gradient }"
          >
            {{ speaker.emoji }}
          </div>
          <div>
            <div class="text-sm font-extrabold text-[var(--text1)]">{{ speaker.name }}</div>
            <div class="text-[10px] text-[var(--teal)] font-bold">
              {{ speaker.verified ? '✅ 已认证' : '⏳ 待认证' }}
            </div>
          </div>
        </div>
        <div class="text-[11px] text-[var(--text3)] leading-relaxed mb-3">
          {{ speaker.description }}
        </div>
        <button
          class="w-full h-8 rounded-lg bg-transparent text-[var(--coral)] border border-[var(--coral)]/30 text-xs font-extrabold cursor-pointer transition-all duration-200 hover:bg-[rgba(255,107,107,.05)]"
          @click="removeSpeaker(speaker)"
        >
          🗑️ 移除
        </button>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div class="px-2 py-3">
      <div
        class="bg-[#f0f4ff] text-[var(--indigo)] text-xs px-3.5 py-2.5 rounded-[12px] font-bold leading-[1.6]"
      >
        💡 通过声纹识别区分不同说话人，实现多用户安全访问
      </div>
    </div>

    <div class="flex items-center justify-between px-2 pt-2 pb-3">
      <div>
        <div class="text-[13px] font-extrabold text-[var(--text1)]">说话人列表</div>
        <div class="text-[11px] text-[var(--text3)] mt-px font-bold">{{ speakers.length }} 人</div>
      </div>
      <button
        class="py-2 px-3 rounded-[20px] bg-[rgba(255,107,107,.12)] text-[var(--coral)] text-[11px] font-extrabold border-none cursor-pointer transition-all duration-200 active:scale-[.95]"
        @click="addSpeaker"
      >
        ＋ 添加
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-for="speaker in speakers"
        :key="speaker.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] p-4 mb-2.5 shadow-[var(--shadow-sm)] flex items-center justify-between transition-all duration-200 active:scale-[.98]"
      >
        <div class="flex items-center gap-2.5 flex-1 min-w-0">
          <div
            class="w-11 h-11 rounded-[14px] flex items-center justify-center text-xl shrink-0"
            :style="{ background: speaker.gradient }"
          >
            {{ speaker.emoji }}
          </div>
          <div>
            <div class="flex items-center gap-1.5 mb-[3px]">
              <span class="text-sm font-extrabold text-[var(--text1)]">{{ speaker.name }}</span>
              <span
                class="text-[10px] text-[var(--teal)] font-extrabold px-1.5 py-0.5 rounded-[20px]"
                :class="speaker.verified ? 'bg-[#e8fdf5]' : 'bg-[var(--bg2)]'"
              >
                {{ speaker.verified ? '✅ 已认证' : '待认证' }}
              </span>
            </div>
            <div class="text-[11px] text-[var(--text3)]">{{ speaker.description }}</div>
          </div>
        </div>
        <button
          class="py-1.5 px-3 rounded-[20px] bg-[rgba(255,107,107,.1)] text-[var(--coral)] text-[11px] font-extrabold border-none cursor-pointer shrink-0 transition-all duration-200 active:scale-[.9]"
          @click="removeSpeaker(speaker)"
        >
          移除
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
