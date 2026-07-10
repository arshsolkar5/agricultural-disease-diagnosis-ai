import { useQuery } from '@tanstack/react-query'
import { useApi } from './useApi'

interface HealthStatus {
  status: string
  database: string
  agents: string
  version: string
}

interface AgentMetric {
  agent_name: string
  total_executions: number
  error_count: number
  success_rate: number
  average_latency_ms: number
  last_execution_time: string | null
  last_status: string | null
}

interface AgentsStatus {
  [key: string]: AgentMetric
}

export function useHealth() {
  const { request } = useApi()

  return useQuery<HealthStatus>({
    queryKey: ['health'],
    queryFn: () => request<HealthStatus>('get', '/health'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

export function useAgentsStatus() {
  const { request } = useApi()

  return useQuery<AgentsStatus>({
    queryKey: ['agents-status'],
    queryFn: () => request<AgentsStatus>('get', '/agents/status'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}
