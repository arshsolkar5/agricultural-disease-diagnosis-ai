'use client'

import { motion } from 'framer-motion'
import { 
  Sprout, 
  Activity, 
  Cpu,
  Database,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp
} from 'lucide-react'
import Link from 'next/link'
import { useHealth, useAgentsStatus } from '@/hooks/useHealth'
import { Spinner } from '@/components/ui/spinner'

const quickActions = [
  {
    title: 'New Diagnosis',
    description: 'Upload plant image for AI analysis',
    href: '/diagnosis',
    icon: Sprout,
    color: 'emerald'
  },
  {
    title: 'System Status',
    description: 'View detailed system health',
    href: '/monitor',
    icon: Activity,
    color: 'blue'
  }
]

export default function DashboardPage() {
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()
  const { data: agents, isLoading: agentsLoading, error: agentsError } = useAgentsStatus()

  const systemStatus = health?.status || 'unknown'
  const dbStatus = health?.database || 'unknown'
  const agentsStatus = health?.agents || 'unknown'

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-emerald-600 bg-emerald-100'
      case 'degraded':
        return 'text-amber-600 bg-amber-100'
      case 'unhealthy':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return <CheckCircle className="w-5 h-5" />
      case 'unhealthy':
        return <XCircle className="w-5 h-5" />
      default:
        return <Clock className="w-5 h-5" />
    }
  }

  return (
    <main className="grid-container py-8">
      {/* Header */}
      <div className="col-span-12 mb-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="space-y-2">
            <h1 className="mb-2">Dashboard</h1>
            <p className="text-gray-700">Monitor system health and AI agent status</p>
          </div>
        </motion.div>
      </div>

      {/* System Health Status */}
      <div className="col-span-12 mb-8">
        <div className="grid gap-6 md:grid-cols-3">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Activity className="w-6 h-6 text-emerald-600" />
                  <h3 className="font-semibold">System Status</h3>
                </div>
                {healthLoading ? (
                  <Spinner />
                ) : (
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(systemStatus)}`}>
                    {getStatusIcon(systemStatus)}
                    <span className="capitalize">{systemStatus}</span>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-700">Overall system health status</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Database className="w-6 h-6 text-blue-600" />
                  <h3 className="font-semibold">Database</h3>
                </div>
                {healthLoading ? (
                  <Spinner />
                ) : (
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(dbStatus)}`}>
                    {getStatusIcon(dbStatus)}
                    <span className="capitalize">{dbStatus}</span>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-700">Database connection status</p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <Cpu className="w-6 h-6 text-purple-600" />
                  <h3 className="font-semibold">AI Agents</h3>
                </div>
                {healthLoading ? (
                  <Spinner />
                ) : (
                  <div className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(agentsStatus)}`}>
                    {getStatusIcon(agentsStatus)}
                    <span className="capitalize">{agentsStatus}</span>
                  </div>
                )}
              </div>
              <p className="text-sm text-gray-700">Multi-agent system status</p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="col-span-12 mb-8">
        <h2 className="mb-4">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {quickActions.map((action, index) => (
            <motion.div
              key={action.title}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <Link href={action.href}>
                <div className="card hover:shadow-lg hover:border-emerald-300 transition-all cursor-pointer h-full">
                  <div className={`p-3 rounded-lg bg-${action.color}-100 w-fit mb-4`}>
                    <action.icon className={`w-6 h-6 text-${action.color}-600`} />
                  </div>
                  <h3 className="font-semibold mb-2">{action.title}</h3>
                  <p className="text-sm text-gray-700">{action.description}</p>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

    </main>
  )
}
