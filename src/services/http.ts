import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types'

interface ValidationError {
  loc?: string[]
  msg?: string
  type?: string
}

interface ErrorResponseBody {
  detail?: ValidationError[] | string | unknown
}

function createHttpClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api',
    timeout: 15000,
  })

  instance.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = localStorage.getItem('auth_token')
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    (error: AxiosError) => Promise.reject(error),
  )

  instance.interceptors.response.use(
    (response) => {
      const body = response.data as ApiResponse
      if (body.code !== 0) {
        return Promise.reject(new Error(body.message ?? '请求失败'))
      }
      return response
    },
    (error: AxiosError) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
      if (error.response?.status === 403) {
        return Promise.reject(new Error('权限不足'))
      }
      if (error.response?.status === 404) {
        const body = error.response.data as ErrorResponseBody | undefined
        return Promise.reject(
          new Error(typeof body?.detail === 'string' ? body.detail : '资源不存在'),
        )
      }
      if (error.response?.status === 409) {
        const body = error.response.data as ErrorResponseBody | undefined
        return Promise.reject(
          new Error(typeof body?.detail === 'string' ? body.detail : '请求冲突'),
        )
      }
      if (error.response?.status === 422) {
        const body = error.response.data as ErrorResponseBody | undefined
        const detail = body?.detail
        const msg = Array.isArray(detail)
          ? detail.map((d: ValidationError) => d.msg ?? JSON.stringify(d)).join('；')
          : (detail as string) || '请求参数有误'
        return Promise.reject(new Error(msg))
      }
      if (error.response?.status && error.response.status >= 500) {
        return Promise.reject(new Error('服务器异常，请稍后再试'))
      }
      if (error.code === 'ECONNABORTED') {
        return Promise.reject(new Error('请求超时'))
      }
      if (!error.response) {
        return Promise.reject(new Error('网络连接失败，请检查网络'))
      }
      return Promise.reject(error)
    },
  )

  return instance
}

export const httpClient = createHttpClient()
