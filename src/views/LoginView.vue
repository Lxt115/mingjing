<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'

const router = useRouter()
const userStore = useUserStore()

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const submitting = ref(false)

async function submit() {
  if (!username.value || !password.value) return
  submitting.value = true
  try {
    let ok: boolean
    if (isLogin.value) {
      ok = await userStore.login(username.value, password.value)
    } else {
      if (password.value.length < 6) {
        userStore.error = '密码至少 6 位'
        return
      }
      ok = await userStore.register(username.value, password.value)
    }
    if (ok) {
      await userStore.fetchProfile()
      router.push('/agents')
    }
  } finally {
    submitting.value = false
  }
}

function toggleMode() {
  isLogin.value = !isLogin.value
  userStore.error = null
}
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#fdf2f2] via-white to-[#f0f4ff] px-4"
  >
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div
          class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] shadow-lg shadow-[rgba(255,107,107,.25)] mb-4"
        >
          <svg
            class="w-9 h-9 text-white"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="8" r="4" />
            <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
            <path d="M16 3.5a4 4 0 0 1 0 7" />
            <path d="M8 3.5a4 4 0 0 0 0 7" />
          </svg>
        </div>
        <h1 class="text-[28px] font-extrabold text-[var(--text1)] tracking-tight">明境</h1>
        <p class="text-sm text-[var(--text3)] mt-1">AI 陪伴管理平台</p>
      </div>

      <!-- Form Card -->
      <div
        class="bg-white rounded-2xl shadow-lg shadow-black/[.04] p-6 border border-[var(--border)]"
      >
        <h2 class="text-lg font-extrabold text-[var(--text1)] mb-5">
          {{ isLogin ? '登录' : '注册' }}
        </h2>

        <!-- Error -->
        <div
          v-if="userStore.error"
          class="mb-4 p-3 rounded-[var(--radius-sm)] bg-[#fff0f0] text-[var(--coral)] text-xs font-bold"
        >
          {{ userStore.error }}
        </div>

        <!-- Username -->
        <div class="mb-4">
          <label
            class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
          >
            用户名
          </label>
          <input
            v-model="username"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
            placeholder="请输入用户名"
            maxlength="50"
          />
        </div>

        <!-- Password -->
        <div class="mb-6">
          <label
            class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
          >
            密码
          </label>
          <input
            v-model="password"
            type="password"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
            placeholder="请输入密码"
            maxlength="100"
            @keyup.enter="submit"
          />
          <p v-if="!isLogin" class="text-xs text-[var(--text3)] mt-1">密码至少 6 位</p>
        </div>

        <!-- Submit -->
        <button
          class="w-full py-3 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          :disabled="submitting || !username || !password"
          @click="submit"
        >
          {{ submitting ? '请稍候…' : isLogin ? '登录' : '注册' }}
        </button>

        <!-- Toggle -->
        <p class="mt-4 text-center text-sm text-[var(--text3)]">
          {{ isLogin ? '没有账号？' : '已有账号？' }}
          <button
            class="text-[var(--coral)] font-bold bg-transparent border-none cursor-pointer hover:underline"
            @click="toggleMode"
          >
            {{ isLogin ? '立即注册' : '去登录' }}
          </button>
        </p>
      </div>
    </div>
  </div>
</template>
