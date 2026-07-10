import { useMutation } from '@tanstack/react-query'
import { useApi } from './useApi'
import type { DiagnosisRequest, DiagnosisResponse } from '@/types'

export function useDiagnosis() {
  const { request } = useApi()

  const mutation = useMutation({
    mutationFn: async (payload: DiagnosisRequest): Promise<DiagnosisResponse> => {
      return request<DiagnosisResponse>('post', '/diagnosis', payload)
    },
  })

  return mutation
}
