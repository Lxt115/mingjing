<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useUiStore } from '@/store'
import { useMediaQuery } from '@/composables'
import { apiService } from '@/services'
import { Switch } from '@/components/ui'
import type { KnowledgeBase, KnowledgeDetail } from '@/types'

const ui = useUiStore()
const { isMobile } = useMediaQuery()
const kbList = ref<KnowledgeBase[]>([])
const memoryEnabled = ref(true)
const selectedKb = ref<KnowledgeDetail | null>(null)
const detailLoading = ref(false)

async function loadList() {
  try {
    const res = await apiService.knowledge.getList()
    kbList.value = res.data
  } catch {
    /* ignore */
  }
}

async function toggleMemory() {
  memoryEnabled.value = !memoryEnabled.value
  try {
    await apiService.knowledge.toggleMemory(memoryEnabled.value)
    ui.showToast(memoryEnabled.value ? '🧠 记忆已开启' : '🔒 记忆已关闭')
  } catch {
    memoryEnabled.value = !memoryEnabled.value
  }
}

async function selectKb(kb: KnowledgeBase) {
  detailLoading.value = true
  selectedKb.value = null
  try {
    const res = await apiService.knowledge.getDetail(kb.id)
    selectedKb.value = res.data
  } catch {
    ui.showToast('❌ 加载知识库详情失败', 'error')
  } finally {
    detailLoading.value = false
  }
}

async function toggleKnowledge(kb: KnowledgeBase) {
  const newState = !kb.isEnabled
  try {
    await apiService.knowledge.toggleKnowledge(kb.id, newState)
    kb.isEnabled = newState
    kb.status = newState ? 'enabled' : 'disabled'
    if (selectedKb.value && selectedKb.value.id === kb.id) {
      selectedKb.value.isEnabled = newState
    }
    ui.showToast(newState ? '✅ 已启用' : '⏸️ 已禁用')
  } catch {
    ui.showToast('❌ 操作失败', 'error')
  }
}

async function deleteKnowledge(kb: KnowledgeBase) {
  if (!confirm(`确定删除知识库「${kb.name}」吗？此操作不可撤销。`)) return
  try {
    await apiService.knowledge.delete(kb.id)
    kbList.value = kbList.value.filter((k) => k.id !== kb.id)
    if (selectedKb.value?.id === kb.id) selectedKb.value = null
    ui.showToast('🗑️ 已删除')
  } catch {
    ui.showToast('❌ 删除失败', 'error')
  }
}

async function deleteContentItem(index: number) {
  if (!selectedKb.value) return
  if (!confirm('确定删除这条内容吗？')) return
  try {
    await apiService.knowledge.deleteContent(selectedKb.value.id, index)
    selectedKb.value.content.splice(index, 1)
    selectedKb.value.itemCount = selectedKb.value.content.length
    ui.showToast('🗑️ 内容已删除')
  } catch {
    ui.showToast('❌ 删除失败', 'error')
  }
}

function openKbUpload() {
  ui.openModal('modal-kb-new')
}

function refreshDetail() {
  if (selectedKb.value) selectKb(selectedKb.value)
}

function categoryLabel(kb: KnowledgeBase) {
  if (kb.isSystem) return '系统'
  return kb.status === 'enabled' ? '已启用' : '已禁用'
}

function categoryClass(kb: KnowledgeBase) {
  if (kb.isSystem) return 'bg-[#e8fdf5] text-[var(--teal)]'
  return kb.status === 'enabled'
    ? 'bg-[#e8fdf5] text-[var(--teal)]'
    : 'bg-[#fff0f0] text-[var(--coral)]'
}

function borderColor(kb: KnowledgeBase) {
  return kb.isSystem ? 'var(--teal)' : 'var(--coral)'
}

onMounted(loadList)
watch(() => ui.kbRefreshCounter, loadList)
</script>

