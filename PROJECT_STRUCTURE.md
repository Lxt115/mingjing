# 明境 · AI 陪伴管理平台 — 项目文件结构说明

一个 **Vue 3 + FastAPI** 的全栈项目，用于管理 AI 伙伴（Agent）、设备、声音、知识库等。

---

## 根目录配置文件

```
├── .env.development              # 前端开发环境变量（VITE_API_BASE 等）
├── .env.production               # 前端生产环境变量
├── .eslintrc.cjs                 # ESLint 代码规范配置
├── .gitignore                    # Git 忽略规则
├── .prettierrc                   # Prettier 代码格式化配置
├── index.html                    # 前端 SPA 入口 HTML
├── mingjing_desktop.html         # 桌面端专用入口页面
├── ai_robot_wxappv7.html         # 微信小程序 AI 机器人页面
├── package.json                  # 前端依赖 & npm scripts（项目名 mingjing-admin v4.0.0）
├── package-lock.json             # 前端依赖锁定文件
├── postcss.config.js             # PostCSS 配置（配合 Tailwind）
├── tailwind.config.js            # Tailwind CSS 配置
├── tsconfig.json                 # TypeScript 主配置
├── tsconfig.node.json            # TypeScript Node 环境配置
├── vite.config.ts                # Vite 构建配置（别名 @、端口 5173、分包策略）
├── vitest.config.ts              # Vitest 单元测试配置
├── README.md                     # 项目说明文档
├── MIGRATION.md                  # 数据库迁移说明文档
└── PROJECT_STRUCTURE.md          # 本文件：项目文件结构说明
```

---

## `.github/workflows/` — CI/CD

```
└── ci.yml                        # GitHub Actions CI 流水线配置
```

---

## `.husky/` — Git 钩子

```
└── pre-commit                    # Git pre-commit 钩子（提交前自动 lint）
```

---

## `.vscode/` — VS Code 配置

```
├── extensions.json               # 推荐 VS Code 插件列表
└── settings.json                 # VS Code 工作区设置
```

---

## `src/` — 前端源代码

### 入口

```
├── App.vue                       # 根组件，包含布局和路由出口
├── main.ts                       # 应用入口：创建 Vue 实例、注册 Pinia/Router
└── env.d.ts                      # Vite 环境变量类型声明
```

### `src/router/` — 路由

```
└── index.ts                      # 路由定义
```

**路由表：**

| 路径 | 页面 | 功能 |
|------|------|------|
| `/agents` | AgentsView | AI 伙伴管理（主页） |
| `/history` | HistoryView | 对话历史记录 |
| `/devices` | DevicesView | 设备管理 |
| `/voice-library` | VoiceLibraryView | 声音库 |
| `/knowledge` | KnowledgeView | 知识库管理 |
| `/voiceprint` | VoiceprintView | 声纹识别 |
| `/profile` | ProfileView | 个人中心 |

### `src/store/` — Pinia 状态管理

```
├── index.ts                      # store 统一导出
├── agents.ts                     # AI 伙伴（Agent）状态管理
├── devices.ts                    # 设备绑定状态管理
├── ui.ts                         # UI 状态（侧边栏、主题等）
├── ui.test.ts                    # UI store 单元测试
└── user.ts                       # 用户/账号状态管理
```

### `src/views/` — 页面组件

```
├── AgentsView.vue                # AI 伙伴管理页（主页面）
├── HistoryView.vue               # 对话历史记录页
├── DevicesView.vue               # 设备管理页
├── VoiceLibraryView.vue          # 声音库页（为 Agent 选音色）
├── KnowledgeView.vue             # 知识库管理页
├── VoiceprintView.vue            # 声纹识别管理页
└── ProfileView.vue               # 个人中心/系统设置页
```

### `src/components/` — 组件库

