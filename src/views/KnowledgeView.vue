<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import { apiService } from '@/services'
import { Switch, InfoTip } from '@/components/ui'
import type { KnowledgeBase } from '@/types'

const ui = useUiStore()
const { isMobile } = useMediaQuery()
const kbList = ref<KnowledgeBase[]>([])
const memoryEnabled = ref(true)

function toggleMemory() {
  memoryEnabled.value = !memoryEnabled.value
  ui.showToast(memoryEnabled.value ? '🧠 记忆已开启' : '🔒 记忆已关闭')
}

function openKbUpload() {
  ui.openModal('modal-kb-new')
}

onMounted(async () => {
  const res = await apiService.knowledge.getList()
  kbList.value = res.data
})
</script>

<template>
  <!-- Desktop Layout -->
  <div v-if="!isMobile" class="animate-[fadeIn_.25s_ease] grid grid-cols-[340px_1fr] gap-5" style="height: calc(100vh - 60px - 48px)">
    <div class="flex flex-col gap-4">
      <div class="kb-cat bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] py-5 px-6">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-[10px] bg-[#fff8e6] flex items-center justify-center text-lg shrink-0">🧠</div>
            <div class="text-[15px] font-extrabold text-[var(--text1)]">自动记忆</div>
          </div>
          <Switch :model-value="memoryEnabled" @update:model-value="toggleMemory" />
        </div>
        <div class="auto-memory-hint bg-[var(--bg)] rounded-[12px] p-4 text-[12px] text-[var(--text2)] leading-relaxed font-semibold">
          <div class="mb-1.5">📝 自动学习内容</div>
          <div class="text-[var(--text3)] leading-[1.65] text-[11px]">
            AI 自动记录关键信息如喜好、习惯等，形成个性化知识
          </div>
        </div>
      </div>
    </div>

    <div class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden flex flex-col">
      <div class="px-5 pt-4 pb-3 border-b border-[var(--border)] shrink-0 flex justify-between items-center">
        <div class="text-[15px] font-extrabold text-[var(--text1)]">知识库列表</div>
        <button
          class="h-8 px-4 rounded-lg bg-[var(--coral)] text-white border-none text-xs font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--teal)]"
          @click="openKbUpload"
        >
          ＋ 上传
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        <div class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.6px] uppercase mb-1">已上传</div>
        <div
          v-for="kb in kbList"
          :key="kb.id"
          :class="[
            'bg-[var(--bg)] rounded-[var(--radius-md)] py-3 px-4 flex items-center justify-between',
            'border-l-4',
          ]"
          :style="{ borderLeftColor: kb.category === 'system' ? 'var(--teal)' : 'var(--coral)' }"
        >
          <div>
            <div class="text-sm font-extrabold text-[var(--text1)]">{{ kb.name }}</div>
            <div class="text-[11px] text-[var(--text3)]">{{ kb.recordCount }} 条记录 · {{ kb.fileSize }}</div>
          </div>
          <span class="text-xs font-bold text-[var(--teal)] bg-[#e8fdf5] px-2 py-0.5 rounded-full">
            {{ kb.category === 'system' ? '系统' : '自定义' }}
          </span>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div
      class="memory-card-mobile flex items-center justify-between py-3.5 px-4 bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mb-3 mx-2"
      @click="toggleMemory"
    >
      <div class="flex items-center gap-2.5">
        <div class="w-10 h-10 rounded-[12px] bg-[#fff8e6] flex items-center justify-center text-lg shrink-0">🧠</div>
        <div>
          <div class="text-sm font-extrabold text-[var(--text1)]">自动记忆</div>
          <div class="text-xs text-[var(--text3)]">AI 自动学习对话，记录关键信息</div>
        </div>
      </div>
      <Switch :model-value="memoryEnabled" @update:model-value="toggleMemory" />
    </div>

    <div class="flex items-center justify-between px-2 pt-3 pb-3">
      <div>
        <div class="text-[13px] font-extrabold text-[var(--text1)]">我的知识库</div>
        <div class="text-[11px] text-[var(--text3)] mt-px font-bold">{{ kbList.length }} 个知识库</div>
      </div>
      <div class="flex gap-2">
        <button
          class="py-2 px-3 rounded-[20px] bg-[rgba(255,107,107,.1)] text-[var(--coral)] text-[11px] font-extrabold border-none cursor-pointer transition-all duration-200 active:scale-[.95]"
          @click="openKbUpload"
        >
          ＋ 新建
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-for="kb in kbList"
        :key="kb.id"
        class="kb-item-mobile bg-[var(--surface)] rounded-[var(--radius-md)] p-4 mb-2.5 shadow-[var(--shadow-sm)] border-l-[3px] transition-all duration-200 active:scale-[.98]"
        :style="{ borderLeftColor: kb.category === 'system' ? 'var(--teal)' : 'var(--coral)' }"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="text-base font-black text-[var(--text1)]">{{ kb.name }}</div>
          <span
            :class="[
              'text-[10px] font-extrabold px-2 py-0.5 rounded-[20px]',
              kb.category === 'system' ? 'bg-[#e8fdf5] text-[var(--teal)]' : 'bg-[rgba(255,107,107,.1)] text-[var(--coral)]',
            ]"
          >
            {{ kb.category === 'system' ? '系统' : '自定义' }}
          </span>
        </div>
        <div class="flex items-center justify-between text-xs font-bold">
          <span class="text-[var(--text3)]">📄 {{ kb.recordCount }} 条记录</span>
          <span class="text-[var(--text3)]">📦 {{ kb.fileSize }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
