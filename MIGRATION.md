# 迁移指南：从单文件 HTML → Vue 3 工程

> 本文档描述从 `mingjing_desktop.html`（单文件 2288 行）迁移到 `mingjing-admin`（Vue 3 + TypeScript 工程）的步骤与注意事项。

## 迁移总览

| 维度 | 原 HTML | 新工程 | 变化 |
|------|---------|--------|------|
| 文件数 | 1 | 60+ | 模块化拆分 |
| 页面切换 | `el.style.display = 'block'` | Vue Router `router-view` | URL 可导航 |
| 弹窗管理 | `onclick="showModal('x')"` | `uiStore.openModal(id)` | 统一管理器 |
| 数据 | HTML 内联硬编码 | Pinia Store → API → Mock/Real | 一环境变量切换 |
| 样式 | 全局 `<style>` 块 | `<style scoped>` + CSS Variables + Tailwind | 样式隔离 |
| 类型 | 无 | TypeScript Strict | 全链路类型安全 |

## 迁移步骤（按优先级）

### 1. 环境准备

```bash
pnpm install
cp .env.example .env.local           # 复制环境变量模板
# 编辑 .env.local，确保 VITE_USE_MOCK=true
pnpm dev                              # 启动开发服务器
```

### 2. 验证 Mock 模式完整性

- [ ] 访问 `/agents` — 验证角色列表正常加载（3 个角色卡片）
- [ ] 点击「新建角色」— 验证弹窗打开，人设/声音/知识库三 Tab 正常
- [ ] 填写名称 + 提示词，保存 — 验证列表新增角色
- [ ] 访问 `/history` — 验证对话列表 + 消息详情
- [ ] 访问 `/devices` — 验证设备卡片（2 个设备）
- [ ] 点击「添加设备」— 验证码弹窗
- [ ] 访问 `/voice-library` — 验证音色 Tab 切换 + 克隆 Banner
- [ ] 点击「克隆我的声音」— 验证三步向导流程
- [ ] 访问 `/knowledge` — 验证系统/自定义知识库 + 记忆开关
- [ ] 访问 `/voiceprint` — 验证说话人列表
- [ ] 访问 `/profile` — 验证账号卡片 + 通知开关
- [ ] 浏览器前进/后退 — 验证路由状态保持

### 3. 对接真实 API

```bash
# .env.local
VITE_USE_MOCK=false
VITE_API_BASE_URL=https://your-api-server.com/api
```

**API 端点清单**（`services/real.ts` 中定义）：

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/agents` | 角色列表 |
| `GET` | `/agents/:id` | 角色详情 |
| `POST` | `/agents` | 创建角色 |
| `PUT` | `/agents/:id` | 更新角色 |
| `DELETE` | `/agents/:id` | 删除角色 |
| `GET` | `/devices` | 设备列表 |
| `POST` | `/devices/bind` | 设备绑定 |
| `DELETE` | `/devices/:id/unbind` | 设备解绑 |
| `POST` | `/devices/:id/upgrade` | 固件升级 |
| `PUT` | `/devices/:id/role` | 角色分配 |
| `GET` | `/voices` | 音色列表 |
| `POST` | `/voices/clone` | 声音克隆（multipart） |
| `GET` | `/knowledge` | 知识库列表 |
| `PUT` | `/knowledge/:id/toggle` | 开关知识库 |
| `PUT` | `/knowledge/memory/toggle` | 自动记忆开关 |
| `POST` | `/knowledge/upload` | 上传文件（multipart） |
| `GET` | `/voiceprint` | 声纹列表 |
| `GET` | `/history` | 对话历史列表 |
| `GET` | `/history/:id` | 对话详情 |
| `GET` | `/user/profile` | 用户资料 |
| `PUT` | `/user/notification` | 通知设置 |

**API 响应格式**：

```json
{
  "code": 0,
  "message": "ok",
  "data": { "... 业务数据 ..." },
  "timestamp": 1714924800000
}
```

### 4. 补充：从原 HTML 提取缺失业务逻辑

以下功能在原 HTML 中已存在，但以简要形式处理，需按实际产品需求深化：

| 功能 | 当前处理 | 需深化 |
|------|---------|--------|
| 声音克隆校验 | 随机 80% 成功率 | 真实声纹验证 API |
| 知识库上传 | 占位 `new File([])` | 真实文件选择 + 上传 |
| OTA 固件升级 | 直接更新 version | 加入升级进度回调 |
| 声纹样本选择 | 硬编码下拉选项 | 对接真实语音消息 API |
| 角色头像 | 固定 emoji | 支持自定义图片上传 |

## 目录映射对照

```
原 HTML 概念          →  新工程文件

