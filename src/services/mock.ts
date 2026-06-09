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
  UserProfile,
  ApiResponse,
  ApiService,
} from '@/types'

function ok<T>(data: T): ApiResponse<T> {
  return { code: 0, message: 'ok', data, timestamp: Date.now() }
}

const agents: Agent[] = [
  {
    id: 'agent-1',
    name: '笃笃',
    emoji: '🌟',
    style: {
      gradient: 'linear-gradient(135deg, var(--coral), #FF8E53)',
    },
    description: '活泼可爱的学习小伙伴，专注数学和英语启蒙，适合6-12岁小朋友',
    tags: [
      { icon: '🧮', label: '数学' },
      { icon: '🌍', label: '英语' },
      { icon: '📖', label: '故事' },
    ],
    status: 'online',
    boundDeviceIds: ['dev-1'],
    systemPrompt:
      '你是明境AI陪伴机器人的默认伙伴，名叫笃笃，是一个活泼可爱的学习小伙伴。专注于帮助6-12岁的小朋友学习数学和英语。',
    voiceId: 'voice-f-1',
    knowledgeIds: ['kb-1', 'kb-2'],
    speed: 55,
    volume: 80,
    pitch: 60,
    createdAt: '2026-04-01T00:00:00Z',
    updatedAt: '2026-04-05T00:00:00Z',
  },
  {
    id: 'agent-2',
    name: '故事大王',
    emoji: '🦉',
    style: {
      gradient: 'linear-gradient(135deg, #a78bfa, #7c3aed)',
    },
    description: '睡前故事专家，用温柔声音陪伴入眠，包含经典童话与自创故事',
    tags: [
      { icon: '🌙', label: '睡前故事' },
      { icon: '🐾', label: '动物世界' },
    ],
    status: 'offline',
    boundDeviceIds: [],
    systemPrompt:
      '你是一个温柔的故事大王，擅长讲述各种童话故事和睡前故事。语调温和，充满想象力，能根据孩子的喜好即兴创作故事。',
    voiceId: 'voice-f-2',
    knowledgeIds: ['kb-3'],
    speed: 40,
    volume: 70,
    pitch: 45,
    createdAt: '2026-04-02T00:00:00Z',
    updatedAt: '2026-04-03T00:00:00Z',
  },
  {
    id: 'agent-3',
    name: '情绪伙伴',
    emoji: '💛',
    style: {
      gradient: 'linear-gradient(135deg, #ffb830, #ffd980)',
    },
    description: '善解人意的情绪支持者，倾听烦恼、给予温暖的鼓励',
    tags: [
      { icon: '💛', label: '情绪' },
      { icon: '🎧', label: '倾听' },
    ],
    status: 'offline',
    boundDeviceIds: [],
    systemPrompt:
      '你是一个情绪陪伴伙伴，善于倾听和鼓励。当孩子感到委屈、开心或困惑时，你能给予温暖的回应和积极的引导。',
    voiceId: null,
    knowledgeIds: [],
    speed: 50,
    volume: 75,
    pitch: 55,
    createdAt: '2026-04-04T00:00:00Z',
    updatedAt: '2026-04-04T00:00:00Z',
  },
]

const devices: Device[] = [
  {
    id: 'dev-1',
    name: '设备 101',
    mac: '44:1b:**:**:06:90',
    status: 'online',
    lastConversation: '1 个月前',
    firmwareVersion: '2.0.5',
    otaStatus: 'pending',
    autoUpgrade: true,
    boundAgentId: 'agent-1',
    boundAgentName: '笃笃',
    emoji: '🤖',
    assignedRole: '数学老师',
    hasOTA: true,
  },
  {
    id: 'dev-2',
    name: '设备 102',
    mac: '44:1b:**:**:07:12',
    status: 'offline',
    lastConversation: '3 天前',
    firmwareVersion: '2.0.5',
    otaStatus: 'latest',
    autoUpgrade: false,
    boundAgentId: 'agent-1',
    boundAgentName: '笃笃',
    emoji: '🎯',
    assignedRole: 'AI伙伴',
    hasOTA: false,
  },
]

