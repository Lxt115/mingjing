<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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

// 检测是否支持录音（需要 HTTPS）
const canRecord = computed(() => !!navigator.mediaDevices?.getUserMedia)

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
const audioFile = ref<File | null>(null)
const promptText = '春天来了，花儿都开放了。小鸟在枝头欢快地歌唱，蜜蜂也飞来飞去忙着采蜜。'

function toggleRecord() {
  if (!isRecording.value) {
    startRecording()
  } else {
    lastTimer.value = recordTimer.value
    stopRecording()
  }
}

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

  let blob: Blob | null = null

  if (canRecord.value) {
    if (!recordDone.value) {
      ui.showToast('❌ 请先录制语音样本', 'error')
      return
    }
    blob = audioBlob.value
  } else {
    if (!audioFile.value) {
      ui.showToast('❌ 请选择音频文件', 'error')
      return
    }
    blob = audioFile.value
  }

  if (!blob) {
    ui.showToast('❌ 音频数据无效', 'error')
    return
  }

  saving.value = true
  try {
    await apiService.voiceprint.register(speakerName.value.trim(), desc.value.trim(), blob)
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
    <InfoTip v-if="canRecord"> 💡 请朗读下方文本，录制5秒以上的清晰语音 </InfoTip>
    <InfoTip v-else>
      💡 请选择5秒以上的清晰音频文件（由于页面通过HTTP访问，浏览器不支持直接录音，请改用文件上传）
    </InfoTip>

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
        >声纹样本 *</label
      >

      <!-- 录音模式（HTTPS） -->
      <template v-if="canRecord">
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
      </template>

      <!-- 文件上传模式（HTTP 兜底） -->
      <template v-else>
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
      </template>
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
        :class="saving ? 'opacity-60 pointer-events-none' : ''"
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
