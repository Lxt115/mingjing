<script setup lang="ts">
defineProps<{
  type?: 'info' | 'warning' | 'error'
}>()
</script>

<template>
  <div
    :class="[
      'rounded-[var(--radius-sm)] px-3.5 py-2.5 text-xs font-semibold border',
      type === 'info' || !type
        ? 'bg-[rgba(92,107,192,.08)] text-[var(--indigo)] border-[rgba(92,107,192,.15)]'
        : '',
      type === 'warning'
        ? 'bg-[#fff8e6] text-[var(--amber)] border-[rgba(255,184,48,.2)]'
        : '',
      type === 'error'
        ? 'bg-[#fff0f0] text-[var(--coral)] border-[rgba(255,107,107,.2)]'
        : '',
    ]"
  >
    <slot />
  </div>
</template>
