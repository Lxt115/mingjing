import { describe, it, expect } from 'vitest'
import { useUiStore } from '@/store/ui'
import { createPinia, setActivePinia } from 'pinia'

describe('uiStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should open and close modal', () => {
    const ui = useUiStore()
    expect(ui.isModalOpen).toBe(false)

    ui.openModal('modal-agent-config', { mode: 'create' })
    expect(ui.isModalOpen).toBe(true)
    expect(ui.activeModalId).toBe('modal-agent-config')

    ui.closeModal()
    expect(ui.isModalOpen).toBe(false)
    expect(ui.activeModalId).toBeNull()
  })

  it('should show and auto-dismiss toast', () => {
    const ui = useUiStore()

    ui.showToast('test message', 'success', 50)
    expect(ui.toasts.length).toBe(1)
    expect(ui.toasts[0].text).toBe('test message')
    expect(ui.toasts[0].type).toBe('success')
  })

  it('should toggle sidebar', () => {
    const ui = useUiStore()
    expect(ui.sidebarCollapsed).toBe(false)

    ui.toggleSidebar()
    expect(ui.sidebarCollapsed).toBe(true)

    ui.toggleSidebar()
    expect(ui.sidebarCollapsed).toBe(false)
  })
})
