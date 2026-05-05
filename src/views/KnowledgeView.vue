<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { KnowledgeBase } from '@/types'
import { apiService } from '@/services'
import { useUiStore } from '@/store'
import { Switch, InfoTip } from '@/components/ui'

const ui = useUiStore()
const knowledgeBases = ref<KnowledgeBase[]>([])
const memoryEnabled = ref(true)
const loading = ref(false)

async function loadKnowledge() {
  loading.value = true
  try {
    const res = await apiService.knowledge.getList()
    knowledgeBases.value = res.data
  } finally {
    loading.value = false
  }
}

async function toggleKnowledge(kb: KnowledgeBase) {
  const next = !kb.isEnabled
  try {
    await apiService.knowledge.toggleKnowledge(kb.id, next)
    kb.isEnabled = next
    kb.status = next ? 'enabled' : 'disabled'
  } catch {
    ui.showToast('❌ 操作失败', 'error')
  }
}

async function toggleMemory() {
  memoryEnabled.value = !memoryEnabled.value
  try {
    await apiService.knowledge.toggleMemory(memoryEnabled.value)
    ui.showToast(memoryEnabled.value ? '🧠 记忆已开启' : '🔒 记忆已关闭')
  } catch {
    memoryEnabled.value = !memoryEnabled.value
    ui.showToast('❌ 操作失败', 'error')
  }
}

function statusBadgeClass(status: string): string {
  if (status === 'enabled') return 'bg-[#e8fdf5] text-[var(--teal)]'
  if (status === 'syncing') return 'bg-[#fff8e6] text-[var(--amber)]'
  if (status === 'draft') return 'bg-[#eef0fc] text-[var(--indigo)]'
  return 'bg-[var(--bg2)] text-[var(--text3)]'
}

function statusLabel(status: string): string {
  if (status === 'enabled') return '启用'
  if (status === 'syncing') return '待同步'
  if (status === 'draft') return '草稿'
  return status
}

onMounted(() => {
  loadKnowledge()
})
</script>

<template>
  <div class="animate-[fadeIn_.25s_ease] grid grid-cols-[1fr_300px] gap-5">
    <div>
      <div class="text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase mb-2.5">系统知识库</div>

      <div
        v-for="kb in knowledgeBases.filter(k => k.isSystem)"
        :key="kb.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] border-[1.5px] border-[var(--border)] p-[18px] flex items-center gap-3.5 cursor-pointer transition-all duration-200 mb-3 shadow-[var(--shadow-sm)] hover:-translate-y-px hover:shadow-[var(--shadow-md)] hover:border-[rgba(92,107,192,.2)]"
      >
        <div
          :class="[
            'w-12 h-12 rounded-2xl flex items-center justify-center text-[22px] shrink-0',
            kb.status === 'enabled' ? 'bg-[#e8fdf5]' : kb.status === 'syncing' ? 'bg-[#fff8e6]' : 'bg-[#eef0fc]',
          ]"
        >
          {{ kb.id === 'kb-1' ? '📗' : kb.id === 'kb-2' ? '📘' : '📙' }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-[15px] font-extrabold text-[var(--text1)] mb-1">{{ kb.name }}</div>
          <div class="text-xs text-[var(--text3)]">{{ kb.itemCount.toLocaleString() }} {{ kb.itemUnit }} · {{ statusLabel(kb.status) }} · 系统内置</div>
        </div>
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-extrabold',
            statusBadgeClass(kb.status),
          ]"
        >
          {{ statusLabel(kb.status) }}
        </span>
      </div>

      <div class="text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase mt-5 mb-2.5">自定义知识库</div>

      <div
        v-for="kb in knowledgeBases.filter(k => !k.isSystem)"
        :key="kb.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] border-[1.5px] border-[var(--border)] p-[18px] flex items-center gap-3.5 cursor-pointer transition-all duration-200 mb-3 shadow-[var(--shadow-sm)] hover:-translate-y-px hover:shadow-[var(--shadow-md)] hover:border-[rgba(92,107,192,.2)]"
      >
        <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-[22px] shrink-0 bg-[#f0f4ff]">
          {{ kb.id === 'kb-4' ? '📄' : '🗂️' }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-[15px] font-extrabold text-[var(--text1)] mb-1">{{ kb.name }}</div>
          <div class="text-xs text-[var(--text3)]">{{ kb.itemCount }} {{ kb.itemUnit }} · 上次更新 {{ kb.lastUpdated }}</div>
        </div>
        <div class="flex items-center gap-2.5">
          <span
            :class="[
              'inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-extrabold',
              statusBadgeClass(kb.status),
            ]"
          >
            {{ statusLabel(kb.status) }}
          </span>
          <span class="text-[var(--text3)] text-base cursor-pointer">›</span>
        </div>
      </div>

      <button
        class="max-w-[300px] mt-2 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] py-3 px-5 text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)] w-full block"
        @click="ui.openModal('modal-kb-new')"
      >
        ＋ 上传新知识库
      </button>
    </div>

    <div>
      <div class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden">
        <div class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)]">
          <div class="flex items-center gap-3">
            <div class="w-[34px] h-[34px] rounded-[10px] bg-[#fff8e6] flex items-center justify-center text-base shrink-0">🧠</div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">自动记忆</div>
              <div class="text-xs text-[var(--text3)] mt-px">从对话中学习知识</div>
            </div>
          </div>
          <Switch :model-value="memoryEnabled" @update:model-value="toggleMemory" />
        </div>
      </div>

      <InfoTip v-if="memoryEnabled" class="mt-4">
        🧠 记忆功能已开启，AI 将从每次对话中自动提炼知识，形成个性化记忆。
      </InfoTip>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
