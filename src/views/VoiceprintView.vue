<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { VoiceprintSpeaker } from '@/types'
import { apiService } from '@/services'
import { useUiStore } from '@/store'
import { InfoTip } from '@/components/ui'

const ui = useUiStore()
const speakers = ref<VoiceprintSpeaker[]>([])
const loading = ref(false)

async function loadSpeakers() {
  loading.value = true
  try {
    const res = await apiService.voiceprint.getList()
    speakers.value = res.data
  } finally {
    loading.value = false
  }
}

async function deleteSpeaker(speaker: VoiceprintSpeaker) {
  try {
    await apiService.voiceprint.delete(speaker.id)
    speakers.value = speakers.value.filter((s) => s.id !== speaker.id)
    ui.showToast('已删除')
  } catch {
    ui.showToast('❌ 删除失败', 'error')
  }
}

onMounted(() => {
  loadSpeakers()
})
</script>

<template>
  <div class="animate-[fadeIn_.25s_ease] max-w-[640px]">
    <InfoTip class="mb-5">
      💡 声纹用于识别不同说话人，建议上传 2 秒以上的清晰语音以获得更好效果
    </InfoTip>

    <div class="text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase mb-3">已注册说话人</div>

    <div v-if="loading" class="text-center py-8 text-[var(--text3)] text-sm font-semibold">加载中…</div>

    <div
      v-for="speaker in speakers"
      :key="speaker.id"
      class="bg-[var(--surface)] rounded-[var(--radius-md)] border-[1.5px] border-[var(--border)] p-[14px] flex items-center gap-3 mb-2.5 shadow-[var(--shadow-sm)] transition-all duration-200 hover:shadow-[var(--shadow-md)]"
    >
      <div class="w-10 h-10 rounded-xl bg-[var(--bg2)] flex items-center justify-center text-xl shrink-0">
        👤
      </div>
      <div class="flex-1">
        <div class="text-sm font-extrabold text-[var(--text1)]">{{ speaker.name }}</div>
        <div class="text-xs text-[var(--text3)] mt-0.5">注册于 {{ speaker.registeredAt }} · {{ speaker.sampleCount }} 条样本</div>
      </div>
      <div class="flex gap-2">
        <button
          class="w-8 h-8 rounded-lg bg-[#eef0fc] text-[var(--indigo)] border-none flex items-center justify-center text-sm cursor-pointer transition-all duration-200 hover:bg-[var(--indigo)] hover:text-white"
          @click="ui.showToast('编辑功能开发中…')"
        >
          ✏️
        </button>
        <button
          class="w-8 h-8 rounded-lg bg-[#fff0f0] text-[var(--coral)] border-none flex items-center justify-center text-sm cursor-pointer transition-all duration-200 hover:bg-[var(--coral)] hover:text-white"
          @click="deleteSpeaker(speaker)"
        >
          🗑️
        </button>
      </div>
    </div>

    <button
      class="max-w-[280px] mt-2 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] py-3 px-5 text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)] w-full block"
      @click="ui.openModal('modal-add-speaker')"
    >
      ＋ 添加说话人
    </button>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
