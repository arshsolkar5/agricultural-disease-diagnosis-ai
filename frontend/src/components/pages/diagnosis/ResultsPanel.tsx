import { Card } from '@/components/ui/card'
import type { DiagnosisResponse } from '@/types'
import { formatPercent } from './reportUtils'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface ResultsPanelProps {
  data: DiagnosisResponse
}

export function ResultsPanel({ data }: ResultsPanelProps) {
  const confidence = Math.round(data.confidence * 100)
  const followUpCount = data.follow_up_questions?.length ?? 0
  const candidateCount = data.disease_candidates?.length ?? 0
  const analysisSource = data.report_analysis?.analysis_source || data.analysis_source || data.vision_analysis?.analysis_source || 'local'

  // Prepare chart data for disease candidates
  const candidateChartData = data.disease_candidates?.map((candidate, index) => ({
    name: candidate.disease.length > 15 ? candidate.disease.substring(0, 15) + '...' : candidate.disease,
    fullName: candidate.disease,
    confidence: Math.round(candidate.confidence * 100),
    rank: candidate.rank
  })) || []

  const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']

  return (
    <Card className="p-6 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-emerald-600">{data.primary_disease}</h2>
          <p className="text-sm text-gray-600 mt-1">Primary diagnosis</p>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {analysisSource}
        </div>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <div className="flex-1">
          <div className="text-5xl font-bold">{confidence}%</div>
          <p className="text-sm text-gray-600">Confidence</p>
        </div>
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-emerald-600 transition-all"
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 pt-4 border-t">
        <div>
          <p className="text-xs text-gray-600">Image Quality</p>
          <p className="text-lg font-semibold">{formatPercent(data.image_quality_score)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Analyzed</p>
          <p className="text-sm text-gray-900">{new Date(data.created_at).toLocaleDateString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Candidate Diseases</p>
          <p className="text-lg font-semibold">{candidateCount}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Follow-up Questions</p>
          <p className="text-lg font-semibold">{followUpCount}</p>
        </div>
      </div>

      {candidateChartData.length > 1 && (
        <div className="pt-4 border-t">
          <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 mb-3">Disease Candidate Confidence</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={candidateChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: number, name: string, props: any) => [`${value}%`, props.payload.fullName]}
                labelStyle={{ color: '#374151' }}
              />
              <Bar dataKey="confidence" radius={[4, 4, 0, 0]}>
                {candidateChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Trace ID</p>
          <p className="mt-1 text-sm font-medium break-all text-gray-900">{data.trace_id}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Report Ready</p>
          <p className="mt-1 text-sm font-medium text-gray-900">
            {data.report_analysis?.report ? 'Yes' : 'Generated from structured workflow data'}
          </p>
        </div>
      </div>
    </Card>
  )
}
