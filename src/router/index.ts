import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/agents',
  },
  {
    path: '/agents',
    name: 'Agents',
    component: () => import('@/views/AgentsView.vue'),
    meta: { title: 'AI 伙伴', subtitle: '管理你的 AI 角色配置' },
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/HistoryView.vue'),
    meta: { title: '历史记录', subtitle: '查看所有对话历史' },
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('@/views/DevicesView.vue'),
    meta: { title: '设备管理', subtitle: '管理已绑定的 AI 设备' },
  },
  {
    path: '/voice-library',
    name: 'VoiceLibrary',
    component: () => import('@/views/VoiceLibraryView.vue'),
    meta: { title: '声音库', subtitle: '为你的 AI 伙伴选择音色' },
  },
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/KnowledgeView.vue'),
    meta: { title: '知识库', subtitle: '管理 AI 伙伴的知识内容' },
  },
  {
    path: '/voiceprint',
    name: 'Voiceprint',
    component: () => import('@/views/VoiceprintView.vue'),
    meta: { title: '声纹识别', subtitle: '管理说话人声纹识别' },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { title: '我的', subtitle: '账号与系统设置' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/agents',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to, _from, next) => {
  const appTitle = import.meta.env.VITE_APP_TITLE ?? '明境 · AI 陪伴管理平台'
  document.title = to.meta.title
    ? `${to.meta.title} · ${appTitle}`
    : appTitle
  next()
})

export default router
