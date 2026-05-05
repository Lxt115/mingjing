<script setup lang="ts">
import { ref, computed } from 'vue'
import type { AgentForm, Agent } from '@/types'
import { useModal } from '@/composables'
import { useAgentsStore, useUiStore } from '@/store'
import { InfoTip, Switch } from '@/components/ui'

const { close } = useModal()
const agentsStore = useAgentsStore()
const ui = useUiStore()

const editId = computed(() => ui.modalData.agentId as string | undefined)
const isCreate = computed(() => !editId.value)

const agentName = ref('')
const systemPrompt = ref('')
const templatesOpen = ref(false)
const voiceId = ref<string | null>(null)
const knowledgeIds = ref<string[]>([])
const speed = ref(55)
const volume = ref(80)
const pitch = ref(60)
const saving = ref(false)

const wordCount = computed(() => systemPrompt.value.length)
const wordCountClass = computed(() =>
  wordCount.value > 500 ? 'text-[var(--coral)] bg-[#fff0f0]' : wordCount.value > 350 ? 'text-[var(--amber)] bg-[#fff8e6]' : 'text-[var(--text3)] bg-[var(--bg2)]',
)

const activeModalTab = ref<'persona' | 'voice' | 'kb'>('persona')

const builtInKnowledges = [
  { id: 'kb-1', name: '小学数学题库', desc: '3,240 道题', icon: '📗', bg: '#e8fdf5' },
  { id: 'kb-2', name: '英语绘本词汇', desc: '1,500 词', icon: '📘', bg: '#eef0fc' },
  { id: 'kb-3', name: '经典童话故事', desc: '328 篇', icon: '📙', bg: '#fff8e6' },
]

function initForm() {
  if (isCreate.value) {
    agentName.value = ''
    systemPrompt.value = ''
    voiceId.value = null
    knowledgeIds.value = []
    speed.value = 55
    volume.value = 80
    pitch.value = 60
  } else {
    const agent = agentsStore.agents.find((a) => a.id === editId.value)
    if (agent) {
      agentName.value = agent.name
      systemPrompt.value = agent.systemPrompt
      voiceId.value = agent.voiceId
      knowledgeIds.value = [...agent.knowledgeIds]
      speed.value = agent.speed
      volume.value = agent.volume
      pitch.value = agent.pitch
    }
  }
  templatesOpen.value = false
}

