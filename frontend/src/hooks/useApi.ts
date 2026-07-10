import { useCallback } from 'react'
import axios, { AxiosError } from 'axios'
import { API_URL } from '@/lib/constants'
import type { ApiError } from '@/types'

export function useApi() {
  const apiClient = axios.create({
    baseURL: API_URL,
    timeout: 300000, // 5 minutes to handle rate limiting delays
    headers: {
      'Content-Type': 'application/json',
    },
  })

  const request = useCallback(
    async <T,>(
      method: 'get' | 'post' | 'put' | 'delete',
      url: string,
      data?: unknown
    ): Promise<T> => {
      try {
        const response = await apiClient[method]<T>(url, data)
        return response.data
      } catch (error) {
        if (error instanceof AxiosError) {
          const apiError = error.response?.data as ApiError
          throw new Error(apiError?.detail || error.message)
        }
        throw error
      }
    },
    [apiClient]
  )

  return { request, apiClient }
}
