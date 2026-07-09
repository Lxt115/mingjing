import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Agent, AgentForm, PromptTemplate } from '@/types'
import { apiService } from '@/services'

export const useAgentsStore = defineStore('agents', () => {
  const agents = ref<Agent[]>([])
  const selectedAgentId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const promptTemplates: PromptTemplate[] = [
    {
      key: 'learning',
      name: '学习助手',
      description: '数学、英语、科普辅导',
      icon: '🧮',
      text: '你是一个活泼可爱的学习小伙伴，擅长数学和英语启蒙。用简单易懂的语言帮助6-12岁的小朋友学习，多用比喻和例子，保持鼓励和正面的态度。',
    },
    {
      key: 'story',
      name: '故事伙伴',
      description: '睡前故事、创意讲述',
      icon: '🌙',
      text: '你是一个温柔的故事大王，擅长讲述各种童话故事和睡前故事。语调温和，充满想象力，能根据孩子的喜好即兴创作故事。',
    },
    {
      key: 'companion',
      name: '情绪陪伴',
      description: '倾听、鼓励、情绪支持',
      icon: '💛',
      text: '你是一个情绪陪伴伙伴，善于倾听和鼓励。当孩子感到委屈、开心或困惑时，你能给予温暖的回应和积极的引导。',
    },
  ]

  const onlineAgents = computed(() => agents.value.filter((a) => a.status === 'online'))

  async function fetchAgents() {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.agents.getList()
      agents.value = res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '获取角色列表失败'
    } finally {
      loading.value = false
    }
  }

  async function createAgent(form: AgentForm) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.agents.create(form)
      agents.value.push(res.data)
      return res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '创建角色失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updateAgent(id: string, form: AgentForm) {
    loading.value = true
    error.value = null
    try {
      const res = await apiService.agents.update(id, form)
      const idx = agents.value.findIndex((a) => a.id === id)
      if (idx !== -1) agents.value[idx] = res.data
      return res.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : '更新角色失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteAgent(id: string) {
    loading.value = true
    error.value = null
    try {
      await apiService.agents.delete(id)
      agents.value = agents.value.filter((a) => a.id !== id)
      if (selectedAgentId.value === id) selectedAgentId.value = null
    } catch (e) {
      error.value = e instanceof Error ? e.message : '删除角色失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  function selectAgent(id: string | null) {
    selectedAgentId.value = id
  }

  function clearError() {
    error.value = null
  }

  return {
    agents,
    selectedAgentId,
    loading,
    error,
    promptTemplates,
    onlineAgents,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    selectAgent,
    clearError,
  }
})