function applyTemplate(key: string) {
  const tpl = agentsStore.promptTemplates.find((t) => t.key === key)
  if (tpl) {
    systemPrompt.value = tpl.text
    templatesOpen.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const form: AgentForm = {
      name: agentName.value,
      description: '',
      systemPrompt: systemPrompt.value,
      voiceId: voiceId.value,
      knowledgeIds: knowledgeIds.value,
      speed: speed.value,
      volume: volume.value,
      pitch: pitch.value,
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

initForm()
</script>

<template>
  <div class="flex flex-col max-h-[85vh]">
    <div class="flex gap-0.5 border-b border-[var(--border)] px-0 -mx-7 px-7">
      <button
        v-for="tab in [
          { id: 'persona' as const, label: '🎭 人设' },
          { id: 'voice' as const, label: '🔊 声音' },
          { id: 'kb' as const, label: '📚 知识库' },
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
      <div v-show="activeModalTab === 'persona'">
        <div class="mb-[18px]">
          <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">伙伴名称</label>
          <input
            v-model="agentName"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none transition-all duration-200 focus:border-[var(--coral)] focus:shadow-[0_0_0_3px_rgba(255,107,107,.1)] focus:bg-white"
            placeholder="给角色起个名字"
          />
        </div>

        <div class="mb-[18px]">
          <div class="flex justify-between items-center mb-2">
            <label class="text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase">系统提示词</label>
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
              <div class="w-[34px] h-[34px] rounded-[10px] bg-white flex items-center justify-center text-lg shrink-0 shadow-[var(--shadow-sm)]">
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
            <span class="text-[11px] text-[var(--text3)] font-semibold">💡 建议描述：名字、性格、说话方式、擅长话题</span>
            <span
              :class="[
                'text-[11px] font-extrabold px-2 py-0.5 rounded-[10px]',
                wordCountClass,
              ]"
            >
              {{ wordCount }} 字
            </span>
          </div>
        </div>
      </div>

      <div v-show="activeModalTab === 'voice'">
        <div class="mb-[18px]">
          <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">音色选择</label>
          <select
            v-model="voiceId"
            class="w-full p-[11px] border-[1.5px] border-[var(--border)] rounded-[var(--radius-sm)] text-sm text-[var(--text1)] bg-[var(--bg)] outline-none cursor-pointer"
          >
            <option :value="null">默认音色</option>
            <option value="voice-f-1">甜美女声 A</option>
            <option value="voice-m-1">活泼男声 B</option>
            <option value="voice-f-2">温柔女声 C</option>
            <option value="voice-f-3">卡通音色 D</option>
          </select>
        </div>

        <div class="mb-[18px]">
          <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">语速调节</label>
          <input
            v-model.number="speed"
            type="range"
            min="0"
            max="100"
            class="w-full h-[5px] rounded-[3px] bg-[var(--bg2)] outline-none appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--coral)] [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-[0_2px_8px_rgba(255,107,107,.35)]"
          />
          <div class="flex justify-between text-xs text-[var(--text3)] mt-1.5 font-semibold">
            <span>🐢 慢速</span>
            <span>🐇 快速</span>
          </div>
        </div>

        <div class="mb-[18px]">
          <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">音量大小</label>
          <input
            v-model.number="volume"
            type="range"
            min="0"
            max="100"
            class="w-full h-[5px] rounded-[3px] bg-[var(--bg2)] outline-none appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--coral)] [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-[0_2px_8px_rgba(255,107,107,.35)]"
          />
          <div class="flex justify-between text-xs text-[var(--text3)] mt-1.5 font-semibold">
            <span>🔇 安静</span>
            <span>🔊 响亮</span>
          </div>
        </div>

        <div class="mb-[18px]">
          <label class="block text-xs font-extrabold text-[var(--text2)] tracking-[.5px] uppercase mb-2">音调高低</label>
          <input
            v-model.number="pitch"
            type="range"
            min="0"
            max="100"
            class="w-full h-[5px] rounded-[3px] bg-[var(--bg2)] outline-none appearance-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[var(--coral)] [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:shadow-[0_2px_8px_rgba(255,107,107,.35)]"
          />
          <div class="flex justify-between text-xs text-[var(--text3)] mt-1.5 font-semibold">
            <span>低沉</span>
            <span>高亢</span>
          </div>
        </div>

        <InfoTip>
          💡 调整完成后点击「试听」可以预览效果
        </InfoTip>
      </div>

      <div v-show="activeModalTab === 'kb'">
        <div class="bg-[var(--surface)] rounded-[var(--radius-md)] border border-[var(--border)] shadow-[var(--shadow-sm)] overflow-hidden">
          <div
            v-for="kb in builtInKnowledges"
            :key="kb.id"
            class="flex justify-between items-center px-[18px] py-3.5 border-b border-[var(--border)] last:border-b-0"
          >
            <div class="flex items-center gap-3">
              <div class="w-[34px] h-[34px] rounded-[10px] flex items-center justify-center text-base shrink-0" :style="{ background: kb.bg }">
                {{ kb.icon }}
              </div>
              <div>
                <div class="text-sm font-bold text-[var(--text1)]">{{ kb.name }}</div>
                <div class="text-xs text-[var(--text3)] mt-px">{{ kb.desc }}</div>
              </div>
            </div>
            <Switch
              :model-value="knowledgeIds.includes(kb.id)"
              @update:model-value="(val: boolean) => val ? knowledgeIds.push(kb.id) : knowledgeIds = knowledgeIds.filter(id => id !== kb.id)"
            />
          </div>
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
