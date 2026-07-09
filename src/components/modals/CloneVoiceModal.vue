<script setup lang="ts">
import { ref, computed } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { apiService } from '@/services'
import { InfoTip } from '@/components/ui'
import { useVoiceRecord } from '@/composables'

const { close } = useModal()
const ui = useUiStore()
const {
  currentStep,
  isRecording,
  recordDone,
  recordSecs,
  recordTimer,
  loadPercent,
  loadStatus,
  startRecording,
  stopRecording,
  resetRecording,
  simulateGeneration,
} = useVoiceRecord()

const lastTimer = ref('00:00')

function stepClass(step: number): string {
  if (currentStep.value > step) return 'done'
  if (currentStep.value === step) return 'active'
  return ''
}

function goNext() {
  if (currentStep.value === 1) {
    currentStep.value = 2
  } else if (currentStep.value === 2) {
    verifyAndProceed()
  }
}

function toggleRecord() {
  if (!isRecording.value) {
    startRecording()
  } else {
    lastTimer.value = recordTimer.value
    stopRecording()
  }
}

function verifyAndProceed() {
  if (!recordDone.value) {
    ui.showToast('❌ 请先完成录音', 'error')
    return
  }
  const ok = Math.random() > 0.2
  if (!ok) {
    ui.showToast('❌ 校验失败，请按照文本朗读', 'error')
    return
  }
  currentStep.value = 3
  simulateGeneration(async () => {
    try {
      await apiService.voices.cloneVoice(new Blob())
      close()
      ui.showToast('🎉 你的声音音色已生成！')
    } catch {
      ui.showToast('❌ 生成失败', 'error')
    }
  })
}

resetRecording()
</script>

