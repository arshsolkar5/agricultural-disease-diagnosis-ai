import { Card } from '@/components/ui/card'
import { formatNumber } from './reportUtils'
import type { PlannerAnalysis } from '@/types'

interface PlannerPanelProps {
  planner?: PlannerAnalysis
  executionPlan?: PlannerAnalysis['plan']
}

export function PlannerPanel({ planner, executionPlan = [] }: PlannerPanelProps) {
  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">Planner Output</h3>
          <p className="text-sm text-gray-600 mt-1">
            {planner?.analysis_source ? `Source: ${planner.analysis_source}` : 'Workflow steps prepared for the diagnosis pipeline'}
          </p>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {executionPlan.length} steps
        </div>
      </div>

      {executionPlan.length === 0 ? (
        <p className="text-sm text-gray-600">No planner output available yet.</p>
      ) : (
        <div className="space-y-3">
          {executionPlan.map((step) => (
            <div key={`${step.step}-${step.agent}`} className="rounded-lg border border-gray-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    Step {formatNumber(step.step)}{step.agent ? ` · ${step.agent}` : ''}
                  </p>
                  <p className="text-sm text-gray-600 mt-1">{step.action}</p>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-xs">
                {step.inputs && (
                  <span className="rounded-full bg-gray-100 px-2 py-1 text-gray-700">
                    Inputs: {Array.isArray(step.inputs) ? `${step.inputs.length} items` : typeof step.inputs === 'string' ? step.inputs : 'See details'}
                  </span>
                )}
                {step.outputs && (
                  <span className="rounded-full bg-gray-100 px-2 py-1 text-gray-700">
                    Outputs: {Array.isArray(step.outputs) ? `${step.outputs.length} items` : typeof step.outputs === 'string' ? step.outputs : 'See details'}
                  </span>
                )}
                {step.notes ? (
                  <span className="rounded-full bg-emerald-50 px-2 py-1 text-emerald-700">
                    Notes: {step.notes}
                  </span>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
