import { Card } from '@/components/ui/card'
import type { EvidenceAnalysis } from '@/types'

interface EvidenceChainProps {
  evidence: string[]
  analysis?: EvidenceAnalysis
}

export function EvidenceChain({ evidence, analysis }: EvidenceChainProps) {
  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Evidence Chain</h3>
        <p className="text-sm text-gray-600 mt-1">Verification trail used to support the final diagnosis</p>
      </div>

      <div className="space-y-3">
        {evidence.map((item, idx) => (
          <div key={idx} className="flex gap-3">
            <div className="text-xs font-bold text-emerald-600 min-w-6">{idx + 1}</div>
            <p className="text-sm text-gray-700">{item}</p>
          </div>
        ))}
      </div>

      {analysis ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="rounded-lg bg-gray-50 p-4">
            <h4 className="text-sm font-semibold text-gray-900">Supporting Evidence</h4>
            <ul className="mt-2 space-y-2 text-sm text-gray-700">
              {analysis.supporting_evidence.length ? analysis.supporting_evidence.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                  <span>{item}</span>
                </li>
              )) : <li className="text-gray-500">None provided</li>}
            </ul>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <h4 className="text-sm font-semibold text-gray-900">Contradictions</h4>
            <ul className="mt-2 space-y-2 text-sm text-gray-700">
              {analysis.contradicting_evidence.length ? analysis.contradicting_evidence.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500" />
                  <span>{item}</span>
                </li>
              )) : <li className="text-gray-500">None provided</li>}
            </ul>
          </div>
        </div>
      ) : null}

      {analysis?.uncertainty_sources?.length ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Uncertainty Sources</h4>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            {analysis.uncertainty_sources.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-gray-400" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Card>
  )
}
