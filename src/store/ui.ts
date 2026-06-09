import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ModalId } from '@/types'

export interface ToastMessage {
  id: number
  text: string
  type: 'success' | 'error' | 'info' | 'warning'
}

let toastSeq = 0

export const useUiStore = defineStore('ui', () => {
  const toasts = ref<ToastMessage[]>([])
  const activeModalId = ref<ModalId>(null)
  const modalData = ref<Record<string, unknown>>({})
  const sidebarCollapsed = ref(false)
  const memoryTipVisible = ref(true)
  const kbRefreshCounter = ref(0)

  const isModalOpen = computed(() => activeModalId.value !== null)

  function showToast(
    text: string,
    type: ToastMessage['type'] = 'success',
    duration = 2500,
  ) {
    const id = ++toastSeq
    toasts.value.push({ id, text, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
  }

  function openModal(id: ModalId, data: Record<string, unknown> = {}) {
    activeModalId.value = id
    modalData.value = data
  }

  function closeModal() {
    activeModalId.value = null
    modalData.value = {}
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setMemoryTip(visible: boolean) {
    memoryTipVisible.value = visible
  }

  function triggerKbRefresh() {
    kbRefreshCounter.value++
  }

  return {
    toasts,
    activeModalId,
    modalData,
    sidebarCollapsed,
    memoryTipVisible,
    kbRefreshCounter,
    isModalOpen,
    showToast,
    openModal,
    closeModal,
    toggleSidebar,
    setMemoryTip,
    triggerKbRefresh,
  }
})