```
├── ModalsContainer.vue           # 全局弹窗容器
├── layout/
│   ├── DesktopSidebar.vue        # 桌面端侧边导航栏
│   ├── MobileTabBar.vue          # 移动端底部 Tab 栏
│   ├── TopBar.vue                # 顶部标题栏
│   └── index.ts                  # 布局组件统一导出
├── modals/
│   ├── AddDeviceModal.vue        # 添加设备弹窗
│   ├── AddSpeakerModal.vue       # 添加说话人弹窗
│   ├── AgentConfigModal.vue      # Agent 配置编辑弹窗
│   ├── AgentDeviceModal.vue      # Agent 绑定设备弹窗
│   ├── CloneVoiceModal.vue       # 声音克隆弹窗
│   ├── KbNewModal.vue            # 新建知识库弹窗
│   ├── UnbindConfirmModal.vue    # 解绑确认弹窗
│   └── index.ts                  # 弹窗组件统一导出
└── ui/
    ├── Button.vue                # 通用按钮
    ├── Card.vue                  # 通用卡片
    ├── FilterChips.vue           # 筛选标签组件
    ├── InfoTip.vue               # 信息提示组件
    ├── Modal.vue                 # 通用弹窗
    ├── StatusBadge.vue           # 状态徽章
    ├── Switch.vue                # 开关组件
    ├── Tabs.vue                  # 标签页组件
    ├── Toast.vue                 # 消息提示组件
    └── index.ts                  # UI 组件统一导出
```

### `src/composables/` — Vue 组合式函数

```
├── index.ts                      # composables 统一导出
├── useDeviceBind.ts              # 设备绑定/解绑逻辑
├── useFormValidator.ts           # 表单校验逻辑
├── useMediaQuery.ts              # 响应式媒体查询
├── useModal.ts                   # 弹窗管理（v-model 驱动）
└── useVoiceRecord.ts             # 录音功能（声纹采集）
```

### `src/services/` — API 调用层

```
├── index.ts                      # 服务统一导出
├── http.ts                       # Axios 实例封装（拦截器、baseURL）
├── mock.ts                       # Mock 数据服务（开发用）
└── real.ts                       # 真实 API 调用服务
```

### `src/types/` — TypeScript 类型定义

```
├── index.ts                      # 类型统一导出
├── api.d.ts                      # API 请求/响应类型
└── models.d.ts                   # 业务模型类型（Agent、Device、Voice 等）
```

### `src/utils/` — 工具函数

```
├── index.ts                      # 工具函数统一导出
├── debounce.ts                   # 防抖函数
├── format.ts                     # 格式化工具（日期等）
├── guards.ts                     # 路由/权限守卫
└── utils.test.ts                 # 工具函数单元测试
```

### `src/styles/` — 样式

```
├── reset.css                     # CSS 重置样式
└── variables.css                 # CSS 变量定义
```

### `src/assets/` — 静态资源

```
└── main.css                      # 全局样式入口
```

---

## `server/` — 后端源代码

### 后端配置

```
├── .env.example                  # 环境变量示例
├── alembic.ini                   # Alembic 数据库迁移配置
├── docker-compose.yml            # Docker 编排配置
├── mingjing_dev.db               # SQLite 开发数据库文件
├── requirements.txt              # Python 依赖列表
├── seed.py                       # 种子数据初始化脚本
└── test_api.py                   # API 接口测试脚本
```

**Python 依赖（requirements.txt）：**

| 包名 | 用途 |
|------|------|
| `fastapi` | Web 框架 |
| `uvicorn` | ASGI 服务器 |
| `sqlalchemy[asyncio]` | 异步 ORM |
| `asyncpg` | PostgreSQL 异步驱动 |
| `aiosqlite` | SQLite 异步驱动 |
| `alembic` | 数据库迁移工具 |
| `pydantic` / `pydantic-settings` | 数据校验 & 配置管理 |
| `httpx` | 异步 HTTP 客户端 |
| `edge-tts` | 微软免费 TTS |
| `openai` | OpenAI API 客户端（兼容 Whisper） |
| `dashscope` | 阿里百炼 SDK（LLM/STT/TTS） |
| `python-multipart` | 文件上传支持 |

### `server/src/` — 源码入口

```
├── __init__.py
├── config.py                     # 全局配置（Settings 类，读取 .env）
├── database.py                   # 数据库引擎 & 会话管理
└── main.py                       # FastAPI 应用入口：挂载路由、中间件、WebSocket
```

### `server/src/middleware/` — 中间件

```
├── __init__.py
└── error_handler.py              # 全局 HTTP 异常处理中间件
```

### `server/src/models/` — SQLAlchemy ORM 模型

```
├── __init__.py
├── base.py                       # 声明式基类 Base
├── agent.py                      # Agent（AI 伙伴）表
├── conversation.py               # Conversation + Message（对话 & 消息）表
├── device.py                     # Device（设备）表
├── knowledge.py                  # KnowledgeBase（知识库）表
├── voice.py                      # Voice（声音/音色）表
└── voiceprint.py                 # VoiceprintSpeaker（声纹说话人）表
```

### `server/src/schemas/` — Pydantic 请求/响应模型

