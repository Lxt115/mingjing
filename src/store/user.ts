import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserProfile } from '@/types'
import { apiService } from '@/services'

export const useUserStore = defineStore('user', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const userId = ref<string | null>(localStorage.getItem('user_id'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const profile = ref<UserProfile>({
    name: '明境用户',
    userId: '',
    version: '4.0.0',
    totalConversations: 0,
    totalHours: 0,
    boundDeviceCount: 0,
    avatarEmoji: '👨‍👧',
  })

  const loading = ref(false)
  const error = ref<string | null>(null)
  const notificationEnabled = ref(true)

  const isLoggedIn = computed(() => !!token.value)

  async function login(name: string, pwd: string) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.auth.login(name, pwd)
      token.value = res.data.token
      userId.value = res.data.userId
      username.value = name
      localStorage.setItem('auth_token', res.data.token)
      localStorage.setItem('user_id', res.data.userId)
      localStorage.setItem('username', name)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function register(name: string, pwd: string) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.auth.register(name, pwd)
      token.value = res.data.token
      userId.value = res.data.userId
      username.value = name
      localStorage.setItem('auth_token', res.data.token)
      localStorage.setItem('user_id', res.data.userId)
      localStorage.setItem('username', name)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : '注册失败'
      return false
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = null
    userId.value = null
    username.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('username')
  }

  async function fetchProfile() {
    try {
      const res = await apiService.user.getProfile()
      profile.value = res.data
    } catch {
      // ignore
    }
  }

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
    token,
    userId,
    username,
    profile,
    loading,
    error,
    isLoggedIn,
    notificationEnabled,
    login,
    register,
    logout,
    fetchProfile,
    toggleNotification,
  }
})
