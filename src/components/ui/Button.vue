<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  full?: boolean
}>()
</script>

<template>
  <button
    :class="[
      'inline-flex items-center justify-center gap-1.5 font-bold rounded-[10px] transition-all duration-200 cursor-pointer border-none focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--coral)]/30',
      full ? 'w-full' : '',
      size === 'sm' ? 'h-[30px] px-3 text-xs' : '',
      size === 'md' || !size ? 'h-[34px] px-3.5 text-[13px]' : '',
      size === 'lg' ? 'h-11 px-5 text-sm' : '',
      variant === 'primary' || !variant
        ? 'text-white bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] shadow-[0_2px_10px_rgba(255,107,107,.3)] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(255,107,107,.4)]'
        : '',
      variant === 'secondary'
        ? 'text-[var(--text2)] bg-[var(--bg2)] hover:bg-[var(--border)]'
        : '',
      variant === 'danger'
        ? 'text-[var(--coral)] border border-[var(--coral)]/50 bg-[#fff0f0] hover:bg-[var(--coral)] hover:text-white'
        : '',
      variant === 'ghost'
        ? 'text-[var(--text2)] bg-transparent hover:bg-[var(--bg2)]'
        : '',
      disabled ? 'opacity-50 cursor-not-allowed pointer-events-none' : '',
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>
