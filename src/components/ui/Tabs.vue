<script setup lang="ts" generic="T extends string">
defineProps<{
  tabs: { id: T; label: string; icon?: string }[]
  modelValue: T
}>()

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()
</script>

<template>
  <div class="flex gap-0.5 bg-[var(--bg2)] p-1 rounded-[10px] w-fit">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      :class="[
        'px-[18px] py-[7px] rounded-[7px] text-[13px] font-bold cursor-pointer border-none transition-all duration-200 whitespace-nowrap flex items-center gap-1.5',
        modelValue === tab.id
          ? 'bg-[var(--surface)] text-[var(--text1)] shadow-[var(--shadow-sm)]'
          : 'bg-transparent text-[var(--text2)] hover:text-[var(--text2)]/80',
      ]"
      @click="emit('update:modelValue', tab.id)"
    >
      <span v-if="tab.icon">{{ tab.icon }}</span>
      {{ tab.label }}
    </button>
  </div>
</template>
