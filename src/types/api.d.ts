import type {
  Agent,
  AgentForm,
  Device,
  Voice,
  KnowledgeBase,
  VoiceprintSpeaker,
  ConversationListItem,
  Conversation,
  Message,
  UserProfile,
} from './models.d'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  timestamp: number
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface PaginatedResponse<T> extends ApiResponse<PaginatedData<T>> {}

export interface AgentsApi {
  getList(): Promise<ApiResponse<Agent[]>>
  getById(id: string): Promise<ApiResponse<Agent>>
  create(form: AgentForm): Promise<ApiResponse<Agent>>
  update(id: string, form: AgentForm): Promise<ApiResponse<Agent>>
  delete(id: string): Promise<ApiResponse<null>>
}

export interface DevicesApi {
  getList(): Promise<ApiResponse<Device[]>>
  getById(id: string): Promise<ApiResponse<Device>>
  bind(code: string, agentId?: string): Promise<ApiResponse<Device>>
  unbind(id: string): Promise<ApiResponse<null>>
  upgradeFirmware(id: string): Promise<ApiResponse<Device>>
  assignRole(id: string, agentId: string): Promise<ApiResponse<Device>>
}

export interface VoicesApi {
  getList(gender?: string): Promise<ApiResponse<Voice[]>>
  cloneVoice(blob: Blob): Promise<ApiResponse<Voice>>
  selectVoice(id: string): Promise<ApiResponse<null>>
}

export interface KnowledgeApi {
  getList(): Promise<ApiResponse<KnowledgeBase[]>>
  toggleKnowledge(id: string, enabled: boolean): Promise<ApiResponse<null>>
  toggleMemory(enabled: boolean): Promise<ApiResponse<null>>
  upload(file: File, name: string): Promise<ApiResponse<KnowledgeBase>>
}

export interface VoiceprintApi {
  getList(): Promise<ApiResponse<VoiceprintSpeaker[]>>
  register(name: string, voiceSampleId: string): Promise<ApiResponse<VoiceprintSpeaker>>
  delete(id: string): Promise<ApiResponse<null>>
}

export interface HistoryApi {
  getList(filter?: string): Promise<ApiResponse<ConversationListItem[]>>
  getConversation(id: string): Promise<ApiResponse<Conversation>>
  getMessages(conversationId: string): Promise<ApiResponse<Message[]>>
}

export interface UserApi {
  getProfile(): Promise<ApiResponse<UserProfile>>
  updateNotification(enabled: boolean): Promise<ApiResponse<null>>
}

export interface ApiService {
  agents: AgentsApi
  devices: DevicesApi
  voices: VoicesApi
  knowledge: KnowledgeApi
  voiceprint: VoiceprintApi
  history: HistoryApi
  user: UserApi
}
