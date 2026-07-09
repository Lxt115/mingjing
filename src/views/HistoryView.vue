<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import type { ConversationListItem, Conversation } from '@/types'
import { apiService } from '@/services'
import { useMediaQuery } from '@/composables'
import { useAgentsStore } from '@/store'
import { FilterChips } from '@/components/ui'
import { formatTime } from '@/utils'

function accentBg(color: string): string {
  if (color === 'var(--teal)') return '#e8fdf5'
  if (color === 'var(--indigo)') return '#eef0fc'
  if (color === 'var(--amber)') return '#fff8e6'
  return '#fff0f0'
}

const { isMobile } = useMediaQuery()
const agentsStore = useAgentsStore()

const filterOptions = computed(() => {
  const names = agentsStore.agents.map((a) => a.name)
  return ['全部', ...names, '今天', '本周']
})
const activeFilter = ref('全部')
const conversations = ref<ConversationListItem[]>([])
const selectedConvId = ref<string | null>(null)
const selectedConv = ref<Conversation | null>(null)
const loadingConv = ref(false)
const showChatPanel = ref(false)

async function loadConversations() {
  const filter = activeFilter.value
  const res = await apiService.history.getList(filter)
  conversations.value = res.data
}

async function selectConversation(id: string) {
  selectedConvId.value = id
  loadingConv.value = true
  if (isMobile.value) {
    showChatPanel.value = true
  }
  try {
    const res = await apiService.history.getConversation(id)
    selectedConv.value = res.data
  } finally {
    loadingConv.value = false
  }
}

function closeChatPanel() {
  showChatPanel.value = false
}

onMounted(async () => {
  await agentsStore.fetchAgents()
  await loadConversations()
  if (!isMobile.value && conversations.value.length > 0) {
    selectConversation(conversations.value[0].id)
  }
})

watch(activeFilter, () => {
  loadConversations()
})
</script>

