import { Card } from '@/components/ui/card'
import type { DiagnosisResponse } from '@/types'
import { normalizeReportContent, formatCurrency, formatNumber, formatPercent } from './reportUtils'
import type { ReactNode } from 'react'

interface ReportPanelProps {
  diagnosis: DiagnosisResponse
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-gray-200 p-4">
      <h4 className="text-sm font-semibold uppercase tracking-wide text-gray-500">{title}</h4>
      <div className="mt-3 text-sm text-gray-700">{children}</div>
    </section>
  )
}

export function ReportPanel({ diagnosis }: ReportPanelProps) {
  const report = normalizeReportContent(diagnosis)

  return (
    <Card className="p-6 space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold">{report.title}</h3>
          <p className="text-sm text-gray-600 mt-1">Generated report assembled from the full diagnosis workflow</p>
        </div>
        <div className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
          {diagnosis.report_analysis?.analysis_source || 'local'}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Diagnosis</p>
          <p className="mt-1 text-sm font-semibold">{diagnosis.primary_disease}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Confidence</p>
          <p className="mt-1 text-sm font-semibold">{formatPercent(diagnosis.confidence)}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Treatments</p>
          <p className="mt-1 text-sm font-semibold">{diagnosis.treatment_recommendations?.length ?? 0}</p>
        </div>
        <div className="rounded-lg bg-gray-50 p-4">
          <p className="text-xs text-gray-500">Economics</p>
          <p className="mt-1 text-sm font-semibold">{diagnosis.economics_analysis?.length ?? 0} lines</p>
        </div>
      </div>

      <Section title="Executive Summary">
        <p>{report.executive_summary}</p>
      </Section>

      <div className="grid gap-4 xl:grid-cols-2">
        <Section title="Key Findings">
          <ul className="space-y-2">
            {report.key_findings.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
        <Section title="Recommended Actions">
          <ul className="space-y-2">
            {report.recommended_actions.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Section title="Diagnosis Summary">
          <p>{report.diagnosis_summary}</p>
        </Section>
        <Section title="Treatment Summary">
          <p>{report.treatment_summary}</p>
        </Section>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <Section title="Market Summary">
          <p>{report.market_summary}</p>
          {diagnosis.market_data ? (
            <p className="mt-2 text-xs text-gray-500">
              Price {diagnosis.market_data.current_price_per_quintal ? formatCurrency(diagnosis.market_data.current_price_per_quintal) : 'Not available'} · Trend{' '}
              {diagnosis.market_data.market_trend || 'Unknown'} · Volatility {diagnosis.market_data.price_volatility || 'Unknown'}
            </p>
          ) : null}
        </Section>
        <Section title="Economics Summary">
          <p>{report.economics_summary}</p>
          {diagnosis.economics_analysis?.length ? (
            <p className="mt-2 text-xs text-gray-500">
              Highest ROI: {formatNumber(Math.max(...diagnosis.economics_analysis.map((item) => item.roi_percent)), 1)}%
            </p>
          ) : null}
        </Section>
      </div>

      {diagnosis.follow_up_questions?.length ? (
        <Section title="Follow-up Questions">
          <ul className="space-y-2">
            {diagnosis.follow_up_questions.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-emerald-600" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {diagnosis.errors?.length ? (
        <Section title="Errors">
          <ul className="space-y-2 text-red-700">
            {diagnosis.errors.map((item) => (
              <li key={item} className="flex gap-2">
                <span className="mt-1 h-1.5 w-1.5 rounded-full bg-red-500" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      <div className="text-xs text-gray-500">
        Generated on {new Date(diagnosis.created_at).toLocaleString()} · Diagnosis ID {diagnosis.diagnosis_id}
      </div>
    </Card>
  )
}
