<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { ConversationListItem, Conversation } from '@/types'
import { apiService } from '@/services'
import { FilterChips } from '@/components/ui'
import { formatTime } from '@/utils'

const filterOptions = ['全部', '笃笃', '故事大王', '今天', '本周']
const activeFilter = ref('全部')
const conversations = ref<ConversationListItem[]>([])
const selectedConvId = ref<string | null>(null)
const selectedConv = ref<Conversation | null>(null)
const loadingConv = ref(false)

async function loadConversations() {
  const filter = activeFilter.value
  const res = await apiService.history.getList(filter)
  conversations.value = res.data
}

async function selectConversation(id: string) {
  selectedConvId.value = id
  loadingConv.value = true
  try {
    const res = await apiService.history.getConversation(id)
    selectedConv.value = res.data
  } finally {
    loadingConv.value = false
  }
}

onMounted(async () => {
  await loadConversations()
  if (conversations.value.length > 0) {
    selectConversation(conversations.value[0].id)
  }
})

watch(activeFilter, () => {
  loadConversations()
})
</script>

<template>
  <div class="grid grid-cols-[340px_1fr] gap-5" style="height: calc(100vh - 60px - 48px)">
    <div class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] flex flex-col overflow-hidden">
      <div class="px-5 pt-4 pb-3 border-b border-[var(--border)] shrink-0">
        <div class="text-[15px] font-extrabold text-[var(--text1)] mb-2.5">对话列表</div>
        <FilterChips
          v-model="activeFilter"
          :chips="filterOptions"
        />
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
            <div
              class="w-1 h-9 rounded-[2px] shrink-0"
              :style="{ background: conv.accentColor }"
            />
            <div
              class="w-[38px] h-[38px] rounded-xl flex items-center justify-center text-lg shrink-0"
              :style="{ background: conv.accentColor === 'var(--teal)' ? '#e8fdf5' : conv.accentColor === 'var(--indigo)' ? '#eef0fc' : conv.accentColor === 'var(--amber)' ? '#fff8e6' : '#fff0f0' }"
            >
              {{ conv.agentEmoji }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[13px] font-bold text-[var(--text1)] whitespace-nowrap overflow-hidden text-ellipsis">{{ conv.title }}</div>
              <div class="text-[11px] text-[var(--text3)] whitespace-nowrap overflow-hidden text-ellipsis mt-0.5">{{ conv.preview }}</div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-[11px] text-[var(--text3)] mb-1">{{ conv.time }}</div>
              <span class="text-[10px] font-extrabold bg-[var(--coral)] text-white rounded-[10px] px-1.5 py-px inline-block">{{ conv.messageCount }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div class="bg-[var(--surface)] rounded-[var(--radius-lg)] border border-[var(--border)] shadow-[var(--shadow-sm)] flex flex-col overflow-hidden">
      <template v-if="selectedConv">
        <div class="flex items-center gap-3 px-5 py-4 border-b border-[var(--border)] shrink-0">
          <div
            class="w-[38px] h-[38px] rounded-xl flex items-center justify-center text-xl"
            :style="{ background: selectedConv.accentBg }"
          >
            {{ selectedConv.agentEmoji }}
          </div>
          <div>
            <div class="text-[15px] font-extrabold text-[var(--text1)]">{{ selectedConv.title }}</div>
            <div class="text-xs text-[var(--text3)] mt-px">{{ selectedConv.meta }}</div>
          </div>
        </div>

        <div
          class="flex-1 overflow-y-auto p-5 flex flex-col gap-3.5 bg-[var(--bg)]"
          ref="msgContainer"
        >
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

      <div v-else-if="loadingConv" class="flex-1 flex items-center justify-center text-[var(--text3)] text-sm font-semibold">
        加载中…
      </div>

      <div v-else class="flex-1 flex flex-col items-center justify-center gap-3 text-[var(--text3)]">
        <div class="text-5xl opacity-40">💬</div>
        <div class="text-sm font-semibold">请选择一个对话</div>
      </div>
    </div>
  </div>
</template>
