<script setup lang="ts">
import { ref } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'

const { close } = useModal()
const ui = useUiStore()

const speakerName = ref('')
const desc = ref('')
const audioFile = ref<File | null>(null)
const saving = ref(false)

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    audioFile.value = input.files[0]
  }
}

async function confirmAdd() {
  if (!speakerName.value.trim()) {
    ui.showToast('❌ 请输入说话人名称', 'error')
    return
  }
  if (!audioFile.value) {
    ui.showToast('❌ 请选择声纹样本音频文件', 'error')
    return
  }
  saving.value = true
  try {
    await apiService.voiceprint.register(
      speakerName.value.trim(),
      desc.value.trim(),
      audioFile.value,
    )
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
    <InfoTip>💡 请选择5秒以上的清晰语音（WAV 格式），避免背景噪音</InfoTip>

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

    <div class="mb-[18px]">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
        >说话人描述</label
      >
      <input
        v-model="desc"
        class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
        placeholder="例如：我的好朋友"
      />
    </div>

    <div class="mb-[18px]">
      <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
        >声纹样本音频 *</label
      >
      <label
        class="flex items-center justify-center w-full p-4 border-[1.5px] border-dashed border-[var(--border)] rounded-[var(--radius-sm)] cursor-pointer transition-all duration-200 hover:border-[var(--coral)] hover:bg-[rgba(255,107,107,.03)]"
      >
        <input
          type="file"
          accept=".wav,.mp3,.ogg,.m4a,audio/*"
          class="hidden"
          @change="onFileChange"
        />
        <div class="text-center">
          <div class="text-2xl mb-1">{{ audioFile ? '✅' : '📁' }}</div>
          <div class="text-sm font-bold text-[var(--text2)]">
            {{ audioFile ? audioFile.name : '点击选择音频文件' }}
          </div>
          <div v-if="audioFile" class="text-[11px] text-[var(--text3)] mt-1">
            {{ (audioFile.size / 1024).toFixed(1) }} KB
          </div>
        </div>
      </label>
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
