<script setup lang="ts">
defineProps<{
  open: boolean
  size?: 'default' | 'large'
  title?: string
}>()

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <Transition name="overlay">
      <div
        v-if="open"
        class="fixed inset-0 z-[500] bg-[rgba(26,29,46,.45)] backdrop-blur-[4px] flex items-center justify-center"
        @click.self="emit('close')"
      >
        <Transition name="modal">
          <div
            v-if="open"
            :class="[
              'bg-[var(--surface)] rounded-[var(--radius-xl)] shadow-[var(--shadow-lg)] max-h-[88vh] overflow-y-auto relative',
              size === 'large' ? 'w-[640px]' : 'w-[480px]',
              'max-w-[92vw]',
            ]"
          >
            <div
              v-if="title || $slots.header"
              class="flex items-center justify-between px-7 pt-6 pb-[18px] border-b border-[var(--border)]"
            >
              <h3 class="text-lg font-black text-[var(--text1)]">
                <slot name="header">
                  {{ title }}
                </slot>
              </h3>
              <button
                class="w-[30px] h-[30px] rounded-full bg-[var(--bg2)] border-none flex items-center justify-center text-base text-[var(--text2)] cursor-pointer hover:bg-[var(--border)] transition-colors duration-200"
                @click="emit('close')"
              >
                ✕
              </button>
            </div>

            <div class="px-7 py-5">
              <slot />
            </div>

            <div
              v-if="$slots.footer"
              class="flex gap-3 px-7 pb-6 pt-0"
            >
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.overlay-enter-active { transition: opacity 0.2s ease; }
.overlay-leave-active { transition: opacity 0.15s ease; }
.overlay-enter-from, .overlay-leave-to { opacity: 0; }

.modal-enter-active {
  transition: all 0.25s cubic-bezier(0.34, 1.4, 0.64, 1);
}
.modal-leave-active {
  transition: all 0.15s ease;
}
.modal-enter-from {
  opacity: 0;
  transform: scale(0.93) translateY(16px);
}
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}
</style>
