<script setup lang="ts">
import { useMediaQuery } from '@/composables'
import { DesktopSidebar, TopBar, MobileTabBar } from '@/components/layout'
import { Toast } from '@/components/ui'
import ModalsContainer from '@/components/ModalsContainer.vue'

const { isMobile } = useMediaQuery()
</script>

<template>
  <div v-if="!isMobile" class="flex h-screen overflow-hidden">
    <DesktopSidebar />
    <div class="flex-1 flex flex-col h-screen overflow-hidden">
      <TopBar />
      <main class="flex-1 overflow-y-auto overflow-x-hidden px-7 py-6 pb-12">
        <router-view v-slot="{ Component }">
          <transition name="page">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>

  <div v-else class="flex flex-col h-[100dvh] overflow-hidden bg-[var(--bg)]">
    <TopBar />
    <main class="flex-1 overflow-y-auto overflow-x-hidden">
      <router-view v-slot="{ Component }">
        <transition name="page">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <MobileTabBar />
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
</style>
