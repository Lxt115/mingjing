<script setup lang="ts" generic="T extends string">
defineProps<{
  chips: T[]
  modelValue: T
}>()

const emit = defineEmits<{
  'update:modelValue': [value: T]
}>()
</script>

<template>
  <div class="flex flex-wrap gap-1.5">
    <button
      v-for="chip in chips"
      :key="chip"
      :class="[
        'px-3 py-[5px] rounded-full text-xs font-bold cursor-pointer border-none transition-all duration-200 whitespace-nowrap',
        modelValue === chip
          ? 'bg-[var(--coral)] text-white'
          : 'bg-[var(--bg)] text-[var(--text2)] hover:bg-[var(--bg2)]',
      ]"
      @click="emit('update:modelValue', chip)"
    >
      {{ chip }}
    </button>
  </div>
</template>
