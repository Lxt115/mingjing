<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { AgentForm, Agent, KnowledgeBase, Voice, Device } from '@/types'
import { useModal } from '@/composables'
import { useAgentsStore, useUiStore } from '@/store'
import { apiService } from '@/services'
import { Switch } from '@/components/ui'

const { close } = useModal()
const agentsStore = useAgentsStore()
const ui = useUiStore()

const editId = computed(() => ui.modalData.agentId as string | undefined)
const isCreate = computed(() => !editId.value)

const agentName = ref('')
const agentEmoji = ref('🤖')
const emojiPickerOpen = ref(false)
const systemPrompt = ref('')
const templatesOpen = ref(false)
const voiceId = ref<string | null>(null)
const knowledgeIds = ref<string[]>([])
const deviceIds = ref<string[]>([])
const saving = ref(false)

const emojiList = [
  '😊',
  '😄',
  '🥰',
  '😎',
  '🤗',
  '😇',
  '😂',
  '🤓',
  '😜',
  '🤔',
  '😏',
  '😤',
  '🥺',
  '😴',
  '🥳',
  '😍',
  '🐶',
  '🐱',
  '🦊',
  '🐻',
  '🐼',
  '🐰',
  '🐨',
  '🐸',
  '🦄',
  '🦋',
  '🐝',
  '🐙',
  '🦉',
  '🐳',
  '🐲',
  '🐥',
  '🎮',
  '📚',
  '🎨',
  '🎵',
  '🎬',
  '🔮',
  '💡',
  '🚀',
  '🌸',
  '🍀',
  '🌙',
  '⭐',
  '💎',
  '🎭',
  '🧸',
  '🎪',
  '🤖',
  '👻',
  '🧚',
  '🧙',
  '🦸',
  '👸',
  '🤴',
  '🧑‍🚀',
  '💂',
  '🕵️',
  '👩‍🔬',
  '👨‍🍳',
  '🧑‍🎤',
  '👩‍🏫',
  '👨‍💻',
  '🦹',
]

const wordCount = computed(() => systemPrompt.value.length)
const wordCountClass = computed(() =>
  wordCount.value > 500
    ? 'text-[var(--coral)] bg-[#fff0f0]'
    : wordCount.value > 350
      ? 'text-[var(--amber)] bg-[#fff8e6]'
      : 'text-[var(--text3)] bg-[var(--bg2)]',
)

const activeModalTab = ref<'persona' | 'kb' | 'device'>('persona')

const availableKbs = ref<KnowledgeBase[]>([])
const kbsLoading = ref(false)
const availableVoices = ref<Voice[]>([])
const availableDevices = ref<Device[]>([])

async function loadKnowledgeBases() {
  if (availableKbs.value.length > 0) return
  kbsLoading.value = true
  try {
    const res = await apiService.knowledge.getList()
    availableKbs.value = res.data
  } catch {
    /* ignore */
  } finally {
    kbsLoading.value = false
  }
}

async function loadVoices() {
  if (availableVoices.value.length > 0) return
  try {
    const res = await apiService.voices.getList()
    availableVoices.value = res.data
  } catch {
    /* ignore */
  }
}

async function loadDevices() {
  if (availableDevices.value.length > 0) return
  try {
    const res = await apiService.devices.getList()
    availableDevices.value = res.data
  } catch {
    /* ignore */
  }
}

function initForm() {
  if (isCreate.value) {
    agentName.value = ''
    agentEmoji.value = '🤖'
    systemPrompt.value = ''
    voiceId.value = null
    knowledgeIds.value = []
    deviceIds.value = []
  } else {
    const agent = agentsStore.agents.find((a) => a.id === editId.value)
    if (agent) {
      agentName.value = agent.name
      agentEmoji.value = agent.emoji || '🤖'
      systemPrompt.value = agent.systemPrompt
      voiceId.value = agent.voiceId
      knowledgeIds.value = [...agent.knowledgeIds]
      deviceIds.value = [...agent.boundDeviceIds]
    }
  }
  templatesOpen.value = false
}

function selectEmoji(emoji: string) {
  agentEmoji.value = emoji
  emojiPickerOpen.value = false
}

function applyTemplate(key: string) {
  const tpl = agentsStore.promptTemplates.find((t) => t.key === key)
  if (tpl) {
    systemPrompt.value = tpl.text
    templatesOpen.value = false
  }
}

function toggleKbId(kbId: string, val: boolean) {
  if (val) {
    if (!knowledgeIds.value.includes(kbId)) knowledgeIds.value = [...knowledgeIds.value, kbId]
  } else {
    knowledgeIds.value = knowledgeIds.value.filter((id) => id !== kbId)
  }
}

function toggleDeviceId(devId: string, val: boolean) {
  if (val) {
    if (!deviceIds.value.includes(devId)) deviceIds.value = [...deviceIds.value, devId]
  } else {
    deviceIds.value = deviceIds.value.filter((id) => id !== devId)
  }
}

function getDeviceLabel(dev: Device): string {
  if (dev.boundAgentId && dev.boundAgentId !== editId.value) {
    const other = agentsStore.agents.find((a) => a.id === dev.boundAgentId)
    return other ? `已绑定：${other.name}` : '已绑定'
  }
  return ''
}

