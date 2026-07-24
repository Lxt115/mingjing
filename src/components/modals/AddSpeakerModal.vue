<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'
import { useVoiceRecord } from '@/composables'

const { close } = useModal()
const ui = useUiStore()

const speakerName = ref('')
const desc = ref('')
const saving = ref(false)

const {
  isRecording,
  recordDone,
  recordTimer,
  audioBlob,
  startRecording,
  stopRecording,
  resetRecording,
} = useVoiceRecord()

const lastTimer = ref('00:00')
const promptText = '春天来了，花儿都开放了。小鸟在枝头欢快地歌唱，蜜蜂也飞来飞去忙着采蜜。'

function toggleRecord() {
  if (!isRecording.value) {
    startRecording()
  } else {
    lastTimer.value = recordTimer.value
    stopRecording()
  }
}

async function confirmAdd() {
  if (!speakerName.value.trim()) {
    ui.showToast('❌ 请输入说话人名称', 'error')
    return
  }
  if (!recordDone.value) {
    ui.showToast('❌ 请先录制语音样本', 'error')
    return
  }
  if (!audioBlob.value) {
    ui.showToast('❌ 录音数据无效，请重新录制', 'error')
    return
  }
  saving.value = true
  try {
    await apiService.voiceprint.register(
      speakerName.value.trim(),
      desc.value.trim(),
      audioBlob.value,
    )
    close()
    ui.showToast(`✅ 「${speakerName.value.trim()}」声纹已注册！`)
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 注册失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  resetRecording()
})
</script>

<template>
  <div>
    <InfoTip>💡 请朗读下方文本，录制5秒以上的清晰语音</InfoTip>

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
        >声纹样本录音 *</label
      >

      <div
        :class="[
          'bg-[var(--bg)] rounded-[var(--radius-sm)] p-4 mb-3.5 text-sm leading-relaxed text-[var(--text2)] font-medium border-2 transition-colors',
          recordDone ? 'border-[var(--teal)] bg-[rgba(0,201,167,.05)]' : 'border-[var(--border)]',
        ]"
      >
        {{ promptText }}
      </div>

      <div class="text-center py-4">
        <button
          :class="[
            'w-20 h-20 rounded-full border-none text-[28px] cursor-pointer flex items-center justify-center mx-auto mb-3 shadow-[0_4px_20px_rgba(255,107,107,.4)] transition-all duration-200 hover:scale-105 relative',
            isRecording
              ? 'bg-gradient-to-br from-[#ff4d4d] to-[var(--coral)] record-pulse'
              : 'bg-gradient-to-br from-[var(--coral)] to-[#FF8E53]',
          ]"
          @click="toggleRecord"
        >
          {{ isRecording ? '⏹' : recordDone ? '✅' : '🎙️' }}
        </button>
        <div class="text-[22px] font-black text-[var(--text1)] mb-1.5">{{ recordTimer }}</div>
        <div class="text-[13px] text-[var(--text2)] font-semibold">
          {{
            isRecording
              ? '正在录音，请朗读文本…'
              : recordDone
                ? '录音完成！可重新录制或确认添加'
                : '点击开始录音'
          }}
        </div>
        <div v-if="recordDone" class="text-xs text-[var(--text3)] mt-1">
          录制完成 · {{ lastTimer }}
        </div>
      </div>
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
        :class="!recordDone ? 'opacity-40 pointer-events-none' : ''"
        :disabled="saving"
        @click="confirmAdd"
      >
        {{ saving ? '添加中…' : '确认添加' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.record-pulse {
  animation: recordPulse 1.5s infinite;
}

@keyframes recordPulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.4);
  }
  50% {
    box-shadow: 0 0 0 16px rgba(255, 107, 107, 0);
  }
}
</style>
