import type { ApiService } from '@/types'
import { createMockApiService } from './mock'
import { createRealApiService } from './real'

function createApiService(): ApiService {
  const useMock = import.meta.env.VITE_USE_MOCK !== 'false'
  if (useMock) {
    console.log('[API] 使用 Mock 模式')
    return createMockApiService()
  }
  console.log('[API] 使用真实 API 模式 —', import.meta.env.VITE_API_BASE_URL)
  return createRealApiService()
}

export const apiService = createApiService()