<template>
  <div
    v-if="!isMobile"
    class="animate-[fadeIn_.25s_ease] grid grid-cols-[340px_1fr] gap-5"
    style="height: calc(100vh - 60px - 48px)"
  >
    <!-- Left panel: KB list -->
    <div class="flex flex-col gap-4">
      <div
        class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] py-5 px-6"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2.5">
            <div
              class="w-9 h-9 rounded-[10px] bg-[#fff8e6] flex items-center justify-center text-lg shrink-0"
            >
              🧠
            </div>
            <div class="text-[15px] font-extrabold text-[var(--text1)]">自动记忆</div>
          </div>
          <Switch :model-value="memoryEnabled" @update:model-value="toggleMemory" />
        </div>
        <div
          class="bg-[var(--bg)] rounded-[12px] p-4 text-[12px] text-[var(--text2)] leading-relaxed font-semibold"
        >
          <div class="mb-1.5">📝 自动学习内容</div>
          <div class="text-[var(--text3)] leading-[1.65] text-[11px]">
            AI 自动记录关键信息如喜好、习惯等，形成个性化知识
          </div>
        </div>
      </div>
    </div>

    <!-- Right panel -->
    <div
      class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden flex flex-col"
    >
      <!-- Toolbar -->
      <div
        class="px-5 pt-4 pb-3 border-b border-[var(--border)] shrink-0 flex justify-between items-center"
      >
        <div class="text-[15px] font-extrabold text-[var(--text1)]">
          {{ selectedKb ? selectedKb.name : '知识库列表' }}
        </div>
        <div class="flex gap-2">
          <button
            v-if="selectedKb"
            class="h-8 px-4 rounded-lg bg-[var(--bg2)] text-[var(--text1)] border border-[var(--border)] text-xs font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
            @click="selectedKb = null"
          >
            ← 返回列表
          </button>
          <button
            class="h-8 px-4 rounded-lg bg-[var(--coral)] text-white border-none text-xs font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--teal)]"
            @click="openKbUpload"
          >
            ＋ 上传
          </button>
        </div>
      </div>

      <!-- List view -->
      <div v-if="!selectedKb" class="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
        <div
          v-for="kb in kbList"
          :key="kb.id"
          class="bg-[var(--bg)] rounded-[var(--radius-md)] py-3 px-4 flex items-center justify-between border-l-4 cursor-pointer hover:bg-[#fafafa] transition-colors"
          :style="{ borderLeftColor: borderColor(kb) }"
          @click="selectKb(kb)"
        >
          <div>
            <div class="text-sm font-extrabold text-[var(--text1)]">
              {{ kb.name }}
              <span v-if="!kb.isEnabled" class="text-[10px] text-[var(--text3)] ml-1"
                >(已禁用)</span
              >
            </div>
            <div class="text-[11px] text-[var(--text3)]">
              {{ kb.itemCount }} {{ kb.itemUnit }} · {{ kb.description }}
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span :class="['text-xs font-bold px-2 py-0.5 rounded-full', categoryClass(kb)]">
              {{ categoryLabel(kb) }}
            </span>
            <button
              v-if="!kb.isSystem"
              class="text-[var(--text3)] hover:text-[var(--coral)] bg-none border-none cursor-pointer text-xs px-1 py-1"
              title="删除"
              @click.stop="deleteKnowledge(kb)"
            >
              🗑️
            </button>
          </div>
        </div>
        <div v-if="kbList.length === 0" class="text-center text-[var(--text3)] text-sm py-10">
          暂无知识库，点击右上角「＋ 上传」新建
        </div>
      </div>

      <!-- Detail view -->
      <div v-else class="flex-1 overflow-y-auto p-5 flex flex-col gap-4">
        <div v-if="detailLoading" class="text-center text-[var(--text3)] py-10">加载中…</div>

        <template v-else>
          <!-- Info bar -->
          <div class="flex items-center gap-3 flex-wrap">
            <span
              :class="['text-xs font-bold px-2.5 py-1 rounded-full', categoryClass(selectedKb)]"
            >
              {{ categoryLabel(selectedKb) }}
            </span>
            <span class="text-xs text-[var(--text3)]"
              >📄 {{ selectedKb.itemCount }} {{ selectedKb.itemUnit }}</span
            >
            <span class="text-xs text-[var(--text3)]">{{ selectedKb.description }}</span>
            <div class="flex-1"></div>
            <button
              class="text-xs font-bold px-2 py-1 rounded bg-[#fff0f0] text-[var(--coral)] border-none cursor-pointer hover:bg-[#ffe0e0] transition-colors"
              title="切换到启用/禁用"
              @click="toggleKnowledge(selectedKb)"
            >
              {{ selectedKb.isEnabled ? '⏸️ 禁用' : '✅ 启用' }}
            </button>
            <button
              v-if="!selectedKb.isSystem"
              class="text-xs font-bold px-2 py-1 rounded bg-[#ff4444] text-white border-none cursor-pointer hover:bg-[#cc0000] transition-colors"
              @click="deleteKnowledge(selectedKb)"
            >
              🗑️ 删除知识库
            </button>
          </div>

          <!-- Content list -->
          <div
            class="text-[10px] font-extrabold text-[var(--text3)] tracking-[.6px] uppercase mt-2"
          >
            知识库内容
          </div>

          <div
            v-if="!selectedKb.content || selectedKb.content.length === 0"
            class="text-center text-[var(--text3)] text-sm py-6 bg-[var(--bg)] rounded-[var(--radius-md)]"
          >
            暂无内容，请通过「＋ 上传」添加文件
          </div>

          <div
            v-for="(item, idx) in selectedKb.content"
            :key="idx"
            class="bg-[var(--bg)] rounded-[var(--radius-md)] border border-[var(--border)] overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-4 py-2 border-b border-[var(--border)] bg-[#fafafa]"
            >
              <span class="text-xs font-extrabold text-[var(--text2)]"
                >第 {{ idx + 1 }} 条 · {{ item.length }} 字</span
              >
              <button
                class="text-[var(--text3)] hover:text-[var(--coral)] bg-none border-none cursor-pointer text-xs px-1"
                title="删除此条"
                @click="deleteContentItem(idx)"
              >
                ✕ 删除
              </button>
            </div>
            <div
              class="p-4 text-[13px] text-[var(--text1)] leading-relaxed whitespace-pre-wrap max-h-[300px] overflow-y-auto font-semibold"
            >
              {{ item.slice(0, 2000) }}{{ item.length > 2000 ? '…' : '' }}
            </div>
          </div>

          <!-- Add content button -->
          <div class="flex gap-2 mt-2">
            <button
              class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg)] border-2 border-dashed border-[var(--border)] text-[var(--text2)] text-sm font-bold cursor-pointer transition-all duration-200 hover:border-[var(--indigo-lt)] hover:bg-[#eef0fc]"
              @click="openKbUpload"
            >
              ＋ 添加新文件
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>

  <!-- Mobile layout -->
  <div v-else class="flex flex-col h-full">
    <div
      class="flex items-center justify-between py-3.5 px-4 bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mb-3 mx-2"
      @click="toggleMemory"
    >
      <div class="flex items-center gap-2.5">
        <div
          class="w-10 h-10 rounded-[12px] bg-[#fff8e6] flex items-center justify-center text-lg shrink-0"
        >
          🧠
        </div>
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
        <div class="text-[11px] text-[var(--text3)] mt-px font-bold">
          {{ kbList.length }} 个知识库
        </div>
      </div>
      <button
        class="py-2 px-3 rounded-[20px] bg-[rgba(255,107,107,.1)] text-[var(--coral)] text-[11px] font-extrabold border-none cursor-pointer transition-all duration-200 active:scale-[.95]"
        @click="openKbUpload"
      >
        ＋ 新建
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-for="kb in kbList"
        :key="kb.id"
        class="bg-[var(--surface)] rounded-[var(--radius-md)] p-4 mb-2.5 shadow-[var(--shadow-sm)] border-l-[3px] transition-all duration-200 active:scale-[.98]"
        :style="{ borderLeftColor: borderColor(kb) }"
        @click="selectKb(kb)"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="text-base font-black text-[var(--text1)]">{{ kb.name }}</div>
          <span
            :class="['text-[10px] font-extrabold px-2 py-0.5 rounded-[20px]', categoryClass(kb)]"
          >
            {{ categoryLabel(kb) }}
          </span>
        </div>
        <div class="flex items-center justify-between text-xs font-bold">
          <span class="text-[var(--text3)]">📄 {{ kb.itemCount }} {{ kb.itemUnit }}</span>
          <span class="text-[var(--text3)]">{{ kb.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped></style>