const voices: Voice[] = [
  {
    id: 'voice-f-1',
    name: '甜美 · 活泼',
    character: '甜',
    description: '中文 · 适合儿童陪伴',
    language: '中文',
    gender: 'female',
    isCloned: false,
    selected: true,
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
    emoji: '🎀',
    style: { gradient: 'linear-gradient(135deg, #f093fb, #f5576c)' },
    category: 'female',
  },
  {
    id: 'voice-f-2',
    name: '温柔 · 安心',
    character: '温',
    description: '中文 · 适合睡前故事',
    language: '中文',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    emoji: '🌸',
    style: { gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
    category: 'female',
  },
  {
    id: 'voice-f-3',
    name: '清澈 · 知性',
    character: '清',
    description: '中文 · 适合学习辅导',
    language: '中文',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #a1c4fd, #c2e9fb)',
    emoji: '📚',
    style: { gradient: 'linear-gradient(135deg, #a1c4fd, #c2e9fb)' },
    category: 'female',
  },
  {
    id: 'voice-f-4',
    name: '甜美 · 俏皮',
    character: '俏',
    description: '中文 · 适合角色扮演',
    language: '中文',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #fddb92, #d1fdff)',
    emoji: '🌟',
    style: { gradient: 'linear-gradient(135deg, #fddb92, #d1fdff)' },
    category: 'female',
  },
  {
    id: 'voice-m-1',
    name: '朗朗 · 阳光',
    character: '朗',
    description: '中文 · 适合儿童陪伴',
    language: '中文',
    gender: 'male',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #0fd850, #f9f047)',
    emoji: '☀️',
    style: { gradient: 'linear-gradient(135deg, #0fd850, #f9f047)' },
    category: 'male',
  },
  {
    id: 'voice-m-2',
    name: '沉稳 · 知识感',
    character: '稳',
    description: '中文 · 适合科普问答',
    language: '中文',
    gender: 'male',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    emoji: '🔬',
    style: { gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)' },
    category: 'male',
  },
  {
    id: 'voice-m-3',
    name: '幽默 · 风趣',
    character: '趣',
    description: '中文 · 适合故事讲述',
    language: '中文',
    gender: 'male',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)',
    emoji: '😄',
    style: { gradient: 'linear-gradient(135deg, #43e97b, #38f9d7)' },
    category: 'male',
  },
  {
    id: 'voice-en-1',
    name: 'Lily · 美式英语',
    character: 'En',
    description: 'English · 亲切自然',
    language: '英语',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)',
    emoji: '🇺🇸',
    style: { gradient: 'linear-gradient(135deg, #667eea, #764ba2)' },
    category: 'english',
  },
  {
    id: 'voice-en-2',
    name: 'Tom · 英式英语',
    character: 'En',
    description: 'English · 清晰标准',
    language: '英语',
    gender: 'male',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #764ba2, #667eea)',
    emoji: '🇬🇧',
    style: { gradient: 'linear-gradient(135deg, #764ba2, #667eea)' },
    category: 'english',
  },
  {
    id: 'voice-ja-1',
    name: 'Hana · 日语女声',
    character: 'あ',
    description: '日本語 · 温柔自然',
    language: '日语',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #f7797d, #FBD786)',
    emoji: '🌸',
    style: { gradient: 'linear-gradient(135deg, #f7797d, #FBD786)' },
    category: 'japanese',
  },
  {
    id: 'voice-ko-1',
    name: 'Yuna · 韩语女声',
    character: '한',
    description: '한국어 · 清脆活泼',
    language: '韩语',
    gender: 'female',
    isCloned: false,
    selected: false,
    gradient: 'linear-gradient(135deg, #11998e, #38ef7d)',
    emoji: '🇰🇷',
    style: { gradient: 'linear-gradient(135deg, #11998e, #38ef7d)' },
    category: 'korean',
  },
]

