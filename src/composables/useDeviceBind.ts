import { ref } from 'vue'

import { useDevicesStore, useUiStore } from '@/store'

export function useDeviceBind() {
  const devicesStore = useDevicesStore()
  const ui = useUiStore()
  const deviceCode = ref('')
  const isSubmitting = ref(false)

  async function submitBind(agentId?: string) {
    const code = deviceCode.value.trim()
    if (code.length !== 4) {
      ui.showToast('❌ 请输入 4 位配对码', 'error')
      return false
    }
    isSubmitting.value = true
    try {
      await devicesStore.bindDevice(code, agentId)
      ui.closeModal()
      ui.showToast('✅ 设备绑定成功！')
      deviceCode.value = ''
      return true
    } catch (e) {
      ui.showToast(e instanceof Error ? e.message : '❌ 设备绑定失败', 'error')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    deviceCode,
    isSubmitting,
    submitBind,
  }
}
