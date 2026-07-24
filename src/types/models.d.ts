export type AgentStatus = 'online' | 'offline' | 'busy'
export type DeviceStatus = 'online' | 'offline'
export type OTABadge = 'latest' | 'pending' | 'updating'
export type KnowledgeStatus = 'enabled' | 'disabled' | 'syncing' | 'draft'
export type MessageRole = 'user' | 'ai'
export type VoiceGender = 'female' | 'male' | 'other'
export type CloneStep = 1 | 2 | 3
export type StepStatus = 'pending' | 'active' | 'done'

export interface GradientStyle {
  gradient: string
  gradientLight?: string
  shadow?: string
}

export interface AgentTag {
  icon: string
  label: string
}

export interface Agent {
  id: string
  name: string
  emoji: string
  style: GradientStyle
  description: string
  tags: AgentTag[]
  status: AgentStatus
  boundDeviceIds: string[]
  systemPrompt: string
  voiceId: string | null
  knowledgeIds: string[]
  createdAt: string
  updatedAt: string
}

export interface AgentForm {
  id?: string
  name: string
  emoji?: string
  description: string
  systemPrompt: string
  voiceId: string | null
  knowledgeIds: string[]
  deviceIds: string[]
  tags: AgentTag[]
}

export interface Device {
  id: string
  name: string
  mac: string
  status: DeviceStatus
  lastConversation: string | null
  firmwareVersion: string
  otaStatus: OTABadge
  autoUpgrade: boolean
  boundAgentId: string | null
  boundAgentName: string | null
  emoji: string
  assignedRole: string
  hasOTA: boolean
}

export interface Voice {
  id: string
  name: string
  character: string
  description: string
  language: string
  gender: VoiceGender
  isCloned: boolean
  selected: boolean
  gradient: string
  emoji: string
  style: GradientStyle
  category: 'female' | 'male' | 'english' | 'japanese' | 'korean' | 'cloned'
  providerVoiceName: string
}

export interface KnowledgeBase {
  id: string
  name: string
  description: string
  itemCount: number
  itemUnit: string
  status: KnowledgeStatus
  isSystem: boolean
  isEnabled: boolean
  lastUpdated: string | null
}

export interface KnowledgeDetail extends KnowledgeBase {
  content: string[]
}

export interface VoiceprintSpeaker {
  id: string
  name: string
  description: string
  registeredAt: string
  sampleCount: number
}

export interface ConversationListItem {
  id: string
  title: string
  preview: string
  agentName: string
  agentEmoji: string
  accentColor: string
  dateLabel: string
  time: string
  messageCount: number
}

export interface Message {
  id: string
  role: MessageRole
  text: string
  timestamp: string
}

export interface Conversation {
  id: string
  title: string
  meta: string
  agentName: string
  agentEmoji: string
  accentColor: string
  accentBg: string
  messages: Message[]
}

export interface UserProfile {
  name: string
  userId: string
  version: string
  totalConversations: number
  totalHours: number
  boundDeviceCount: number
  avatarEmoji: string
}

export interface PromptTemplate {
  key: string
  name: string
  description: string
  icon: string
  text: string
}

export type ModalId =
  | 'modal-agent-config'
  | 'modal-add-device'
  | 'modal-unbind-confirm'
  | 'modal-clone-voice'
  | 'modal-add-speaker'
  | 'modal-kb-new'
  | 'modal-agent-device'
  | null

export interface ModalState {
  id: ModalId
  data: Record<string, unknown>
}