const knowledgeBases: KnowledgeBase[] = [
  {
    id: 'kb-1',
    name: '小学数学题库',
    description: '3,240 道题',
    itemCount: 3240,
    itemUnit: '道题',
    status: 'enabled',
    isSystem: true,
    isEnabled: true,
    lastUpdated: null,
  },
  {
    id: 'kb-2',
    name: '英语绘本词汇',
    description: '1,500 词',
    itemCount: 1500,
    itemUnit: '词',
    status: 'enabled',
    isSystem: true,
    isEnabled: true,
    lastUpdated: null,
  },
  {
    id: 'kb-3',
    name: '经典童话故事',
    description: '328 篇',
    itemCount: 328,
    itemUnit: '篇',
    status: 'syncing',
    isSystem: true,
    isEnabled: false,
    lastUpdated: null,
  },
  {
    id: 'kb-4',
    name: '我的绘本合集',
    description: '12 个文件',
    itemCount: 12,
    itemUnit: '个文件',
    status: 'enabled',
    isSystem: false,
    isEnabled: true,
    lastUpdated: '3 天前',
  },
  {
    id: 'kb-5',
    name: '家庭专属词汇',
    description: '68 个词条',
    itemCount: 68,
    itemUnit: '个词条',
    status: 'draft',
    isSystem: false,
    isEnabled: false,
    lastUpdated: '1 周前',
  },
]

const speakers: VoiceprintSpeaker[] = [
  {
    id: 'vp-1',
    name: '小婷',
    registeredAt: '2026-04-01',
    sampleCount: 3,
    gradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
    emoji: '👩',
    verified: true,
    description: '已注册 3 个样本',
  },
  {
    id: 'vp-2',
    name: '小明',
    registeredAt: '2026-04-02',
    sampleCount: 2,
    gradient: 'linear-gradient(135deg, #4facfe, #00f2fe)',
    emoji: '👦',
    verified: false,
    description: '已注册 2 个样本',
  },
]

const conversationList: ConversationListItem[] = [
  {
    id: 'conv-math',
    title: '数学思维 · 苹果题',
    preview: '小明有12个苹果，给了小红3个…',
    agentName: '笃笃',
    agentEmoji: '🧮',
    accentColor: 'var(--teal)',
    dateLabel: '今天',
    time: '14:23',
    messageCount: 4,
  },
  {
    id: 'conv-english',
    title: '英语启蒙 · 动物单词',
    preview: 'Cat的发音是/kæt/…',
    agentName: '笃笃',
    agentEmoji: '🌍',
    accentColor: 'var(--indigo)',
    dateLabel: '今天',
    time: '10:19',
    messageCount: 6,
  },
  {
    id: 'conv-weather',
    title: '天气与清明节',
    preview: '今天天气晴朗，温度18-25度…',
    agentName: '笃笃',
    agentEmoji: '☀️',
    accentColor: 'var(--amber)',
    dateLabel: '昨天',
    time: '09:48',
    messageCount: 6,
  },
  {
    id: 'conv-story',
    title: '睡前故事 · 小熊和森林',
    preview: '从前，在一片大森林里住着…',
    agentName: '故事大王',
    agentEmoji: '📖',
    accentColor: 'var(--coral)',
    dateLabel: '昨天',
    time: '20:05',
    messageCount: 12,
  },
]

