import type { ApiService } from '@/types'
import { createRealApiService } from './real'

export const apiService: ApiService = createRealApiService()
