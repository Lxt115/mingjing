<script setup lang="ts">
import { ref } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'

const { close } = useModal()
const ui = useUiStore()

const speakerName = ref('')
const voiceSampleId = ref('')
const desc = ref('')
const saving = ref(false)

const sampleOptions = [
  { id: '1', label: '语音消息 2026-04-05 14:32 (3.2s)' },
  { id: '2', label: '语音消息 2026-04-05 10:15 (4.1s)' },
  { id: '3', label: '语音消息 2026-04-04 20:03 (2.8s)' },
]

async function confirmAdd() {
  if (!voiceSampleId.value) {
    ui.showToast('❌ 请选择声纹样本', 'error')
    return
  }
  if (!speakerName.value.trim()) {
    ui.showToast('❌ 请输入说话人名称', 'error')
    return
  }
  saving.value = true
  try {
    await apiService.voiceprint.register(speakerName.value.trim())
    close()
    ui.showToast(`✅ 「${speakerName.value.trim()}」声纹已注册！`)
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 注册失败', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div>
    <InfoTip>💡 请选择2秒以上的清晰语音，避免背景噪音</InfoTip>

    <div class="mb-[18px]">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
        >说话人名称 *</label
      >
      <input
        v-model="speakerName"
        class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
        placeholder="例如：小明、妈妈"
      />
    </div>

    <div class="flex gap-3 mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] border-none text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white"
        :disabled="saving"
        @click="confirmAdd"
      >
        {{ saving ? '添加中…' : '确认添加' }}
      </button>
    </div>
  </div>
</template>