```
├── __init__.py
├── common.py                     # 通用响应模型
├── agent.py                      # Agent 请求/响应 Schema
├── conversation.py               # 对话 Schema
├── device.py                     # 设备 Schema
├── knowledge.py                  # 知识库 Schema
├── pipeline.py                   # 对话管道 Schema
├── user.py                       # 用户 Schema
├── voice.py                      # 声音 Schema
└── voiceprint.py                 # 声纹 Schema
```

### `server/src/routers/` — API 路由

```
├── __init__.py
├── agents.py                     # /api/agents — CRUD
├── conversations.py              # /api/conversations — 对话管理
├── devices.py                    # /api/devices — 设备绑定
├── knowledge.py                  # /api/knowledge — 知识库
├── pipeline.py                   # /api/pipeline — 对话管道（LLM+TTS）
├── users.py                      # /api/users — 用户
├── voiceprints.py                # /api/voiceprints — 声纹
└── voices.py                     # /api/voices — 声音/音色
```

### `server/src/services/` — 业务逻辑层

```
├── __init__.py
├── agents.py                     # Agent 业务逻辑
├── conversations.py              # 对话业务逻辑
├── devices.py                    # 设备业务逻辑
├── knowledge.py                  # 知识库业务逻辑
├── pipeline.py                   # 管道业务逻辑（组装 LLM+STT+TTS）
├── users.py                      # 用户业务逻辑
├── voiceprints.py                # 声纹业务逻辑
└── voices.py                     # 声音业务逻辑
```

### `server/src/providers/` — 第三方服务适配层

```
├── __init__.py
├── factory.py                    # Provider 工厂：根据配置动态选择实现
├── llm/                          # 大语言模型提供商
│   ├── __init__.py
│   ├── base.py                   # LLM 抽象基类
│   ├── bailian.py                # 阿里百炼 LLM
│   └── deepseek.py               # DeepSeek LLM
├── stt/                          # 语音识别提供商
│   ├── __init__.py
│   ├── base.py                   # STT 抽象基类
│   ├── bailian.py                # 阿里百炼 STT
│   └── whisper.py                # OpenAI Whisper STT
└── tts/                          # 语音合成提供商
    ├── __init__.py
    ├── base.py                   # TTS 抽象基类
    ├── _synthesize.py            # 百炼 TTS 底层实现（CosyVoice WebSocket 调用）
    ├── bailian.py                # 百炼 TTS Provider
    └── edgetts.py                # Edge TTS Provider（免费微软 TTS）
```

### `server/src/ws/` — WebSocket 处理

```
├── __init__.py
├── device.py                     # /ws/device/{device_id} — 设备实时通信
├── manager.py                    # WebSocket 连接管理器
└── voice.py                      # /ws/voice/{agent_id} — 语音对话实时流
```

### `server/alembic/` — 数据库迁移

```
├── __init__.py
├── env.py                        # Alembic 环境配置（数据库连接、元数据）
└── versions/
    └── __init__.py               # 迁移版本文件目录
```

---

## `simulator/` — 设备模拟器

```
└── index.html                    # 设备端模拟页面（模拟硬件设备交互）
```

---

## 架构总览

```
浏览器/Vue 3 SPA                  硬件设备
    │  HTTP/REST                     │  WebSocket
    ▼                                ▼
┌─────────────────────────────────────────┐
│         FastAPI 后端 (Python)            │
│                                          │
│  routers  →  services  →  providers     │
│                            ├── LLM      │
│                            ├── STT      │
│                            └── TTS      │
│                                          │
│               models (SQLAlchemy)        │
│                    │                     │
│               SQLite / PostgreSQL        │
└─────────────────────────────────────────┘
```

### 核心功能流

1. **管理后台（浏览器）**：用户通过 Vue SPA 创建/配置 AI 伙伴（Agent），设置其人格、声音、知识库
2. **设备端**：硬件设备通过 WebSocket 连接到后端，进行实时语音交互
3. **管道服务**：`pipeline.py` 组装 STT → LLM → TTS 的完整对话链路
4. **Provider 工厂**：通过配置 `llm_provider` / `stt_provider` / `tts_provider` 动态切换底层服务

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | Vue 3 + TypeScript |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| CSS | Tailwind CSS |
| 构建 | Vite |
| 测试 | Vitest |
| 后端框架 | FastAPI (Python) |
| ORM | SQLAlchemy 2.0 (异步) |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 迁移工具 | Alembic |
| AI 服务 | 阿里百炼 / DeepSeek / OpenAI Whisper / Edge TTS |
