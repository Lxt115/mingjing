import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useUiStore } from '@/store'
import type { ModalId } from '@/types'

export function useModal() {
  const ui = useUiStore()
  const escHandler = ref<((e: KeyboardEvent) => void) | null>(null)

  const activeModal = computed(() => ui.activeModalId)
  const modalData = computed(() => ui.modalData)
  const isOpen = computed(() => ui.isModalOpen)

  function open(id: ModalId, data: Record<string, unknown> = {}) {
    ui.openModal(id, data)
    ensureEscBinding()
  }

  function close() {
    ui.closeModal()
    removeEscBinding()
  }

  function isActive(id: ModalId): boolean {
    return ui.activeModalId === id
  }

  function ensureEscBinding() {
    if (escHandler.value) return
    escHandler.value = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
    }
    document.addEventListener('keydown', escHandler.value)
  }

  function removeEscBinding() {
    if (escHandler.value) {
      document.removeEventListener('keydown', escHandler.value)
      escHandler.value = null
    }
  }

  watch(isOpen, (val) => {
    if (val) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
      removeEscBinding()
    }
  })

  onBeforeUnmount(() => {
    removeEscBinding()
    document.body.style.overflow = ''
  })

  return {
    activeModal,
    modalData,
    isOpen,
    open,
    close,
    isActive,
  }
}