<template>
  <!-- Desktop Layout -->
  <div
    v-if="!isMobile"
    class="grid grid-cols-[340px_1fr] gap-5"
    style="height: calc(100vh - 60px - 48px)"
  >
    <div
      class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] flex flex-col overflow-hidden"
    >
      <div class="px-5 pt-4 pb-3 border-b border-[var(--border)] shrink-0">
        <div class="text-[15px] font-extrabold text-[var(--text1)] mb-2.5">对话列表</div>
        <FilterChips v-model="activeFilter" :chips="filterOptions" />
      </div>

      <div class="flex-1 overflow-y-auto p-3">
        <template v-for="conv in conversations" :key="conv.id">
          <div
            v-if="conv.dateLabel"
            class="text-[11px] font-bold text-[var(--text3)] tracking-[.6px] uppercase px-2 pt-2 pb-1.5"
          >
            {{ conv.dateLabel }}
          </div>
          <div
            :class="[
              'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-sm)] cursor-pointer transition-all duration-200 relative mb-0.5 border-[1.5px]',
              selectedConvId === conv.id
                ? 'bg-[rgba(255,107,107,.06)] border-[rgba(255,107,107,.15)]'
                : 'border-transparent hover:bg-[var(--bg)]',
            ]"
            @click="selectConversation(conv.id)"
          >
            <div class="w-1 h-9 rounded-[2px] shrink-0" :style="{ background: conv.accentColor }" />
            <div
              class="w-[38px] h-[38px] rounded-xl flex items-center justify-center text-lg shrink-0"
              :style="{
                background:
                  conv.accentColor === 'var(--teal)'
                    ? '#e8fdf5'
                    : conv.accentColor === 'var(--indigo)'
                      ? '#eef0fc'
                      : conv.accentColor === 'var(--amber)'
                        ? '#fff8e6'
                        : '#fff0f0',
              }"
            >
              {{ conv.agentEmoji }}
            </div>
            <div class="flex-1 min-w-0">
              <div
                class="text-[13px] font-bold text-[var(--text1)] whitespace-nowrap overflow-hidden text-ellipsis"
              >
                {{ conv.title }}
              </div>
              <div
                class="text-[11px] text-[var(--text3)] whitespace-nowrap overflow-hidden text-ellipsis mt-0.5"
              >
                {{ conv.preview }}
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-[11px] text-[var(--text3)] mb-1">{{ conv.time }}</div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div
      class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] flex flex-col overflow-hidden"
    >
      <template v-if="selectedConv">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-[var(--border)] shrink-0">
          <div
            class="w-[38px] h-[38px] rounded-xl flex items-center justify-center text-xl"
            :style="{ background: selectedConv.accentBg }"
          >
            {{ selectedConv.agentEmoji }}
          </div>
          <div>
            <div class="text-[15px] font-extrabold text-[var(--text1)]">
              {{ selectedConv.title }}
            </div>
            <div class="text-xs text-[var(--text3)] mt-px">{{ selectedConv.meta }}</div>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-5 flex flex-col gap-3.5 bg-[var(--bg)]">
          <div
            v-for="msg in selectedConv.messages"
            :key="msg.id"
            :class="[
              'flex flex-col max-w-[65%]',
              msg.role === 'user' ? 'self-end items-end' : 'self-start items-start',
            ]"
          >
            <div
              :class="[
                'px-[15px] py-[11px] rounded-2xl text-sm leading-relaxed font-medium',
                msg.role === 'user'
                  ? 'bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white rounded-br'
                  : 'bg-[var(--surface)] text-[var(--text1)] rounded-bl border border-[var(--border)] shadow-[var(--shadow-sm)]',
              ]"
            >
              <span v-for="(line, i) in msg.text.split('\n')" :key="i">
                {{ line }}<br v-if="i < msg.text.split('\n').length - 1" />
              </span>
            </div>
            <div class="text-[11px] text-[var(--text3)] mt-1.5 px-1">
              {{ msg.role === 'user' ? '你' : 'AI伙伴' }} · {{ formatTime(msg.timestamp) }}
            </div>
          </div>
        </div>
      </template>

      <div
        v-else-if="loadingConv"
        class="flex-1 flex items-center justify-center text-[var(--text3)] text-sm font-semibold"
      >
        加载中…
      </div>

      <div
        v-else
        class="flex-1 flex flex-col items-center justify-center gap-3 text-[var(--text3)]"
      >
        <div class="text-5xl opacity-40">💬</div>
        <div class="text-sm font-semibold">请选择一个对话</div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div class="history-filter-mobile flex gap-1.5 px-4 pt-3 pb-4 overflow-x-auto shrink-0">
      <div
        v-for="opt in filterOptions"
        :key="opt"
        :class="[
          'py-1.5 px-3.5 rounded-[20px] text-xs font-bold whitespace-nowrap cursor-pointer transition-all duration-200',
          activeFilter === opt
            ? 'bg-[var(--coral)] text-white'
            : 'bg-[var(--surface)] text-[var(--text2)] shadow-[var(--shadow-sm)]',
        ]"
        @click="activeFilter = opt"
      >
        {{ opt }}
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-4">
      <template v-for="conv in conversations" :key="conv.id">
        <div
          v-if="conv.dateLabel"
          class="text-xs font-extrabold text-[var(--text3)] tracking-[.6px] uppercase pt-3 pb-1.5"
        >
          {{ conv.dateLabel }}
        </div>
        <div
          class="mb-2.5 bg-[var(--surface)] rounded-[var(--radius-md)] py-3.5 px-4 flex items-center gap-3 cursor-pointer shadow-[var(--shadow-sm)] transition-all duration-200 active:scale-[.98] relative overflow-hidden"
          @click="selectConversation(conv.id)"
        >
          <div
            class="absolute left-0 top-0 bottom-0 w-1"
            :style="{ background: conv.accentColor }"
          />
          <div
            class="w-[42px] h-[42px] rounded-[14px] flex items-center justify-center text-xl shrink-0"
            :style="{
              background:
                conv.accentColor === 'var(--teal)'
                  ? '#e8fdf5'
                  : conv.accentColor === 'var(--indigo)'
                    ? '#eef0fc'
                    : conv.accentColor === 'var(--amber)'
                      ? '#fff8e6'
                      : '#fff0f0',
            }"
          >
            {{ conv.agentEmoji }}
          </div>
          <div class="flex-1 min-w-0">
            <div
              class="text-sm font-extrabold text-[var(--text1)] mb-[3px] whitespace-nowrap overflow-hidden text-ellipsis"
            >
              {{ conv.title }}
            </div>
            <div
              class="text-xs text-[var(--text3)] whitespace-nowrap overflow-hidden text-ellipsis"
            >
              {{ conv.preview }}
            </div>
          </div>
          <div class="text-right shrink-0">
            <div class="text-[11px] text-[var(--text3)] mb-1">{{ conv.time }}</div>
          </div>
        </div>
      </template>
    </div>

    <Transition name="slide">
      <div v-if="showChatPanel" class="fixed inset-0 z-50 bg-[var(--bg)] flex flex-col">
        <div
          class="flex items-center gap-3 px-4 py-3.5 border-b border-[var(--border)] bg-white/90 backdrop-blur-[12px] shrink-0"
        >
          <button
            class="w-9 h-9 rounded-full bg-[var(--bg2)] border-none flex items-center justify-center text-lg text-[var(--text1)] cursor-pointer shrink-0 transition-all duration-200 active:scale-[.92]"
            @click="closeChatPanel"
          >
            ‹
          </button>
          <div v-if="selectedConv">
            <div class="text-[17px] font-black text-[var(--text1)]">{{ selectedConv.title }}</div>
            <div class="text-[11px] text-[var(--text3)] font-semibold">{{ selectedConv.meta }}</div>
          </div>
        </div>

        <div
          v-if="selectedConv"
          class="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-[var(--bg)]"
        >
          <div
            v-for="msg in selectedConv.messages"
            :key="msg.id"
            :class="[
              'flex flex-col max-w-[78%] animate-[msgIn_.25s_ease]',
              msg.role === 'user' ? 'self-end items-end' : 'self-start items-start',
            ]"
          >
            <div
              :class="[
                'py-[11px] px-[14px] rounded-[18px] text-sm leading-[1.55] font-semibold',
                msg.role === 'user'
                  ? 'bg-[var(--coral)] text-white rounded-br'
                  : 'bg-[var(--surface)] text-[var(--text1)] rounded-bl shadow-[var(--shadow-sm)]',
              ]"
            >
              <span v-for="(line, i) in msg.text.split('\n')" :key="i">
                {{ line }}<br v-if="i < msg.text.split('\n').length - 1" />
              </span>
            </div>
            <div class="text-[10px] text-[var(--text3)] mt-1 px-1">
              {{ msg.role === 'user' ? '你' : 'AI伙伴' }} · {{ formatTime(msg.timestamp) }}
            </div>
          </div>
        </div>

        <div
          v-else
          class="flex-1 flex items-center justify-center text-[var(--text3)] text-sm font-semibold"
        >
          加载中…
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@keyframes msgIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-enter-from {
  transform: translateX(100%);
}
.slide-leave-to {
  transform: translateX(100%);
}
</style>
