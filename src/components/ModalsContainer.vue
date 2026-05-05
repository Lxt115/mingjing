<script setup lang="ts">
import { computed } from 'vue'
import { useModal } from '@/composables'
import { useUiStore } from '@/store'
import { Modal } from '@/components/ui'
import {
  AgentConfigModal,
  AddDeviceModal,
  UnbindConfirmModal,
  CloneVoiceModal,
  AddSpeakerModal,
  KbNewModal,
  AgentDeviceModal,
} from '@/components/modals'

const { close, isActive } = useModal()

const modalTitle = computed(() => {
  if (isActive('modal-agent-config')) {
    const isCreate = !useUiStore().modalData.agentId
    return isCreate ? '＋ 新建角色' : '⚙️ 配置角色'
  }
  if (isActive('modal-add-device')) return '📱 添加新设备'
  if (isActive('modal-unbind-confirm')) return '⚠️ 确认解绑'
  if (isActive('modal-clone-voice')) return '🎤 克隆我的声音'
  if (isActive('modal-add-speaker')) return '🎙️ 添加说话人'
  if (isActive('modal-kb-new')) return '📄 上传文件'
  if (isActive('modal-agent-device')) {
    const name = useUiStore().modalData.agentName as string ?? '角色'
    return `📱 ${name} · 管理设备`
  }
  return ''
})
</script>

<template>
  <Modal
    :open="isActive('modal-agent-config')"
    :title="modalTitle"
    :size="'large'"
    @close="close"
  >
    <AgentConfigModal />
  </Modal>

  <Modal
    :open="isActive('modal-add-device')"
    :title="modalTitle"
    @close="close"
  >
    <AddDeviceModal />
  </Modal>

  <Modal
    :open="isActive('modal-unbind-confirm')"
    :title="modalTitle"
    @close="close"
  >
    <UnbindConfirmModal />
  </Modal>

  <Modal
    :open="isActive('modal-clone-voice')"
    :title="modalTitle"
    :size="'large'"
    @close="close"
  >
    <CloneVoiceModal />
  </Modal>

  <Modal
    :open="isActive('modal-add-speaker')"
    :title="modalTitle"
    @close="close"
  >
    <AddSpeakerModal />
  </Modal>

  <Modal
    :open="isActive('modal-kb-new')"
    :title="modalTitle"
    @close="close"
  >
    <KbNewModal />
  </Modal>

  <Modal
    :open="isActive('modal-agent-device')"
    :title="modalTitle"
    :size="'large'"
    @close="close"
  >
    <AgentDeviceModal />
  </Modal>
</template>
