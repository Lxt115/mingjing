<script setup lang="ts">
import { Sidebar, TopBar } from '@/components/layout'
import { Toast } from '@/components/ui'
import ModalsContainer from '@/components/ModalsContainer.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden">
    <Sidebar />
    <div class="flex-1 flex flex-col h-screen overflow-hidden">
      <TopBar />
      <main class="flex-1 overflow-y-auto overflow-x-hidden px-7 py-6">
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
  <Toast />
  <ModalsContainer />
</template>

<style scoped>
.page-enter-active {
  animation: fadeIn 0.25s ease;
}
.page-leave-active {
  animation: fadeIn 0.15s ease reverse;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
