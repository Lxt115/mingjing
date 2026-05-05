<script setup lang="ts">
import type { AgentStatus, DeviceStatus, OTABadge, KnowledgeStatus } from '@/types'

defineProps<{
  type: AgentStatus | DeviceStatus | OTABadge | KnowledgeStatus
  label?: string
  withDot?: boolean
}>()
</script>

<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-extrabold',
      type === 'online'
        ? 'bg-[#e8fdf5] text-[var(--teal)]'
        : '',
      type === 'offline'
        ? 'bg-[var(--bg2)] text-[var(--text3)]'
        : '',
      type === 'busy'
        ? 'bg-[#fff8e6] text-[var(--amber)]'
        : '',
      type === 'latest'
        ? 'bg-[#e8fdf5] text-[var(--teal)]'
        : '',
      type === 'pending'
        ? 'bg-[#fff8e6] text-[var(--amber)]'
        : '',
      type === 'updating'
        ? 'bg-[#eef0fc] text-[var(--indigo)]'
        : '',
      type === 'enabled'
        ? 'bg-[#e8fdf5] text-[var(--teal)]'
        : '',
      type === 'disabled'
        ? 'bg-[var(--bg2)] text-[var(--text3)]'
        : '',
      type === 'syncing'
        ? 'bg-[#fff8e6] text-[var(--amber)]'
        : '',
      type === 'draft'
        ? 'bg-[#eef0fc] text-[var(--indigo)]'
        : '',
    ]"
  >
    <div
      v-if="withDot && (type === 'online' || type === 'offline')"
      :class="[
        'w-1.5 h-1.5 rounded-full',
        type === 'online' ? 'bg-[var(--teal)] animate-pulse' : 'bg-[var(--text3)]',
      ]"
    />
    <slot>
      {{ label ?? type }}
    </slot>
  </span>
</template>
