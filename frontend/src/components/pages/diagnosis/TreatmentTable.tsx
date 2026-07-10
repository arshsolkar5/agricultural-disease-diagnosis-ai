import { Card } from '@/components/ui/card'
import type { TreatmentRecommendation } from '@/types'
import { formatCurrency, formatNumber, formatPercent } from './reportUtils'

interface TreatmentTableProps {
  treatments?: TreatmentRecommendation[]
}

export function TreatmentTable({ treatments = [] }: TreatmentTableProps) {
  return (
    <Card className="p-6 space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Recommended Treatments</h3>
        <p className="text-sm text-gray-600 mt-1">Ranked treatment guidance with costs, recovery, and precautions</p>
      </div>
      {treatments.length === 0 ? (
        <p className="text-gray-600 text-sm">No treatment data available.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr className="text-left text-xs font-semibold text-gray-700">
                <th className="pb-3">Treatment</th>
                <th className="pb-3">Cost</th>
                <th className="pb-3">Recovery</th>
                <th className="pb-3">Timeline</th>
                <th className="pb-3">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {treatments.map((t, idx) => (
                <tr key={`${t.name}-${idx}`} className="border-b last:border-0 align-top">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-gray-900">{t.name}</div>
                    <p className="mt-1 text-xs text-gray-500">{t.description}</p>
                    {t.rationale ? <p className="mt-1 text-xs text-gray-500">Why: {t.rationale}</p> : null}
                  </td>
                  <td className="py-3">{formatCurrency(t.cost_per_acre)}</td>
                  <td className="py-3">
                    {t.yield_recovery_percent == null ? 'N/A' : formatPercent(t.yield_recovery_percent / 100)}
                  </td>
                  <td className="py-3">{t.days_to_recovery == null ? 'N/A' : `${formatNumber(t.days_to_recovery)}d`}</td>
                  <td className="py-3">
                    <div className="font-medium text-gray-900">{formatPercent(t.confidence)}</div>
                    <div className="text-xs text-gray-500">
                      {idx === 0 ? 'Top recommendation' : 'Alternative'}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {treatments.some((item) => item.precautions?.length) ? (
        <div>
          <h4 className="text-sm font-semibold text-gray-900">Precautions</h4>
          <ul className="mt-2 space-y-2 text-sm text-gray-700">
            {treatments.flatMap((item) => item.precautions.map((precaution) => `${item.name}: ${precaution}`)).map((item) => (
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
