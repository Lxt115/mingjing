<script setup lang="ts">
defineProps<{
  hoverable?: boolean
  padding?: boolean
}>()
</script>

<template>
  <div
    :class="[
      'bg-[var(--surface)] border border-[var(--border)] shadow-[var(--shadow-sm)] rounded-[var(--radius-md)] overflow-hidden transition-all duration-200',
      hoverable ? 'cursor-pointer hover:-translate-y-px hover:shadow-[var(--shadow-md)]' : '',
      padding ? 'p-5' : '',
    ]"
  >
    <slot />
  </div>
</template>
