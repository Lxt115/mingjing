<script setup lang="ts">
import { useUiStore } from '@/store'

const ui = useUiStore()
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-6 right-6 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="t in ui.toasts"
          :key="t.id"
          :class="[
            'px-5 py-3 rounded-xl text-[13px] font-bold shadow-[0_8px_24px_rgba(0,0,0,.2)] pointer-events-auto',
            t.type === 'success' ? 'bg-[var(--teal)] text-white' : '',
            t.type === 'error' ? 'bg-[#ff4d4d] text-white' : '',
            t.type === 'info' ? 'bg-[var(--text1)] text-white' : '',
            t.type === 'warning' ? 'bg-[var(--amber)] text-[var(--text1)]' : '',
          ]"
        >
          {{ t.text }}
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-enter-active {
  transition: all 0.3s ease;
}
.toast-leave-active {
  transition: all 0.2s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(20px);
}
</style>
