import { Card } from '@/components/ui/card'
import type { Observation, VisionAnalysis } from '@/types'
import { formatPercent } from './reportUtils'

interface ObservationsPanelProps {
  observations: Observation[]
  visionAnalysis?: VisionAnalysis
}

export function ObservationsPanel({ observations, visionAnalysis }: ObservationsPanelProps) {
  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Visual Observations</h3>
        <p className="text-sm text-gray-600 mt-1">
          {visionAnalysis?.summary || 'Structured findings extracted from the uploaded image'}
        </p>
      </div>

      {visionAnalysis ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-500">Vision Confidence</p>
            <p className="mt-1 text-lg font-semibold">{formatPercent(visionAnalysis.confidence)}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-500">Image Quality</p>
            <p className="mt-1 text-lg font-semibold">{formatPercent(visionAnalysis.image_quality_score)}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-500">Follow-up</p>
            <p className="mt-1 text-lg font-semibold">{visionAnalysis.needs_follow_up ? 'Yes' : 'No'}</p>
          </div>
          <div className="rounded-lg bg-gray-50 p-4">
            <p className="text-xs text-gray-500">Analysis Source</p>
            <p className="mt-1 text-lg font-semibold capitalize">{visionAnalysis.analysis_source || 'N/A'}</p>
          </div>
        </div>
      ) : null}

      <div className="space-y-3">
        {observations.map((obs, idx) => (
          <div key={idx} className="flex items-start gap-3 rounded-lg border border-gray-200 p-4">
            <div className="mt-1 h-2 w-2 rounded-full bg-emerald-600" />
            <div className="flex-1">
              <p className="font-medium text-gray-900 capitalize">{obs.category}</p>
              <p className="text-sm text-gray-600 mt-1">{obs.description}</p>
              <p className="text-xs text-emerald-600 mt-1">
                Confidence: {Math.round(obs.confidence * 100)}%
              </p>
              <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-700">
                {obs.location ? <span className="rounded-full bg-gray-100 px-2 py-1">Location: {obs.location}</span> : null}
                {obs.severity ? <span className="rounded-full bg-gray-100 px-2 py-1">Severity: {obs.severity}</span> : null}
                {obs.possible_cause ? <span className="rounded-full bg-gray-100 px-2 py-1">Cause: {obs.possible_cause}</span> : null}
              </div>
              {obs.visible_signs?.length ? (
                <p className="mt-2 text-xs text-gray-500">
                  Visible signs: {obs.visible_signs.join(', ')}
                </p>
              ) : null}
            </div>
          </div>
        ))}
      </div>

      {visionAnalysis?.uncertainties?.length ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Uncertainties</h4>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            {visionAnalysis.uncertainties.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-amber-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {visionAnalysis?.quality_notes?.length ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Quality Notes</h4>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            {visionAnalysis.quality_notes.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Card>
  )
}
