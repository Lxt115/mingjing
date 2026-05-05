import { ref, onBeforeUnmount } from 'vue'
import type { CloneStep, StepStatus } from '@/types'

export function useVoiceRecord() {
  const isRecording = ref(false)
  const recordDone = ref(false)
  const recordSecs = ref(0)
  const recordTimer = ref('00:00')
  const currentStep = ref<CloneStep>(1)
  const isLoading = ref(false)
  const loadStatus = ref('')
  const loadPercent = ref(0)

  let recordInterval: ReturnType<typeof setInterval> | null = null

  const stepStatuses = (): Record<CloneStep, StepStatus> => ({
    1: currentStep.value === 1 ? 'active' : currentStep.value > 1 ? 'done' : 'pending',
    2: currentStep.value === 2 ? 'active' : currentStep.value > 2 ? 'done' : 'pending',
    3: currentStep.value === 3 ? 'active' : 'pending',
  })

  function formatTimer(secs: number): string {
    const m = String(Math.floor(secs / 60)).padStart(2, '0')
    const s = String(secs % 60).padStart(2, '0')
    return `${m}:${s}`
  }

  function startRecording() {
    isRecording.value = true
    recordSecs.value = 0
    recordTimer.value = '00:00'
    recordDone.value = false

    recordInterval = setInterval(() => {
      recordSecs.value++
      recordTimer.value = formatTimer(recordSecs.value)
      if (recordSecs.value >= 30) stopRecording()
    }, 1000)
  }

  function stopRecording() {
    if (recordInterval) {
      clearInterval(recordInterval)
      recordInterval = null
    }
    isRecording.value = false
    recordDone.value = true
  }

  function resetRecording() {
    stopRecording()
    recordSecs.value = 0
    recordTimer.value = '00:00'
    recordDone.value = false
    currentStep.value = 1
    isLoading.value = false
    loadPercent.value = 0
    loadStatus.value = ''
  }

  function goToStep(step: CloneStep) {
    currentStep.value = step
  }

  function nextStep() {
    if (currentStep.value < 3) {
      currentStep.value = (currentStep.value + 1) as CloneStep
    }
  }

  function simulateGeneration(onComplete: () => void) {
    isLoading.value = true
    const stages: [number, string][] = [
      [20, '正在分析声纹特征…'],
      [45, '提取音色模型中…'],
      [70, '生成个性化音色…'],
      [90, '优化音质细节…'],
      [100, '音色生成完成！'],
    ]

    let si = 0
    const iv = setInterval(() => {
      if (si < stages.length) {
        loadPercent.value = stages[si][0]
        loadStatus.value = stages[si][1]
        si++
      }
      if (loadPercent.value >= 100) {
        clearInterval(iv)
        setTimeout(onComplete, 800)
      }
    }, 700)
  }

  onBeforeUnmount(() => {
    stopRecording()
  })

  return {
    isRecording,
    recordDone,
    recordSecs,
    recordTimer,
    currentStep,
    isLoading,
    loadStatus,
    loadPercent,
    stepStatuses,
    startRecording,
    stopRecording,
    resetRecording,
    goToStep,
    nextStep,
    simulateGeneration,
  }
}
