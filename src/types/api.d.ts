import type {
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
} from './models.d'

export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  timestamp: number
}

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
  assignRole(id: string, agentId: string | null): Promise<ApiResponse<Device>>
  startProvisioning(): Promise<ApiResponse<{ sessionId: string; expiresInSeconds: number }>>
}

export interface VoicesApi {
  getList(gender?: string): Promise<ApiResponse<Voice[]>>
  cloneVoice(blob: Blob): Promise<ApiResponse<Voice>>
  selectVoice(id: string): Promise<ApiResponse<null>>
}

export interface VoiceLibraryApi {
  getList(): Promise<ApiResponse<Voice[]>>
}

export interface KnowledgeApi {
  getList(): Promise<ApiResponse<KnowledgeBase[]>>
  getDetail(id: string): Promise<ApiResponse<KnowledgeDetail>>
  toggleKnowledge(id: string, enabled: boolean): Promise<ApiResponse<null>>
  toggleMemory(enabled: boolean): Promise<ApiResponse<null>>
  upload(file: File, name: string): Promise<ApiResponse<KnowledgeBase>>
  delete(id: string): Promise<ApiResponse<null>>
  deleteContent(id: string, index: number): Promise<ApiResponse<null>>
}

export interface VoiceprintApi {
  getList(): Promise<ApiResponse<VoiceprintSpeaker[]>>
  register(
    name: string,
    description: string,
    audioFile: Blob,
  ): Promise<ApiResponse<VoiceprintSpeaker>>
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

export interface AuthApi {
  register(
    username: string,
    password: string,
  ): Promise<ApiResponse<{ token: string; userId: string }>>
  login(username: string, password: string): Promise<ApiResponse<{ token: string; userId: string }>>
  me(): Promise<ApiResponse<{ userId: string; username: string }>>
}

export interface ApiService {
  auth: AuthApi
  agents: AgentsApi
  devices: DevicesApi
  voices: VoicesApi
  knowledge: KnowledgeApi
  voiceprint: VoiceprintApi
  history: HistoryApi
  user: UserApi
}
