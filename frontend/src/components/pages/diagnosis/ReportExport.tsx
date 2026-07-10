'use client'

import { Button } from '@/components/ui/button'
import type { DiagnosisResponse } from '@/types'
import { buildReportMarkdown, normalizeReportContent } from './reportUtils'

interface ReportExportProps {
  diagnosis: DiagnosisResponse
}

export function ReportExport({ diagnosis }: ReportExportProps) {
  const generateMarkdown = () => {
    try {
      const md = buildReportMarkdown(diagnosis)
      const blob = new Blob([md], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report-${diagnosis.diagnosis_id}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to generate markdown file:', error)
      alert('Failed to download markdown file. Please try again.')
    }
  }

  const generatePDF = () => {
    const report = normalizeReportContent(diagnosis)
    const printWindow = window.open('', '', 'width=800,height=600')
    if (!printWindow) return
    printWindow.document.write(`
      <html>
        <head>
          <title>Diagnosis Report</title>
          <style>
            * { box-sizing: border-box; }
            @page {
              size: A4 landscape;
              margin: 0.5cm;
            }
            body {
              font-family: Arial, sans-serif;
              font-size: 10px;
              color: #111827;
              margin: 0;
              padding: 10px;
            }
            h1 { font-size: 18px; color: #065f46; margin: 0 0 5px; }
            h2 { font-size: 12px; color: #065f46; margin: 5px 0; }
            table {
              width: 100%;
              border-collapse: collapse;
              font-size: 9px;
            }
            th, td {
              border: 1px solid #d1d5db;
              padding: 4px 6px;
              text-align: left;
              vertical-align: top;
            }
            th {
              background: #f3f4f6;
              font-weight: 600;
              color: #374151;
              white-space: nowrap;
            }
            .header-row th {
              background: #ecfdf5;
              color: #047857;
            }
            .badge {
              display: inline-block;
              padding: 2px 6px;
              border-radius: 9999px;
              background: #ecfdf5;
              color: #047857;
              font-size: 9px;
              font-weight: 600;
            }
            ul { margin: 0; padding-left: 12px; }
            li { margin: 2px 0; }
            .muted { color: #6b7280; }
            .footer {
              margin-top: 10px;
              color: #6b7280;
              font-size: 8px;
              text-align: center;
            }
          </style>
        </head>
        <body>
          <h1>${report.title}</h1>
          <p class="muted">Diagnosis ID: ${diagnosis.diagnosis_id} | Trace ID: ${diagnosis.trace_id} | Generated: ${new Date().toLocaleString()}</p>
          
          <table style="margin-top: 10px;">
            <tr class="header-row">
              <th colspan="4">Diagnosis Overview</th>
            </tr>
            <tr>
              <th>Primary Disease</th>
              <td colspan="3"><span class="badge">${diagnosis.primary_disease}</span></td>
            </tr>
            <tr>
              <th>Confidence</th>
              <td>${(diagnosis.confidence * 100).toFixed(1)}%</td>
              <th>Image Quality</th>
              <td>${(diagnosis.image_quality_score * 100).toFixed(1)}%</td>
            </tr>
            <tr>
              <th>Crop Type</th>
              <td>${diagnosis.crop_type}</td>
              <th>Created At</th>
              <td>${new Date(diagnosis.created_at).toLocaleString()}</td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="2">Executive Summary</th>
            </tr>
            <tr>
              <td colspan="2">${report.executive_summary}</td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th>Key Findings</th>
              <th>Recommended Actions</th>
            </tr>
            <tr>
              <td>
                <ul>
                  ${report.key_findings.map((item) => `<li>${item}</li>`).join('')}
                </ul>
              </td>
              <td>
                <ul>
                  ${report.recommended_actions.map((item) => `<li>${item}</li>`).join('')}
                </ul>
              </td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="2">Observations</th>
            </tr>
            <tr>
              <td colspan="2">
                <ul>
                  ${diagnosis.observations
                    .map((o) => `<li>${o.category}: ${o.description} (${(o.confidence * 100).toFixed(1)}%)</li>`)
                    .join('')}
                </ul>
              </td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="2">Planner Output</th>
            </tr>
            <tr>
              <td colspan="2">
                <ul>
                  ${(diagnosis.execution_plan || []).map((step) => `<li>Step ${step.step}: ${step.agent || 'N/A'} - ${step.action}</li>`).join('')}
                </ul>
              </td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="4">Treatment Recommendations</th>
            </tr>
            ${(diagnosis.treatment_recommendations || []).map(
              (item) => `
              <tr>
                <th>${item.name}</th>
                <td colspan="3">${item.description}</td>
              </tr>
              <tr>
                <th>Cost/Acre</th>
                <td>${item.cost_per_acre ?? 'N/A'}</td>
                <th>Yield Recovery</th>
                <td>${item.yield_recovery_percent ?? 'N/A'}%</td>
              </tr>
              <tr>
                <th>Days to Recovery</th>
                <td>${item.days_to_recovery ?? 'N/A'}</td>
                <th>Confidence</th>
                <td>${(item.confidence * 100).toFixed(1)}%</td>
              </tr>
              `
            ).join('')}
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="2">RAG Evidence</th>
            </tr>
            <tr>
              <td colspan="2">
                <ul>
                  ${(diagnosis.treatment_sources || [])
                    .map(
                      (item) =>
                        `<li>${item.title || item.document_title || item.source || 'Retrieved document'} (score: ${item.score !== undefined ? item.score.toFixed(3) : 'N/A'})</li>`
                    )
                    .join('')}
                </ul>
              </td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="4">Market Analysis</th>
            </tr>
            <tr>
              <th>Recommendation</th>
              <td colspan="3">${diagnosis.market_data?.recommendation || 'No market analysis available.'}</td>
            </tr>
            <tr>
              <th>Price/Quintal</th>
              <td>${diagnosis.market_data?.current_price_per_quintal ?? 'N/A'}</td>
              <th>Trend</th>
              <td>${diagnosis.market_data?.market_trend || 'N/A'}</td>
            </tr>
            <tr>
              <th>Volatility</th>
              <td colspan="3">${diagnosis.market_data?.price_volatility || 'N/A'}</td>
            </tr>
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="4">Economics Analysis</th>
            </tr>
            ${(diagnosis.economics_analysis || []).map(
              (item) => `
              <tr>
                <th>${item.treatment}</th>
                <td>ROI: ${item.roi_percent.toFixed(1)}%</td>
                <th>Net Profit</th>
                <td>INR ${item.net_profit_rupees.toLocaleString()}</td>
              </tr>
              `
            ).join('')}
          </table>

          <table style="margin-top: 5px;">
            <tr class="header-row">
              <th colspan="2">Generated Report Summaries</th>
            </tr>
            <tr>
              <th>Diagnosis</th>
              <td>${report.diagnosis_summary}</td>
            </tr>
            <tr>
              <th>Treatment</th>
              <td>${report.treatment_summary}</td>
            </tr>
            <tr>
              <th>Market</th>
              <td>${report.market_summary}</td>
            </tr>
            <tr>
              <th>Economics</th>
              <td>${report.economics_summary}</td>
            </tr>
          </table>

          <div class="footer">AgriSense AI Crop Diagnosis Report - Generated on ${new Date().toLocaleString()}</div>
        </body>
      </html>
    `)
    printWindow.document.close()
    printWindow.print()
  }

  return (
    <div className="flex gap-2">
      <Button variant="secondary" onClick={generateMarkdown}>
        Download Markdown
      </Button>
      <Button variant="secondary" onClick={generatePDF}>
        Print/PDF
      </Button>
    </div>
  )
}
