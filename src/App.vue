<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMediaQuery } from '@/composables'
import { DesktopSidebar, TopBar, MobileTabBar } from '@/components/layout'
import { Toast } from '@/components/ui'
import ModalsContainer from '@/components/ModalsContainer.vue'

const route = useRoute()
const router = useRouter()
const { isMobile } = useMediaQuery()

const isGuestRoute = computed(() => route.meta.guest === true)

// 未登录直接跳登录页（在渲染前执行，避免侧边栏闪烁）
if (!localStorage.getItem('auth_token') && !isGuestRoute.value) {
  router.replace('/login')
}
</script>

<template>
  <!-- 登录/注册 → 全屏无布局 -->
  <template v-if="isGuestRoute">
    <router-view />
    <Toast />
  </template>

  <!-- 正常布局 -->
  <template v-else>
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
  </template>

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
