<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUiStore, useUserStore } from '@/store'
import { useMediaQuery } from '@/composables'
import { Switch } from '@/components/ui'

const ui = useUiStore()
const user = useUserStore()
const router = useRouter()
const { isMobile } = useMediaQuery()
const memoryEnabled = ref(true)

function navigateTo(path: string) {
  router.push(path)
}

function toggleMemory() {
  memoryEnabled.value = !memoryEnabled.value
  ui.showToast(memoryEnabled.value ? '🧠 记忆已开启' : '🔒 记忆已关闭')
}
</script>

<template>
  <!-- Desktop Layout -->
  <div
    v-if="!isMobile"
    class="animate-[fadeIn_.25s_ease] grid grid-cols-[320px_1fr] gap-5 items-start"
  >
    <div>
      <div
        class="relative overflow-hidden bg-gradient-to-br from-[var(--indigo)] to-[var(--teal)] rounded-[var(--radius-lg)] p-7 mb-5 shadow-[0_8px_32px_rgba(92,107,192,.2)]"
      >
        <div
          class="absolute -top-[60px] -right-[60px] w-[200px] h-[200px] rounded-full bg-white/8 pointer-events-none"
        ></div>
        <div
          class="absolute -bottom-10 -left-5 w-[120px] h-[120px] rounded-full bg-white/6 pointer-events-none"
        ></div>

        <div
          class="w-[72px] h-[72px] rounded-[22px] bg-white/20 flex items-center justify-center text-4xl mb-3.5 relative z-[1] border-2 border-white/30"
        >
          {{ user.profile.avatarEmoji }}
        </div>
        <div class="text-[22px] font-black text-white mb-1 relative z-[1]">
          {{ user.profile.name }}
        </div>
        <div class="text-xs text-white/60 relative z-[1] mb-5">
          ID: {{ user.profile.userId }} · v{{ user.profile.version }}
        </div>

        <div class="grid grid-cols-3 gap-3 relative z-[1]">
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.totalConversations }}</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">对话次数</div>
          </div>
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.totalHours }}h</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">陪伴时长</div>
          </div>
          <div class="bg-white/15 rounded-[10px] py-3 px-2.5 text-center">
            <div class="text-xl font-black text-white">{{ user.profile.boundDeviceCount }}</div>
            <div class="text-[11px] text-white/70 mt-0.5 font-semibold">绑定设备</div>
          </div>
        </div>
      </div>
    </div>

    <div>
      <div class="mb-5">
        <div
          class="text-[11px] font-extrabold text-[var(--text3)] tracking-[.8px] uppercase mb-2.5 pl-0.5"
        >
          账号设置
        </div>
        <div
          class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden"
        >
          <div
            class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)] cursor-pointer transition-colors duration-150 hover:bg-[var(--bg)]"
            @click="ui.showToast('功能开发中…')"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#e8fdf5]"
              >
                🔒
              </div>
              <div class="text-sm font-bold text-[var(--text1)]">隐私设置</div>
            </div>
            <span class="text-[var(--text3)] text-base">›</span>
          </div>

          <div
            class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)]"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#fff8e6]"
              >
                🔔
              </div>
              <div class="text-sm font-bold text-[var(--text1)]">消息通知</div>
            </div>
            <Switch
              :model-value="user.notificationEnabled"
              @update:model-value="user.toggleNotification"
            />
          </div>

          <div
            class="flex justify-between items-center px-[18px] py-3.5 cursor-pointer transition-colors duration-150 hover:bg-[var(--bg)]"
            @click="ui.showToast('当前版本 v4.0.0')"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0 bg-[#eef0fc]"
              >
                ℹ️
              </div>
              <div>
                <div class="text-sm font-bold text-[var(--text1)]">关于明境</div>
                <div class="text-xs text-[var(--text3)] mt-px">
                  版本 v{{ user.profile.version }}
                </div>
              </div>
            </div>
            <span class="text-[var(--text3)] text-base">›</span>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Layout -->
  <div v-else class="flex flex-col h-full">
    <div
      class="profile-hero bg-gradient-to-br from-[var(--indigo)] to-[var(--teal)] pt-7 pb-8 px-5 relative overflow-hidden"
    >
      <div
        class="absolute -top-10 -right-10 w-[180px] h-[180px] rounded-full bg-white/10 pointer-events-none"
      ></div>
      <div class="flex items-center gap-3.5 mb-5 relative z-[1]">
        <div
          class="w-16 h-16 rounded-[22px] bg-white/20 flex items-center justify-center text-[32px] border-[2px] border-white/40"
        >
          {{ user.profile.avatarEmoji }}
        </div>
        <div>
          <div class="text-xl font-black text-white">{{ user.profile.name }}</div>
          <div class="text-xs text-white/70 mt-0.5 font-semibold">
            ID: {{ user.profile.userId }}
          </div>
        </div>
      </div>
      <div class="flex gap-0 bg-white/15 rounded-[var(--radius-md)] overflow-hidden relative z-[1]">
        <div class="flex-1 py-3 text-center relative">
          <div class="text-xl font-black text-white">{{ user.profile.totalConversations }}</div>
          <div class="text-[10px] text-white/75 font-bold tracking-[.5px] mt-0.5">对话次数</div>
          <div class="absolute right-0 top-[20%] bottom-[20%] w-px bg-white/25"></div>
        </div>
        <div class="flex-1 py-3 text-center relative">
          <div class="text-xl font-black text-white">{{ user.profile.totalHours }}h</div>
          <div class="text-[10px] text-white/75 font-bold tracking-[.5px] mt-0.5">陪伴时长</div>
          <div class="absolute right-0 top-[20%] bottom-[20%] w-px bg-white/25"></div>
        </div>
        <div class="flex-1 py-3 text-center">
          <div class="text-xl font-black text-white">{{ user.profile.boundDeviceCount }}</div>
          <div class="text-[10px] text-white/75 font-bold tracking-[.5px] mt-0.5">绑定设备</div>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto">
      <div
        class="section-label text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase pt-5 pb-2 px-4"
      >
        设备与绑定
      </div>
      <div
        class="card-mobile bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mx-4 mb-3 overflow-hidden"
      >
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 border-b border-[var(--border)] cursor-pointer active:bg-[var(--bg)]"
          @click="navigateTo('/devices')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#e8fdf5] flex items-center justify-center text-[15px] shrink-0"
            >
              📱
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">管理设备</div>
              <div class="text-xs text-[var(--text3)] mt-px">
                已绑定 {{ user.profile.boundDeviceCount }} 台 · 1 台在线
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1.5 text-[var(--text3)] text-sm">
            <span
              class="text-[10px] font-extrabold bg-[#e8fdf5] text-[var(--teal)] px-2 py-0.5 rounded-[20px]"
              >{{ user.profile.boundDeviceCount }} 台</span
            >
            <span>›</span>
          </div>
        </div>
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 cursor-pointer active:bg-[var(--bg)]"
          @click="ui.openModal('modal-add-device')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#fffbec] flex items-center justify-center text-[15px] shrink-0"
            >
              ➕
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">添加新设备</div>
              <div class="text-xs text-[var(--text3)] mt-px">通过验证码绑定</div>
            </div>
          </div>
          <span class="text-[var(--text3)] text-sm">›</span>
        </div>
      </div>

      <div
        class="section-label text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase pt-4 pb-2 px-4"
      >
        声音
      </div>
      <div
        class="card-mobile bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mx-4 mb-3 overflow-hidden"
      >
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 cursor-pointer active:bg-[var(--bg)]"
          @click="navigateTo('/voice-library')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#f0f4ff] flex items-center justify-center text-[15px] shrink-0"
            >
              🔊
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">声音库</div>
              <div class="text-xs text-[var(--text3)] mt-px">
                系统音色 · 克隆我的声音 · 声纹识别
              </div>
            </div>
          </div>
          <span class="text-[var(--text3)] text-sm">›</span>
        </div>
      </div>

      <div
        class="section-label text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase pt-4 pb-2 px-4"
      >
        知识库
      </div>
      <div
        class="card-mobile bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mx-4 mb-3 overflow-hidden"
      >
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 border-b border-[var(--border)] cursor-pointer active:bg-[var(--bg)]"
          @click="navigateTo('/knowledge')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#e8fdf5] flex items-center justify-center text-[15px] shrink-0"
            >
              📚
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">知识库管理</div>
              <div class="text-xs text-[var(--text3)] mt-px">2 个自定义 · 3 个系统</div>
            </div>
          </div>
          <span class="text-[var(--text3)] text-sm">›</span>
        </div>
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 cursor-pointer"
          @click="toggleMemory"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#fff8e6] flex items-center justify-center text-[15px] shrink-0"
            >
              🧠
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">记忆</div>
              <div class="text-xs text-[var(--text3)] mt-px">自动学习对话，形成个性化知识</div>
            </div>
          </div>
          <div
            class="toggle-mobile w-[46px] h-[26px] rounded-[13px] relative cursor-pointer transition-colors duration-250 shrink-0"
            :class="memoryEnabled ? 'bg-[var(--teal)]' : 'bg-[var(--bg2)]'"
          >
            <div
              class="absolute w-5 h-5 rounded-full bg-white top-[3px] shadow-[0_1px_4px_rgba(0,0,0,.2)] transition-transform duration-250"
              :class="memoryEnabled ? 'translate-x-5' : 'left-[3px]'"
            ></div>
          </div>
        </div>
      </div>

      <div
        class="section-label text-xs font-extrabold text-[var(--text3)] tracking-[.8px] uppercase pt-4 pb-2 px-4"
      >
        账号与设置
      </div>
      <div
        class="card-mobile bg-[var(--surface)] rounded-[var(--radius-md)] shadow-[var(--shadow-sm)] mx-4 mb-3 overflow-hidden"
      >
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 border-b border-[var(--border)] cursor-pointer active:bg-[var(--bg)]"
          @click="ui.showToast('功能开发中…')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#e8fdf5] flex items-center justify-center text-[15px] shrink-0"
            >
              🔒
            </div>
            <div class="text-sm font-bold text-[var(--text1)]">隐私设置</div>
          </div>
          <span class="text-[var(--text3)] text-sm">›</span>
        </div>
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 border-b border-[var(--border)] cursor-pointer"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#fff8e6] flex items-center justify-center text-[15px] shrink-0"
            >
              🔔
            </div>
            <div class="text-sm font-bold text-[var(--text1)]">消息通知</div>
          </div>
          <Switch
            :model-value="user.notificationEnabled"
            @update:model-value="user.toggleNotification"
          />
        </div>
        <div
          class="row-item flex items-center justify-between px-4 py-3.5 cursor-pointer active:bg-[var(--bg)]"
          @click="ui.showToast('当前版本 v4.0.0')"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="w-8 h-8 rounded-[10px] bg-[#eef0fc] flex items-center justify-center text-[15px] shrink-0"
            >
              ℹ️
            </div>
            <div>
              <div class="text-sm font-bold text-[var(--text1)]">关于明境</div>
              <div class="text-xs text-[var(--text3)] mt-px">版本 v{{ user.profile.version }}</div>
            </div>
          </div>
          <span class="text-[var(--text3)] text-sm">›</span>
        </div>
      </div>

      <div class="h-6 shrink-0"></div>
    </div>
  </div>
</template>

<style scoped></style>