const conversationDetails: Record<string, Conversation> = {
  'conv-math': {
    id: 'conv-math',
    title: '数学思维 · 苹果题',
    meta: '笃笃 · 今天 14:23 · 4 条消息',
    agentName: '笃笃',
    agentEmoji: '🧮',
    accentColor: 'var(--teal)',
    accentBg: '#e8fdf5',
    messages: [
      {
        id: 'msg-1',
        role: 'user',
        text: '笃笃，小明有12个苹果，给了小红3个，还剩几个？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-2',
        role: 'ai',
        text: '嗨！这是个减法问题哦！\n小明原来有 12 个苹果，给了小红 3 个，所以：\n12 - 3 = 9 个\n小明还剩 9 个苹果！🍎 你答对了吗？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-3',
        role: 'user',
        text: '对的！那如果再给小华5个呢？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-4',
        role: 'ai',
        text: '很棒！继续算！\n小明还有 9 个苹果，再给小华 5 个：\n9 - 5 = 4 个\n小明最后还有 4 个苹果 🍎🍎🍎🍎！你是数学小达人！',
        timestamp: new Date().toISOString(),
      },
    ],
  },
  'conv-english': {
    id: 'conv-english',
    title: '英语启蒙 · 动物单词',
    meta: '笃笃 · 今天 10:19 · 6 条消息',
    agentName: '笃笃',
    agentEmoji: '🌍',
    accentColor: 'var(--indigo)',
    accentBg: '#eef0fc',
    messages: [
      {
        id: 'msg-5',
        role: 'user',
        text: '笃笃，猫用英语怎么说？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-6',
        role: 'ai',
        text: 'Cat！发音是 /kæt/，听起来像"卡特"。Cat 这个单词很简单，记住了吗？🐱',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-7',
        role: 'user',
        text: '那狗呢？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-8',
        role: 'ai',
        text: 'Dog！发音是 /dɒɡ/，听起来像"道格"。Cat 和 Dog 是英语里最常见的动物单词，你已经会两个了！🐶',
        timestamp: new Date().toISOString(),
      },
    ],
  },
  'conv-weather': {
    id: 'conv-weather',
    title: '天气与清明节',
    meta: '笃笃 · 昨天 09:48 · 6 条消息',
    agentName: '笃笃',
    agentEmoji: '☀️',
    accentColor: 'var(--amber)',
    accentBg: '#fff8e6',
    messages: [
      {
        id: 'msg-9',
        role: 'user',
        text: '今天天气怎么样？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-10',
        role: 'ai',
        text: '今天天气晴朗，温度18-25度，非常适合户外活动！清明节快到了，可以去扫墓、踏青哦！',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-11',
        role: 'user',
        text: '清明节是什么节日？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-12',
        role: 'ai',
        text: '清明节是中国的传统节日，通常在每年4月4日或5日。这一天，人们会祭扫祖先的坟墓，表达对先人的思念，也是踏青赏春的好时节！',
        timestamp: new Date().toISOString(),
      },
    ],
  },
  'conv-story': {
    id: 'conv-story',
    title: '睡前故事 · 小熊和森林',
    meta: '故事大王 · 昨天 20:05 · 12 条消息',
    agentName: '故事大王',
    agentEmoji: '📖',
    accentColor: 'var(--coral)',
    accentBg: '#fff0f0',
    messages: [
      {
        id: 'msg-13',
        role: 'user',
        text: '给我讲一个小熊的故事吧',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-14',
        role: 'ai',
        text: '从前，在一片大森林里住着一只叫豆豆的小熊。豆豆有一双大眼睛，棕色的毛发软软的，最爱吃蜂蜜🍯',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-15',
        role: 'user',
        text: '后来发生什么了？',
        timestamp: new Date().toISOString(),
      },
      {
        id: 'msg-16',
        role: 'ai',
        text: '有一天，豆豆在森林里散步，发现了一棵神奇的大树，树上有一个金色的蜂巢，里面传来甜甜的香气…要继续听吗？',
        timestamp: new Date().toISOString(),
      },
    ],
  },
}

const profile: UserProfile = {
  name: '明境用户',
  userId: 'MJ-20240405',
  version: '4.0.0',
  totalConversations: 127,
  totalHours: 43,
  boundDeviceCount: 2,
  avatarEmoji: '👨‍👧',
}

let agentSeq = agents.length
function newAgentId(): string {
  return `agent-${++agentSeq}`
}

let devSeq = devices.length
function newDevId(): string {
  return `dev-${++devSeq}`
}

let kbSeq = knowledgeBases.length
function newKbId(): string {
  return `kb-${++kbSeq}`
}

let cloneSeq = 0
function newCloneId(): string {
  return `voice-cloned-${++cloneSeq}`
}

function delay<T>(data: T, ms = 300): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data), ms))
}

