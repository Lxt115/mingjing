import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserProfile } from '@/types'
import { apiService } from '@/services'

export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile>({
    name: '明境用户',
    userId: 'MJ-20240405',
    version: '4.0.0',
    totalConversations: 127,
    totalHours: 43,
    boundDeviceCount: 2,
    avatarEmoji: '👨‍👧',
  })

  const loading = ref(false)
  const error = ref<string | null>(null)
  const notificationEnabled = ref(true)

  async function toggleNotification() {
    const next = !notificationEnabled.value
    try {
      await apiService.user.updateNotification(next)
      notificationEnabled.value = next
    } catch (e) {
      error.value = e instanceof Error ? e.message : '通知设置更新失败'
    }
  }

  return {
    profile,
    loading,
    error,
    notificationEnabled,
    toggleNotification,
  }
})
