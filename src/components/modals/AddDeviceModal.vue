<script setup lang="ts">
import { ref } from 'vue'
import { useModal } from '@/composables'
import { useDevicesStore, useUiStore } from '@/store'
import { InfoTip } from '@/components/ui'

const { close } = useModal()
const devicesStore = useDevicesStore()
const ui = useUiStore()

const step = ref<'guide' | 'input'>('guide')
const code = ref('')
const submitting = ref(false)

async function startConfig() {
  step.value = 'input'
}

async function submitCode() {
  if (code.value.length !== 4) {
    ui.showToast('请输入 4 位配对码', 'error')
    return
  }
  submitting.value = true
  try {
    await devicesStore.bindDevice(code.value)
    ui.closeModal()
    ui.showToast('✅ 设备绑定成功！')
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 绑定失败', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div>
    <!-- Step 1: 引导 -->
    <div v-if="step === 'guide'">
      <InfoTip>确保设备已开机且处于正常联网状态</InfoTip>
      <div
        class="mt-4 p-4 bg-[var(--bg2)] rounded-[var(--radius-sm)] text-sm text-[var(--text2)] leading-6"
      >
        <p class="font-bold text-[var(--text1)] mb-2">操作步骤：</p>
        <ol class="list-decimal pl-4 space-y-2">
          <li><strong>双击</strong>设备说话按钮，进入配网模式</li>
          <li>
            手机打开 WiFi 设置，连接热点 <strong class="text-[var(--coral)]">Aidoll-Config</strong>
          </li>
          <li>
            浏览器访问<br />
            <code
              class="inline-block mt-1 px-2 py-0.5 bg-[var(--bg)] rounded text-xs font-bold text-[var(--coral)] select-all"
              >http://192.168.4.1</code
            >
          </li>
          <li>
            在配网页输入你的 <strong>WiFi 名称</strong>和<strong>密码</strong>，点击"保存并连接"
          </li>
          <li>设备联网后会<strong>语音播报 4 位配对码</strong></li>
          <li>记下配对码，点击下方"开始输入"</li>
        </ol>
      </div>
    </div>

    <!-- Step 2: 输入配对码 -->
    <div v-else>
      <InfoTip>设备会循环语音播报配对码，请仔细听</InfoTip>
      <div class="mt-4">
        <label
          class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
          >配对码 *</label
        >
        <input
          v-model="code"
          class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-lg text-center tracking-[.5em] font-bold text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
          placeholder="4 位数字"
          maxlength="4"
          inputmode="numeric"
          @keyup.enter="submitCode"
        />
      </div>
    </div>

    <!-- 按钮 -->
    <div class="flex gap-3 mt-6">
      <button
        class="flex-1 py-3 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text1)] border-none text-sm font-bold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close()"
      >
        取消
      </button>
      <button
        v-if="step === 'guide'"
        class="flex-1 py-3 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)]"
        @click="startConfig()"
      >
        开始输入
      </button>
      <button
        v-else
        class="flex-1 py-3 bg-gradient-to-br from-[var(--coral)] to-[#FF8E53] text-white border-none rounded-[var(--radius-sm)] text-sm font-extrabold cursor-pointer shadow-[0_3px_12px_rgba(255,107,107,.3)] transition-all duration-200 hover:-translate-y-px hover:shadow-[0_5px_16px_rgba(255,107,107,.4)]"
        :disabled="submitting"
        @click="submitCode()"
      >
        {{ submitting ? '绑定中…' : '确认绑定' }}
      </button>
    </div>
  </div>
</template>
