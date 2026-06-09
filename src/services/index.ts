import type { ApiService } from '@/types'
import { createMockApiService } from './mock'
import { createRealApiService } from './real'

function createApiService(): ApiService {
  const useMock = import.meta.env.VITE_USE_MOCK !== 'false'
  if (useMock) {
    return createMockApiService()
  }
  return createRealApiService()
}

export const apiService = createApiService()