<template>
  <div>
    <div class="flex items-center justify-center gap-0 pt-5 pb-6">
      <div :class="['flex flex-col items-center gap-1.5', stepClass(1)]">
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-black transition-all duration-300',
            stepClass(1) === 'active'
              ? 'bg-[var(--coral)] text-white shadow-[0_2px_10px_rgba(255,107,107,.4)]'
              : stepClass(1) === 'done'
                ? 'bg-[var(--teal)] text-white'
                : 'bg-[var(--bg2)] text-[var(--text3)]',
          ]"
        >
          1
        </div>
        <div
          :class="[
            'text-[11px] font-bold',
            stepClass(1) === 'active'
              ? 'text-[var(--coral)]'
              : stepClass(1) === 'done'
                ? 'text-[var(--teal)]'
                : 'text-[var(--text3)]',
          ]"
        >
          阅读须知
        </div>
      </div>
      <div class="w-12 h-0.5 bg-[var(--border)] mb-4 shrink-0"></div>
      <div :class="['flex flex-col items-center gap-1.5', stepClass(2)]">
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-black transition-all duration-300',
            stepClass(2) === 'active'
              ? 'bg-[var(--coral)] text-white shadow-[0_2px_10px_rgba(255,107,107,.4)]'
              : stepClass(2) === 'done'
                ? 'bg-[var(--teal)] text-white'
                : 'bg-[var(--bg2)] text-[var(--text3)]',
          ]"
        >
          2
        </div>
        <div
          :class="[
            'text-[11px] font-bold',
            stepClass(2) === 'active'
              ? 'text-[var(--coral)]'
              : stepClass(2) === 'done'
                ? 'text-[var(--teal)]'
                : 'text-[var(--text3)]',
          ]"
        >
          录制声音
        </div>
      </div>
      <div class="w-12 h-0.5 bg-[var(--border)] mb-4 shrink-0"></div>
      <div :class="['flex flex-col items-center gap-1.5', stepClass(3)]">
        <div
          :class="[
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-black transition-all duration-300',
            stepClass(3) === 'active'
              ? 'bg-[var(--coral)] text-white shadow-[0_2px_10px_rgba(255,107,107,.4)]'
              : 'bg-[var(--bg2)] text-[var(--text3)]',
          ]"
        >
          3
        </div>
        <div
          :class="[
            'text-[11px] font-bold',
            stepClass(3) === 'active' ? 'text-[var(--coral)]' : 'text-[var(--text3)]',
          ]"
        >
          生成音色
        </div>
      </div>
    </div>

    <div v-show="currentStep === 1">
      <div
        class="bg-[var(--bg)] rounded-[var(--radius-md)] p-[18px] mb-3.5 border border-[var(--border)]"
      >
        <div class="text-sm font-extrabold text-[var(--text1)] mb-2.5">📋 录制须知</div>
        <div class="text-[13px] text-[var(--text2)] font-semibold leading-relaxed py-1">
          🔇 请在安静的环境中录制，避免背景噪音
        </div>
        <div class="text-[13px] text-[var(--text2)] font-semibold leading-relaxed py-1">
          🎙️ 距麦克风约 15–20 厘米
        </div>
        <div class="text-[13px] text-[var(--text2)] font-semibold leading-relaxed py-1">
          ⏱️ 朗读文本约需 30 秒，语速自然即可
        </div>
        <div class="text-[13px] text-[var(--text2)] font-semibold leading-relaxed py-1">
          ✅ 克隆结果仅用于本设备 AI 伙伴发声
        </div>
        <div class="text-[13px] text-[var(--text2)] font-semibold leading-relaxed py-1">
          🔒 录音数据加密存储，不会对外共享
        </div>
      </div>
      <InfoTip>💡 建议在安静空间录制，效果更佳</InfoTip>
    </div>

    <div v-show="currentStep === 2">
      <div
        :class="[
          'bg-[var(--bg)] rounded-[var(--radius-sm)] p-4 mb-3.5 text-sm leading-relaxed text-[var(--text2)] font-medium border-2 transition-colors',
          recordDone ? 'border-[var(--teal)] bg-[rgba(0,201,167,.05)]' : 'border-[var(--border)]',
        ]"
      >
        春天来了，花儿都开放了。小鸟在枝头欢快地歌唱，蜜蜂也飞来飞去忙着采蜜。阳光照在身上暖洋洋的，小朋友们在公园里玩耍，笑声传遍了整个公园。
      </div>

      <div
        v-if="recordDone"
        class="py-2.5 px-3.5 rounded-[var(--radius-sm)] text-xs font-bold mb-3 bg-[#fff8e6] text-[var(--amber)] border border-[rgba(255,184,48,.2)]"
      >
        ⚠️ 请朗读完整段文本后再点击完成
      </div>

      <div class="text-center pt-6 pb-4">
        <button
          :class="[
            'w-20 h-20 rounded-full border-none text-[28px] cursor-pointer flex items-center justify-center mx-auto mb-3 shadow-[0_4px_20px_rgba(255,107,107,.4)] transition-all duration-200 hover:scale-105 relative',
            isRecording
              ? 'bg-gradient-to-br from-[#ff4d4d] to-[var(--coral)] animate-[recordPulse_1.5s_infinite]'
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
              ? '正在录音，请自然朗读…'
              : recordDone
                ? '录制完成！可重新录制或继续'
                : '点击开始录音'
          }}
        </div>
        <div v-if="recordDone" class="text-xs text-[var(--text3)] mt-1">
          录制完成 · {{ lastTimer }}
        </div>
      </div>
    </div>

    <div v-show="currentStep === 3">
      <div class="text-center py-5">
        <div class="text-base font-black text-[var(--text1)] mb-2">
          {{ loadPercent >= 100 ? '✅ 生成成功！' : '🔄 正在生成音色…' }}
        </div>
        <div class="mt-5">
          <div class="h-2 bg-[var(--bg2)] rounded overflow-hidden mb-2.5">
            <div
              class="h-full rounded bg-gradient-to-r from-[var(--teal)] to-[var(--indigo)] transition-all duration-700"
              :style="{ width: loadPercent + '%' }"
            ></div>
          </div>
          <div class="text-[13px] text-[var(--text2)] font-semibold text-center">
            {{ loadStatus || '准备中…' }}
          </div>
        </div>
      </div>
    </div>

    <div v-if="currentStep < 3" class="flex gap-3 w-full mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] border-none text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white"
        :class="currentStep === 2 && !recordDone ? 'opacity-40 pointer-events-none' : ''"
        @click="goNext"
      >
        {{ currentStep === 1 ? '我已了解，开始录音 →' : '校验并继续 →' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
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