# 页面
main-area 内 tab 切换  →  src/views/*View.vue (7个页面)
sidebar 导航            →  src/components/layout/Sidebar.vue
topbar                  →  src/components/layout/TopBar.vue

# 弹窗
agent-config 弹窗       →  src/components/modals/AgentConfigModal.vue
add-device 弹窗         →  src/components/modals/AddDeviceModal.vue
unbind-confirm 弹窗     →  src/components/modals/UnbindConfirmModal.vue
clone-voice 弹窗        →  src/components/modals/CloneVoiceModal.vue
add-speaker 弹窗        →  src/components/modals/AddSpeakerModal.vue
kb-new 弹窗             →  src/components/modals/KbNewModal.vue
agent-device 弹窗       →  src/components/modals/AgentDeviceModal.vue

# 数据
agentsData 数组         →  src/store/agents.ts (Pinia)
devicesData 数组        →  src/store/devices.ts (Pinia)
voicesData 数组         →  src/services/mock.ts
knowledgeData 数组      →  src/services/mock.ts
speakersData 数组       →  src/services/mock.ts

# 工具
showToast()             →  uiStore.showToast()
formatTimer()           →  src/composables/useVoiceRecord.ts
showModal() / hideModal() →  uiStore.openModal() / uiStore.closeModal()
```

## 测试清单

### 功能测试

- [ ] 角色 CRUD（创建 / 编辑 / 删除）
- [ ] 设备绑定 / 解绑 / OTA / 角色分配
- [ ] 音色选择 / 试听 / 克隆三步流程
- [ ] 知识库启用/禁用 / 记忆开关
- [ ] 声纹注册 / 删除
- [ ] 对话列表 / 消息详情
- [ ] 通知开关

### 非功能测试

- [ ] 路由前进/后退不丢失状态
- [ ] Mock/Real 模式切换无报错
- [ ] 表单校验 (空名称/短提示词/非数字验证码)
- [ ] Toast 消息自动消失
- [ ] ESC 键关闭弹窗
- [ ] 遮罩点击关闭弹窗
- [ ] 页面刷新保持路由
- [ ] `<script setup>` 中无 `innerHTML` / `onclick=`
- [ ] 浏览器 DevTools 无 Vue warn / error

## 风险应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 后端 API 响应格式与 `ApiResponse<T>` 不一致 | 所有请求报错 | 在 `services/real.ts` 的 `unwrap()` 中添加格式适配层 |
| Tailwind v3 → v4 迁移 | 样式批量失效 | 固定 v3 版本号，迁移时使用 `@tailwindcss/upgrade` |
| TypeScript Strict 模式兼容 | 类型错误阻塞构建 | 首选修复类型声明，最后才使用 `// @ts-expect-error` |
| 动态路由数据懒加载失败 | 页面白屏 | 所有异步操作在 Store 中添加 `loading`/`error` 状态处理 |
| pnpm → npm 环境差异 | 依赖安装失败 | 可使用 `npm install` 替代，但推荐 `pnpm` 以获得 `frozen-lockfile` 支持 |

## 开发工作流

```bash
# 日常开发（Mock 模式）
pnpm dev

# 提交前检查
pnpm lint && pnpm typecheck && pnpm test

# 通过 husky + lint-staged 自动执行
git commit -m "feat: ..."
```
