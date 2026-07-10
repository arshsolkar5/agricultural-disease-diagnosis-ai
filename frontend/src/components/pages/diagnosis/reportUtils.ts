import type {
  DiagnosisResponse,
  ReportContent,
  TreatmentRecommendation,
  TreatmentSource,
} from '@/types'

export function formatPercent(value?: number | null, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A'
  return `${(value * 100).toFixed(digits)}%`
}

export function formatNumber(value?: number | null, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A'
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export function formatCurrency(value?: number | null, digits = 0) {
  if (value === null || value === undefined || Number.isNaN(value)) return 'N/A'
  return `INR ${Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`
}

export function normalizeReportContent(diagnosis: DiagnosisResponse): ReportContent {
  return (
    diagnosis.report_analysis?.report ?? {
      title: 'AgriSense Crop Diagnosis Report',
      executive_summary: `Diagnosis suggests ${diagnosis.primary_disease}.`,
      key_findings: [
        `Primary diagnosis: ${diagnosis.primary_disease}`,
        `Confidence: ${formatPercent(diagnosis.confidence)}`,
        `Observations reviewed: ${diagnosis.observations.length}`,
      ],
      diagnosis_summary: `Verified diagnosis: ${diagnosis.primary_disease}`,
      treatment_summary: `${diagnosis.treatment_recommendations?.length ?? 0} treatment options prepared.`,
      market_summary: diagnosis.market_data?.recommendation || 'No market analysis available.',
      economics_summary: `${diagnosis.economics_analysis?.length ?? 0} economics line items analyzed.`,
      recommended_actions: [
        'Follow the top-ranked treatment plan.',
        'Monitor the crop closely for recovery.',
      ],
      follow_up_questions: diagnosis.follow_up_questions ?? [],
    }
  )
}

function renderList(items: string[]) {
  return items.length
    ? items.map((item) => `- ${item}`).join('\n')
    : '- None provided'
}

function renderTreatmentRecommendations(items: TreatmentRecommendation[] = []) {
  if (!items.length) return '- None provided'

  return items
      .map(
      (item, index) => [
        `${index + 1}. ${item.name}`,
        `   - Description: ${item.description}`,
        `   - Cost per acre: ${formatCurrency(item.cost_per_acre)}`,
        `   - Yield recovery: ${item.yield_recovery_percent == null ? 'N/A' : formatPercent(item.yield_recovery_percent / 100, 1)}`,
        `   - Days to recovery: ${formatNumber(item.days_to_recovery)}`,
        `   - Confidence: ${formatPercent(item.confidence)}`,
        `   - Rationale: ${item.rationale || 'N/A'}`,
        `   - Precautions: ${item.precautions?.length ? item.precautions.join('; ') : 'None provided'}`,
      ].join('\n')
    )
    .join('\n\n')
}

function renderRagEvidence(items: TreatmentSource[] = []) {
  if (!items.length) return '- None provided'

  return items
    .map((item, index) => {
      const excerpt = item.text ? item.text.slice(0, 300).replace(/\s+/g, ' ').trim() : 'N/A'
      return [
        `${index + 1}. ${item.title || item.document_title || item.source || 'Retrieved document'}`,
        `   - Source: ${item.document_source || item.source || 'N/A'}`,
        `   - Score: ${item.score !== undefined ? item.score.toFixed(3) : 'N/A'}`,
        `   - Excerpt: ${excerpt}${item.text && item.text.length > 300 ? '...' : ''}`,
      ].join('\n')
    })
    .join('\n\n')
}

export function buildReportMarkdown(diagnosis: DiagnosisResponse) {
  const report = normalizeReportContent(diagnosis)
  const plannerPlan = diagnosis.execution_plan ?? diagnosis.planner_analysis?.plan ?? []
  const economics = diagnosis.economics_analysis ?? []

  return `# ${report.title}

## Snapshot
- Diagnosis ID: ${diagnosis.diagnosis_id}
- Trace ID: ${diagnosis.trace_id}
- Crop type: ${diagnosis.crop_type}
- Primary disease: ${diagnosis.primary_disease}
- Confidence: ${formatPercent(diagnosis.confidence)}
- Image quality: ${formatPercent(diagnosis.image_quality_score)}
- Generated: ${new Date(diagnosis.created_at).toLocaleString()}

## Executive Summary
${report.executive_summary}

## Key Findings
${renderList(report.key_findings)}

## Vision Analysis
- Summary: ${diagnosis.vision_analysis?.summary || 'N/A'}
- Analysis source: ${diagnosis.vision_analysis?.analysis_source || diagnosis.analysis_source || 'N/A'}
- Uncertainties: ${renderList(diagnosis.vision_analysis?.uncertainties ?? [])}
- Quality notes: ${renderList(diagnosis.vision_analysis?.quality_notes ?? [])}
- Follow-up questions: ${renderList(diagnosis.follow_up_questions ?? [])}

## Observations
${diagnosis.observations.length
    ? diagnosis.observations
        .map(
          (obs, index) => [
            `${index + 1}. ${obs.category}`,
            `   - Description: ${obs.description}`,
            `   - Confidence: ${formatPercent(obs.confidence)}`,
            `   - Location: ${obs.location || 'N/A'}`,
            `   - Severity: ${obs.severity || 'N/A'}`,
            `   - Visible signs: ${obs.visible_signs?.length ? obs.visible_signs.join('; ') : 'N/A'}`,
            `   - Possible cause: ${obs.possible_cause || 'N/A'}`,
          ].join('\n')
        )
        .join('\n\n')
    : '- None provided'}

## Planner Output
- Analysis source: ${diagnosis.planner_analysis?.analysis_source || 'N/A'}
${plannerPlan
  .map(
    (step) =>
      `- Step ${step.step}: ${step.agent || 'N/A'} - ${step.action}\n  - Inputs: ${Array.isArray(step.inputs) ? step.inputs.join(', ') : 'N/A'}\n  - Outputs: ${Array.isArray(step.outputs) ? step.outputs.join(', ') : 'N/A'}`
  )
  .join('\n')}

## Diagnosis Reasoning
- Analysis source: ${diagnosis.diagnosis_analysis?.analysis_source || 'N/A'}
- Reasoning: ${diagnosis.diagnosis_analysis?.reasoning || 'N/A'}
- Next steps: ${renderList(diagnosis.diagnosis_analysis?.next_steps ?? [])}
- Disease candidates:
${diagnosis.disease_candidates
  .map(
    (candidate, index) =>
      `  ${index + 1}. ${candidate.disease} (${formatPercent(candidate.confidence)}) - ${candidate.reasoning || 'N/A'}`
  )
  .join('\n')}

## Evidence Chain
${diagnosis.evidence_chain.length ? diagnosis.evidence_chain.map((item) => `- ${item}`).join('\n') : '- None provided'}

## Treatment Recommendations
${renderTreatmentRecommendations(diagnosis.treatment_recommendations ?? [])}

## RAG Evidence
${renderRagEvidence(diagnosis.treatment_sources ?? [])}

## Market Analysis
- Price per quintal: ${formatCurrency(diagnosis.market_data?.current_price_per_quintal)}
- Trend: ${diagnosis.market_data?.market_trend || 'N/A'}
- Volatility: ${diagnosis.market_data?.price_volatility || 'N/A'}
- Recommendation: ${diagnosis.market_data?.recommendation || 'N/A'}

## Economics Analysis
${economics.length
    ? economics
        .map(
          (item, index) =>
            `${index + 1}. ${item.treatment}\n   - Cost per acre: ${formatCurrency(item.cost_per_acre)}\n   - Yield gain: ${formatNumber(item.expected_yield_gain_quintals, 2)} quintals\n   - Revenue gain: ${formatCurrency(item.revenue_gain_rupees)}\n   - Net profit: ${formatCurrency(item.net_profit_rupees)}\n   - ROI: ${formatNumber(item.roi_percent, 1)}%\n   - Break-even days: ${formatNumber(item.break_even_days, 0)}\n   - Confidence: ${formatPercent(item.confidence)}`
        )
        .join('\n\n')
    : '- None provided'}

## Generated Report
- Executive summary: ${report.executive_summary}
- Diagnosis summary: ${report.diagnosis_summary}
- Treatment summary: ${report.treatment_summary}
- Market summary: ${report.market_summary}
- Economics summary: ${report.economics_summary}
- Recommended actions: ${renderList(report.recommended_actions)}
- Follow-up questions: ${renderList(report.follow_up_questions)}

## Errors
${(diagnosis.errors ?? []).length ? (diagnosis.errors ?? []).map((item) => `- ${item}`).join('\n') : '- None provided'}
`
}
