# 明境 · AI 陪伴管理平台

> AI Companion Management Platform — 生产级 Vue 3 + TypeScript 前端工程

## 项目简介

「明境」是一个 AI 陪伴玩偶的后端管理平台，以网页的形式提供 AI 伙伴（角色）创建与配置、设备管理、声音库、
知识库、声纹识别等核心功能的设置。玩偶芯片采用ESP32，上接麦克风、扬声器、开关、说话按钮（长按说话，松手发送）、电池。无显示屏，防低龄用户沉迷。

### 核心业务模块

| 模块 | 说明 |
|------|------|
| AI 伙伴 | 角色创建、提示词模板配置、声音/知识库绑定、设备分配 |
| 历史记录 | 对话列表浏览、消息详情查看、按角色/时间筛选 |
| 设备管理 | 设备绑定/解绑、OTA 升级、角色分配、状态监控 |
| 声音库 | 预设音色选择（女声/男声/多语言）、声音克隆（三步流程） |
| 知识库 | 系统内置/自定义知识库管理、自动记忆开关 |
| 声纹识别 | 说话人注册、声纹样本管理 |
| 账号设置 | 隐私、通知、版本信息 |

## 技术栈

| 类别 | 选型 | 说明 |
|------|------|------|
| 构建工具 | Vite 5+ | 极速 HMR，ESBuild 预构建 |
| 框架 | Vue 3 (Composition API) | `<script setup>` + TypeScript |
| 类型系统 | TypeScript (Strict) | 全链路类型安全 |
| 状态管理 | Pinia | 模块化 Store，支持 DevTools |
| 路由 | Vue Router 4 | History 模式 + 路由懒加载 |
| 样式方案 | Tailwind CSS + CSS Variables | 基于原设计系统的变量迁移 |
| 网络请求 | Axios + Mock 适配器 | 拦截器、错误格式化、环境切换 |
| 代码规范 | ESLint + Prettier | AirBnb 风格 + 自动修正 |
| 测试 | Vitest + Vue Test Utils | 单元测试覆盖核心逻辑 |
| Git Hooks | Husky + lint-staged | 提交前自动 Lint/格式化 |

## 快速开始

```bash
# 安装依赖
pnpm install

# 启动开发服务器（默认 Mock 模式）
pnpm dev

# 以真实 API 模式启动
pnpm dev:real

# 构建生产版本
pnpm build

# 预览生产构建
pnpm preview

# 运行单元测试
pnpm test

# 代码检查
pnpm lint

# 代码格式化
pnpm format
```

## 目录结构

```
src/
├── main.ts                 # 入口文件
├── App.vue                 # 根组件
├── assets/                 # 静态资源（图标、图片）
├── components/             # 基础 UI 组件
│   └── ui/                 # Button / Modal / Card / Switch / StatusBadge
├── views/                  # 页面级组件
│   ├── AgentsView.vue      # AI 伙伴管理
│   ├── HistoryView.vue     # 历史记录
│   ├── DevicesView.vue     # 设备管理
│   ├── VoiceLibraryView.vue# 声音库
│   ├── KnowledgeView.vue   # 知识库
│   ├── VoiceprintView.vue  # 声纹识别
│   └── ProfileView.vue     # 账号设置
├── router/                 # 路由配置 + 守卫
│   └── index.ts
├── store/                  # Pinia 状态模块
│   ├── roles.ts
│   ├── devices.ts
│   ├── user.ts
│   └── ui.ts
├── services/               # API 层
│   ├── http.ts             # Axios 实例 + 拦截器
│   ├── mock.ts             # Mock 适配器
│   └── api/                # 业务 API 函数
├── composables/            # 组合式函数
│   ├── useModal.ts         # 弹窗管理器
│   ├── useVoiceRecord.ts   # 录音/声音克隆
│   ├── useDeviceBind.ts    # 设备绑定
│   └── useFormValidator.ts # 表单校验
├── utils/                  # 纯函数工具
│   ├── format.ts           # 时间格式化
│   ├── debounce.ts         # 防抖
│   └── guards.ts           # 类型守卫
├── types/                  # TS 类型定义
│   ├── index.ts            # 业务模型
│   ├── api.d.ts            # API 请求/响应类型
│   └── models.d.ts         # 领域模型
└── styles/                 # 全局样式
    ├── variables.css       # CSS 变量（原设计系统迁移）
    └── reset.css           # Reset + base
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `VITE_USE_MOCK` | 是否启用 Mock 数据 | `true` |
| `VITE_API_BASE_URL` | 真实 API 地址 | `http://localhost:3000/api` |
| `VITE_APP_TITLE` | 应用标题 | `明境 · AI 陪伴管理平台` |

## 许可证

Private — All rights reserved.