async function saveConfig() {
  saving.value = true
  try {
    const form: AgentForm = {
      name: agentName.value,
      emoji: agentEmoji.value,
      description: '',
      systemPrompt: systemPrompt.value,
      voiceId: voiceId.value,
      knowledgeIds: knowledgeIds.value,
      deviceIds: deviceIds.value,
      tags: [],
    }
    if (isCreate.value) {
      await agentsStore.createAgent(form)
    } else {
      await agentsStore.updateAgent(editId.value!, form)
    }
    close()
    ui.showToast('✅ 配置已保存！')
  } catch (e) {
    ui.showToast(e instanceof Error ? e.message : '❌ 保存失败', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadKnowledgeBases()
  loadVoices()
  loadDevices()
})
initForm()
</script>

<template>
  <div class="flex flex-col max-h-[85vh]">
    <div class="flex gap-0.5 border-b border-[var(--border)] px-0 -mx-7 px-7">
      <button
        v-for="tab in [
          { id: 'persona' as const, label: '🎭 人设' },
          { id: 'kb' as const, label: '📚 知识库' },
          { id: 'device' as const, label: '📱 设备' },
        ]"
        :key="tab.id"
        :class="[
          'py-3 px-[18px] text-[13px] font-bold cursor-pointer border-b-2 transition-all duration-200 bg-transparent -mb-px',
          activeModalTab === tab.id
            ? 'text-[var(--coral)] border-[var(--coral)]'
            : 'text-[var(--text3)] border-transparent',
        ]"
        @click="activeModalTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="overflow-y-auto flex-1 pt-5">
      <!--  人设 -->
      <div v-show="activeModalTab === 'persona'">
        <div class="flex flex-col items-center mb-5">
          <div class="relative">
            <button
              class="w-[72px] h-[72px] rounded-2xl flex items-center justify-center text-[38px] bg-[var(--bg)] border-[1.5px] border-[var(--border)] cursor-pointer transition-all duration-200 hover:border-[var(--coral)] hover:shadow-[0_4px_16px_rgba(255,107,107,.18)] hover:-translate-y-0.5"
              @click="emojiPickerOpen = !emojiPickerOpen"
            >
              {{ agentEmoji }}
            </button>
            <Transition name="picker-slide">
              <div
                v-if="emojiPickerOpen"
                class="absolute top-full left-1/2 -translate-x-1/2 mt-2 p-3 bg-[var(--surface)] border border-[var(--border)] rounded-[var(--radius-md)] shadow-[var(--shadow-lg)] grid grid-cols-8 gap-1 z-10 w-[316px]"
              >
                <button
                  v-for="emoji in emojiList"
                  :key="emoji"
                  :class="[
                    'w-9 h-9 flex items-center justify-center text-lg rounded-lg cursor-pointer border-[1.5px] transition-all duration-150 bg-transparent',
                    agentEmoji === emoji
                      ? 'border-[var(--coral)] bg-[rgba(255,107,107,.08)] scale-110'
                      : 'border-transparent hover:bg-[var(--bg)] hover:border-[var(--border)]',
                  ]"
                  @click="selectEmoji(emoji)"
                >
                  {{ emoji }}
                </button>
              </div>
            </Transition>
          </div>
          <div class="text-[11px] text-[var(--text3)] font-semibold mt-2">点击更换头像</div>
        </div>

        <div class="mb-[18px]">
          <label
            class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
            >伙伴名称</label
          >
          <input
            v-model="agentName"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
            placeholder="给角色起个名字"
          />
        </div>

        <div class="mb-[18px]">
          <div class="flex justify-between items-center mb-2">
            <label class="text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase"
              >系统提示词</label
            >
            <button
              class="text-xs font-extrabold text-[var(--indigo)] bg-[#eef0fc] px-3 py-1 rounded-full cursor-pointer border-none transition-all duration-200 hover:bg-[#dde1f8]"
              @click="templatesOpen = !templatesOpen"
            >
              📋 模板
            </button>
          </div>

          <div v-if="templatesOpen" class="flex flex-col gap-1.5 mb-3">
            <div
              v-for="tpl in agentsStore.promptTemplates"
              :key="tpl.key"
              class="flex items-center gap-2.5 px-3 py-2.5 bg-[var(--bg)] rounded-[var(--radius-sm)] cursor-pointer border-[1.5px] border-transparent transition-all duration-150 hover:border-[var(--indigo-lt)] hover:bg-[#eef0fc]"
              @click="applyTemplate(tpl.key)"
            >
              <div
                class="w-[34px] h-[34px] rounded-[10px] bg-white flex items-center justify-center text-lg shrink-0 shadow-[var(--shadow-sm)]"
              >
                {{ tpl.icon }}
              </div>
              <div>
                <div class="text-[13px] font-extrabold text-[var(--text1)]">{{ tpl.name }}</div>
                <div class="text-[11px] text-[var(--text3)] mt-px">{{ tpl.description }}</div>
              </div>
            </div>
          </div>

          <textarea
            v-model="systemPrompt"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 resize-none min-h-[100px] leading-relaxed focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
            placeholder="描述角色的名字、性格、说话风格和专长方向…"
          />

          <div class="flex justify-between items-center mt-1.5">
            <span class="text-[11px] text-[var(--text3)] font-semibold"
              >💡 建议描述：名字、性格、说话方式、擅长话题</span
            >
            <span
              :class="['text-[11px] font-extrabold px-2 py-0.5 rounded-[10px]', wordCountClass]"
            >
              {{ wordCount }} 字
            </span>
          </div>
        </div>

        <div class="mb-[18px]">
          <label
            class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2"
            >音色选择</label
          >
          <select
            v-model="voiceId"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none cursor-pointer transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
          >
            <option :value="null">默认音色</option>
            <option v-for="v in availableVoices" :key="v.id" :value="v.id">
              {{ v.name }} · {{ v.description }} · {{ v.providerVoiceName }}
            </option>
          </select>
        </div>
      </div>

      <!--  知识库 -->
      <div v-show="activeModalTab === 'kb'">
        <div v-if="kbsLoading" class="text-center text-[var(--text3)] text-sm py-8">加载中…</div>
        <div
          v-else-if="availableKbs.length === 0"
          class="bg-[var(--bg)] rounded-[var(--radius-md)] text-center py-8 px-4"
        >
          <div class="text-[32px] mb-2">📭</div>
          <div class="text-sm font-bold text-[var(--text2)] mb-1">暂无可用知识库</div>
          <div class="text-xs text-[var(--text3)]">去「知识库」页面先上传你的文档吧</div>
        </div>
        <div
          v-else
          class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden"
        >
          <div
            v-for="kb in availableKbs"
            :key="kb.id"
            class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)] last:border-b-0"
            :class="kb.isEnabled ? '' : 'opacity-50'"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0"
                :style="{ background: kb.isSystem ? '#e8fdf5' : '#eef0fc' }"
              >
                {{ kb.isSystem ? '🧠' : '📄' }}
              </div>
              <div>
                <div class="text-sm font-bold text-[var(--text1)]">
                  {{ kb.name }}
                  <span v-if="!kb.isEnabled" class="text-[10px] text-[var(--text3)]">(已禁用)</span>
                </div>
                <div class="text-xs text-[var(--text3)] mt-px">
                  {{ kb.itemCount }} {{ kb.itemUnit }} · {{ kb.description }}
                </div>
              </div>
            </div>
            <Switch
              :model-value="knowledgeIds.includes(kb.id)"
              :disabled="!kb.isEnabled"
              @update:model-value="(val: boolean) => toggleKbId(kb.id, val)"
            />
          </div>
        </div>
      </div>

      <!--  设备 -->
      <div v-show="activeModalTab === 'device'">
        <div
          v-if="availableDevices.length === 0"
          class="bg-[var(--bg)] rounded-[var(--radius-md)] text-center py-8 px-4"
        >
          <div class="text-[32px] mb-2">📱</div>
          <div class="text-sm font-bold text-[var(--text2)] mb-1">暂无设备</div>
          <div class="text-xs text-[var(--text3)]">去「设备管理」页面先添加设备吧</div>
        </div>
        <div
          v-else
          class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden"
        >
          <div
            v-for="dev in availableDevices"
            :key="dev.id"
            class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)] last:border-b-0"
          >
            <div class="flex items-center gap-3">
              <div
                class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0"
                :style="{ background: dev.status === 'online' ? '#e8fdf5' : '#fff0f0' }"
              >
                📱
              </div>
              <div>
                <div class="text-sm font-bold text-[var(--text1)]">{{ dev.name }}</div>
                <div class="text-xs text-[var(--text3)] mt-px">
                  <span :class="dev.status === 'online' ? 'text-[var(--teal)]' : ''">{{
                    dev.status === 'online' ? '●' : '○'
                  }}</span>
                  {{ getDeviceLabel(dev) || dev.mac }}
                </div>
              </div>
            </div>
            <Switch
              :model-value="deviceIds.includes(dev.id)"
              @update:model-value="(val: boolean) => toggleDeviceId(dev.id, val)"
            />
          </div>
        </div>
        <div class="text-[11px] text-[var(--text3)] mt-2 font-semibold">
          💡 选中设备即绑定到当前角色，取消选中则解绑。若设备已绑定其他角色，选中后将自动切换。
        </div>
      </div>
    </div>

    <div class="flex gap-3 pt-4 border-t border-[var(--border)] mt-2">
      <button
        class="flex-1 h-11 rounded-[var(--radius-sm)] bg-[var(--bg2)] text-[var(--text2)] border-none text-sm font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--border)]"
        @click="close"
      >
        取消
      </button>
      <button
        class="flex-1 h-11 rounded-[var(--radius-sm)] bg-[var(--coral)] text-white border-none text-sm font-extrabold cursor-pointer transition-all duration-200 hover:bg-[var(--coral-dk)] disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="saving"
        @click="saveConfig"
      >
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.picker-slide-enter-active,
.picker-slide-leave-active {
  transition: all 0.2s ease;
}
.picker-slide-enter-from,
.picker-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
