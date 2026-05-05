<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function toggle() {
  emit('update:modelValue', !props.modelValue)
}
</script>

<template>
  <div
    role="switch"
    :aria-checked="modelValue"
    :tabindex="disabled ? -1 : 0"
    :class="[
      'relative w-[42px] h-6 rounded-xl cursor-pointer transition-colors duration-250 flex-shrink-0',
      modelValue ? 'bg-[var(--teal)]' : 'bg-[var(--bg2)]',
      disabled ? 'opacity-50 cursor-not-allowed' : '',
    ]"
    @click="!disabled && toggle()"
    @keydown.enter.prevent="!disabled && toggle()"
    @keydown.space.prevent="!disabled && toggle()"
  >
    <div
      :class="[
        'absolute top-[3px] w-[18px] h-[18px] rounded-full bg-white shadow-[0_1px_4px_rgba(0,0,0,.2)] transition-transform duration-250',
        modelValue ? 'translate-x-[18px]' : 'translate-x-[3px]',
      ]"
    />
  </div>
</template>