export function createMockApiService(): ApiService {
  return {
    agents: {
      getList: () => delay(ok(structuredClone(agents))),
      getById: (id: string) => {
        const agent = agents.find((a) => a.id === id)
        if (!agent) return Promise.reject(new Error('角色不存在'))
        return delay(ok(structuredClone(agent)))
      },
      create: (form: AgentForm) => {
        const newAgent: Agent = {
          id: newAgentId(),
          name: form.name,
          emoji: form.emoji ?? '🤖',
          style: {
            gradient: 'linear-gradient(135deg, var(--coral), #FF8E53)',
          },
          description: form.description,
          tags: form.tags,
          status: 'offline',
          boundDeviceIds: [],
          systemPrompt: form.systemPrompt,
          voiceId: form.voiceId,
          knowledgeIds: form.knowledgeIds,
          speed: form.speed,
          volume: form.volume,
          pitch: form.pitch,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        agents.push(newAgent)
        return delay(ok(structuredClone(newAgent)))
      },
      update: (id: string, form: AgentForm) => {
        const idx = agents.findIndex((a) => a.id === id)
        if (idx === -1) return Promise.reject(new Error('角色不存在'))
        agents[idx] = {
          ...agents[idx],
          name: form.name,
          description: form.description,
          systemPrompt: form.systemPrompt,
          voiceId: form.voiceId,
          knowledgeIds: form.knowledgeIds,
          speed: form.speed,
          volume: form.volume,
          pitch: form.pitch,
          tags: form.tags,
          updatedAt: new Date().toISOString(),
        }
        return delay(ok(structuredClone(agents[idx])))
      },
      delete: (id: string) => {
        const idx = agents.findIndex((a) => a.id === id)
        if (idx === -1) return Promise.reject(new Error('角色不存在'))
        agents.splice(idx, 1)
        return delay(ok(null))
      },
    },

    devices: {
      getList: () => delay(ok(structuredClone(devices))),
      getById: (id: string) => {
        const dev = devices.find((d) => d.id === id)
        if (!dev) return Promise.reject(new Error('设备不存在'))
        return delay(ok(structuredClone(dev)))
      },
      bind: (code: string, agentId?: string) => {
        if (code.length !== 6) {
          return Promise.reject(new Error('请输入6位验证码'))
        }
        const agent = agentId ? agents.find((a) => a.id === agentId) : null
        const newDev: Device = {
          id: newDevId(),
          name: `设备 ${100 + devices.length + 1}`,
          mac: `44:1b:**:**:${String(devices.length + 1).padStart(2, '0')}:${String(Math.floor(Math.random() * 100)).padStart(2, '0')}`,
          status: 'online',
          lastConversation: null,
          firmwareVersion: '2.0.5',
          otaStatus: 'latest',
          autoUpgrade: true,
          boundAgentId: agent?.id ?? null,
          boundAgentName: agent?.name ?? null,
          emoji: '🤖',
          assignedRole: '未分配',
          hasOTA: false,
        }
        devices.push(newDev)
        if (agent) {
          agent.boundDeviceIds.push(newDev.id)
          agent.status = 'online'
        }
        return delay(ok(structuredClone(newDev)))
      },
      unbind: (id: string) => {
        const idx = devices.findIndex((d) => d.id === id)
        if (idx === -1) return Promise.reject(new Error('设备不存在'))
        const dev = devices[idx]
        if (dev.boundAgentId) {
          const agent = agents.find((a) => a.id === dev.boundAgentId)
          if (agent) {
            agent.boundDeviceIds = agent.boundDeviceIds.filter((did) => did !== id)
            if (agent.boundDeviceIds.length === 0) agent.status = 'offline'
          }
        }
        devices.splice(idx, 1)
        return delay(ok(null))
      },
      upgradeFirmware: (id: string) => {
        const dev = devices.find((d) => d.id === id)
        if (!dev) return Promise.reject(new Error('设备不存在'))
        dev.firmwareVersion = '2.0.6'
        dev.otaStatus = 'latest'
        return delay(ok(structuredClone(dev)))
      },
      assignRole: (id: string, agentId: string | null) => {
        const dev = devices.find((d) => d.id === id)
        if (!dev) return Promise.reject(new Error('设备不存在'))

        if (dev.boundAgentId) {
          const prevAgent = agents.find((a) => a.id === dev.boundAgentId)
          if (prevAgent) {
            prevAgent.boundDeviceIds = prevAgent.boundDeviceIds.filter((did) => did !== id)
            if (prevAgent.boundDeviceIds.length === 0) prevAgent.status = 'offline'
          }
        }
        if (agentId) {
          const agent = agents.find((a) => a.id === agentId)
          if (!agent) return Promise.reject(new Error('角色不存在'))
          dev.boundAgentId = agent.id
          dev.boundAgentName = agent.name
          if (!agent.boundDeviceIds.includes(id)) {
            agent.boundDeviceIds.push(id)
          }
          agent.status = 'online'
        } else {
          dev.boundAgentId = null
          dev.boundAgentName = null
        }
        return delay(ok(structuredClone(dev)))
      },
    },

    voices: {
      getList: () => delay(ok(structuredClone(voices))),
      cloneVoice: () => {
        const cloned: Voice = {
          id: newCloneId(),
          name: '我的声音克隆',
          character: '我',
          description: '自定义克隆 · 已激活',
          language: '中文',
          gender: 'female',
          isCloned: true,
          selected: false,
          gradient: 'linear-gradient(135deg, var(--violet), var(--coral))',
          emoji: '🎙️',
          style: { gradient: 'linear-gradient(135deg, var(--violet), var(--coral))' },
          category: 'cloned',
        }
        voices.push(cloned)
        return delay(ok(structuredClone(cloned)), 3700)
      },
      selectVoice: (id: string) => {
        voices.forEach((v) => (v.selected = v.id === id))
        return delay(ok(null))
      },
    },

    voiceLibrary: {
      getList: () => delay(ok(structuredClone(voices))),
    },

    knowledge: {
      getList: () => delay(ok(structuredClone(knowledgeBases))),
      getDetail: (id: string) => {
        const kb = knowledgeBases.find((k) => k.id === id)
        if (!kb) return Promise.reject(new Error('知识库不存在'))
        const detail: KnowledgeDetail = {
          ...structuredClone(kb),
          content: ['示例知识点内容1', '示例知识点内容2'],
        }
        return delay(ok(detail))
      },
      toggleKnowledge: (id: string, enabled: boolean) => {
        const kb = knowledgeBases.find((k) => k.id === id)
        if (!kb) return Promise.reject(new Error('知识库不存在'))
        kb.isEnabled = enabled
        kb.status = enabled ? 'enabled' : 'disabled'
        return delay(ok(null))
      },
      toggleMemory: (enabled: boolean) => {
        return delay(ok(null))
      },
      upload: (_file: File, name: string) => {
        const newKb: KnowledgeBase = {
          id: newKbId(),
          name,
          description: '1 个文件',
          itemCount: 1,
          itemUnit: '个文件',
          status: 'enabled',
          isSystem: false,
          isEnabled: true,
          lastUpdated: '刚刚',
        }
        knowledgeBases.push(newKb)
        return delay(ok(structuredClone(newKb)))
      },
      delete: (id: string) => {
        const idx = knowledgeBases.findIndex((k) => k.id === id)
        if (idx === -1) return Promise.reject(new Error('知识库不存在'))
        knowledgeBases.splice(idx, 1)
        return delay(ok(null))
      },
      deleteContent: (_id: string, _index: number) => {
        return delay(ok(null))
      },
    },

    voiceprint: {
      getList: () => delay(ok(structuredClone(speakers))),
      register: (name: string) => {
        const newSpeaker: VoiceprintSpeaker = {
          id: `vp-${speakers.length + 1}`,
          name,
          registeredAt: new Date().toISOString().split('T')[0],
          sampleCount: 1,
          gradient: 'linear-gradient(135deg, #f093fb, #f5576c)',
          emoji: '🎙️',
          verified: false,
          description: '新注册样本',
        }
        speakers.push(newSpeaker)
        return delay(ok(structuredClone(newSpeaker)))
      },
      delete: (id: string) => {
        const idx = speakers.findIndex((s) => s.id === id)
        if (idx === -1) return Promise.reject(new Error('说话人不存在'))
        speakers.splice(idx, 1)
        return delay(ok(null))
      },
    },

    history: {
      getList: (filter?: string) => {
        let list = structuredClone(conversationList)
        if (filter && filter !== '全部') {
          list = list.filter((c) => c.agentName === filter || c.dateLabel === filter)
        }
        return delay(ok(list))
      },
      getConversation: (id: string) => {
        const conv = conversationDetails[id]
        if (!conv) return Promise.reject(new Error('对话不存在'))
        return delay(ok(structuredClone(conv)))
      },
      getMessages: (conversationId: string) => {
        const conv = conversationDetails[conversationId]
        if (!conv) return Promise.reject(new Error('对话不存在'))
        return delay(ok(structuredClone(conv.messages)))
      },
    },

    user: {
      getProfile: () => delay(ok(structuredClone(profile))),
      updateNotification: () => delay(ok(null)),
    },
  }
}
