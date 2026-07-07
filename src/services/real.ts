import { httpClient } from '@/services/http'
import type {
  ApiResponse,
  ApiService,
  Agent,
  AgentForm,
  Device,
  Voice,
  KnowledgeBase,
  KnowledgeDetail,
  VoiceprintSpeaker,
  ConversationListItem,
  Conversation,
  Message,
  UserProfile,
} from '@/types'

function unwrap<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<ApiResponse<T>> {
  return promise.then((res) => res.data)
}

export function createRealApiService(): ApiService {
  return {
    agents: {
      getList: () => unwrap(httpClient.get<ApiResponse<Agent[]>>('/agents')),
      getById: (id) => unwrap(httpClient.get<ApiResponse<Agent>>(`/agents/${id}`)),
      create: (form) => unwrap(httpClient.post<ApiResponse<Agent>>('/agents', form)),
      update: (id, form) => unwrap(httpClient.put<ApiResponse<Agent>>(`/agents/${id}`, form)),
      delete: (id) => unwrap(httpClient.delete<ApiResponse<null>>(`/agents/${id}`)),
    },

    devices: {
      getList: () => unwrap(httpClient.get<ApiResponse<Device[]>>('/devices')),
      getById: (id) => unwrap(httpClient.get<ApiResponse<Device>>(`/devices/${id}`)),
      bind: (code, agentId) =>
        unwrap(httpClient.post<ApiResponse<Device>>('/devices/bind', { code, agent_id: agentId })),
      unbind: (id) => unwrap(httpClient.delete<ApiResponse<null>>(`/devices/${id}/unbind`)),
      upgradeFirmware: (id) =>
        unwrap(httpClient.post<ApiResponse<Device>>(`/devices/${id}/upgrade`)),
      assignRole: (id, agentId) =>
        unwrap(httpClient.put<ApiResponse<Device>>(`/devices/${id}/role`, { agent_id: agentId })),
    },

    voices: {
      getList: () => unwrap(httpClient.get<ApiResponse<Voice[]>>('/voices')),
      cloneVoice: (blob) => {
        const formData = new FormData()
        formData.append('audio', blob)
        return unwrap(
          httpClient.post<ApiResponse<Voice>>('/voices/clone', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
          }),
        )
      },
      selectVoice: (id) => unwrap(httpClient.put<ApiResponse<null>>(`/voices/${id}/select`)),
    },

    voiceLibrary: {
      getList: () => unwrap(httpClient.get<ApiResponse<Voice[]>>('/voices')),
    },

    knowledge: {
      getList: () => unwrap(httpClient.get<ApiResponse<KnowledgeBase[]>>('/knowledge')),
      getDetail: (id) => unwrap(httpClient.get<ApiResponse<KnowledgeDetail>>(`/knowledge/${id}`)),
      toggleKnowledge: (id, enabled) =>
        unwrap(httpClient.put<ApiResponse<null>>(`/knowledge/${id}/toggle`, { enabled })),
      toggleMemory: (enabled) =>
        unwrap(httpClient.put<ApiResponse<null>>('/knowledge/memory/toggle', { enabled })),
      upload: (file, name) => {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('name', name)
        return unwrap(httpClient.post<ApiResponse<KnowledgeBase>>('/knowledge/upload', formData))
      },
      delete: (id) => unwrap(httpClient.delete<ApiResponse<null>>(`/knowledge/${id}`)),
      deleteContent: (id, index) =>
        unwrap(httpClient.delete<ApiResponse<null>>(`/knowledge/${id}/content/${index}`)),
    },

    voiceprint: {
      getList: () => unwrap(httpClient.get<ApiResponse<VoiceprintSpeaker[]>>('/voiceprint')),
      register: (name, voiceSampleId) =>
        unwrap(
          httpClient.post<ApiResponse<VoiceprintSpeaker>>('/voiceprint/register', {
            name,
            voiceSampleId,
          }),
        ),
      delete: (id) => unwrap(httpClient.delete<ApiResponse<null>>(`/voiceprint/${id}`)),
    },

    history: {
      getList: (filter) =>
        unwrap(
          httpClient.get<ApiResponse<ConversationListItem[]>>('/history', {
            params: filter ? { filter } : {},
          }),
        ),
      getConversation: (id) => unwrap(httpClient.get<ApiResponse<Conversation>>(`/history/${id}`)),
      getMessages: (conversationId) =>
        unwrap(httpClient.get<ApiResponse<Message[]>>(`/history/${conversationId}/messages`)),
    },

    user: {
      getProfile: () => unwrap(httpClient.get<ApiResponse<UserProfile>>('/user/profile')),
      updateNotification: (enabled) =>
        unwrap(httpClient.put<ApiResponse<null>>('/user/notification', { enabled })),
    },
  }
}
