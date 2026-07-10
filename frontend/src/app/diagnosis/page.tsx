'use client'

import { useState } from 'react'
import { useDiagnosis } from '@/hooks/useDiagnosis'
import { useDiagnosisStore } from '@/store/diagnosis'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Spinner } from '@/components/ui/spinner'
import { ResultsPanel } from '@/components/pages/diagnosis/ResultsPanel'
import { ObservationsPanel } from '@/components/pages/diagnosis/ObservationsPanel'
import { EvidenceChain } from '@/components/pages/diagnosis/EvidenceChain'
import { TreatmentTable } from '@/components/pages/diagnosis/TreatmentTable'
import { EconomicsChart } from '@/components/pages/diagnosis/EconomicsChart'
import { ReportExport } from '@/components/pages/diagnosis/ReportExport'
import { PlannerPanel } from '@/components/pages/diagnosis/PlannerPanel'
import { RagEvidencePanel } from '@/components/pages/diagnosis/RagEvidencePanel'
import { MarketAnalysisPanel } from '@/components/pages/diagnosis/MarketAnalysisPanel'
import { ReportPanel } from '@/components/pages/diagnosis/ReportPanel'
import { CROP_TYPES } from '@/lib/constants'

function SearchableSelect({ value, onChange, options, placeholder }: {
  value: string
  onChange: (value: string) => void
  options: readonly string[]
  placeholder: string
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  
  const filteredOptions = options.filter(option => 
    option.toLowerCase().includes(searchTerm.toLowerCase())
  )
  
  const displayValue = value || placeholder
  
  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="input-base w-full text-left flex items-center justify-between"
      >
        <span>{displayValue === 'auto_detect' ? 'Auto Detect' : displayValue.charAt(0).toUpperCase() + displayValue.slice(1)}</span>
        <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          )}
        </svg>
      </button>
      
      {isOpen && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          <div className="p-2 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search crops..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
          <div className="py-1">
            {filteredOptions.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => {
                  onChange(option)
                  setIsOpen(false)
                  setSearchTerm('')
                }}
                className={`w-full text-left px-3 py-2 text-sm hover:bg-emerald-50 ${
                  value === option ? 'bg-emerald-100 font-semibold' : ''
                }`}
              >
                {option === 'auto_detect' ? 'Auto Detect' : option.charAt(0).toUpperCase() + option.slice(1)}
              </button>
            ))}
            {filteredOptions.length === 0 && (
              <div className="px-3 py-2 text-sm text-gray-500">No crops found</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function DiagnosisPage() {
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string>('')
  const {
    selectedCropType,
    farmerId,
    location,
    additionalContext,
    latestDiagnosis,
    setCropType,
    setFarmerId,
    setLocation,
    setAdditionalContext,
    setLatestDiagnosis,
  } = useDiagnosisStore()
  const { mutate, isPending, data, error } = useDiagnosis()
  const diagnosis = data ?? latestDiagnosis
  const evidenceAnalysis = diagnosis
    ? {
        verified_diagnosis: diagnosis.primary_disease,
        final_confidence: diagnosis.confidence,
        evidence_chain: diagnosis.evidence_chain,
        supporting_evidence: [
          ...(diagnosis.diagnosis_analysis?.reasoning ? [diagnosis.diagnosis_analysis.reasoning] : []),
          ...diagnosis.observations.map((obs) => `${obs.category}: ${obs.description} (${(obs.confidence * 100).toFixed(1)}% confidence)`),
          ...diagnosis.disease_candidates.slice(0, 2).map((candidate) => `${candidate.disease}: ${candidate.reasoning || 'Matched symptoms'}`),
          ...(diagnosis.treatment_sources?.slice(0, 2).map((source) => `RAG Source: ${source.title || source.document_title || 'Document'} (score: ${source.score?.toFixed(3) || 'N/A'})`) || []),
        ],
        contradicting_evidence: diagnosis.diagnosis_analysis?.uncertainties ?? [],
        uncertainty_sources: [
          ...(diagnosis.vision_analysis?.uncertainties ?? []),
          ...(diagnosis.diagnosis_analysis?.uncertainties ?? []),
        ],
        alternative_diseases: diagnosis.disease_candidates.slice(1, 3).map((candidate) => ({
          disease: candidate.disease,
          confidence: candidate.confidence,
          reason_ranked_lower: candidate.reasoning || 'Ranked lower by the diagnosis agent',
        })),
        reasoning: diagnosis.diagnosis_analysis?.reasoning || '',
        analysis_source: diagnosis.diagnosis_analysis?.analysis_source,
      }
    : undefined

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setImageFile(file)
      const reader = new FileReader()
      reader.onload = (e) => setPreview(e.target?.result as string)
      reader.readAsDataURL(file)
    }
  }

  const handleDiagnosis = async () => {
    if (!imageFile) return
    const reader = new FileReader()
    reader.onload = (e) => {
      const base64 = (e.target?.result as string).split(',')[1]
      mutate(
        {
          image_base64: base64,
          crop_type: selectedCropType,
          farmer_id: farmerId || undefined,
          location: location || undefined,
          additional_context: additionalContext || undefined,
        },
        {
          onSuccess: (result) => {
            console.log('[DEBUG] Frontend received result:', result)
            console.log('[DEBUG] Result keys:', Object.keys(result))
            console.log('[DEBUG] primary_disease:', result.primary_disease)
            setLatestDiagnosis(result)
          },
          onError: (error) => {
            console.error('[DEBUG] Frontend error:', error)
          },
        }
      )
    }
    reader.readAsDataURL(imageFile)
  }

  return (
    <div className="grid-container space-y-8 py-8">
      <div className="col-span-12">
        <h1 className="text-5xl font-bold">Diagnosis</h1>
        <p className="mt-2 text-gray-600">Upload crop image for AI analysis</p>
      </div>

      <div className="col-span-12 grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <Card className="p-8 sticky top-24">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Crop Type</label>
                <div className="mt-1">
                  <SearchableSelect
                    value={selectedCropType}
                    onChange={setCropType}
                    options={CROP_TYPES}
                    placeholder="Select crop type"
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">Default: Auto Detect (AI will identify crop from image)</p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <Input
                  label="Farmer ID"
                  value={farmerId ?? ''}
                  onChange={(e) => setFarmerId(e.target.value || null)}
                  placeholder="Optional"
                />
                <Input
                  label="Location"
                  value={location ?? ''}
                  onChange={(e) => setLocation(e.target.value || null)}
                  placeholder="Optional"
                />
              </div>

              <div>
                <label htmlFor="additional-context" className="block text-sm font-medium text-gray-700">
                  Additional Context
                </label>
                <textarea
                  id="additional-context"
                  value={additionalContext ?? ''}
                  onChange={(e) => setAdditionalContext(e.target.value || null)}
                  placeholder="Describe symptoms, previous treatments, weather conditions, or any relevant notes..."
                  className="input-base mt-1 w-full min-h-[100px] resize-y"
                  rows={4}
                />
                <p className="mt-1 text-xs text-gray-500">Optional: Helps improve diagnosis accuracy</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Upload Image</label>
                <div className="relative mt-2">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="absolute inset-0 opacity-0 cursor-pointer"
                  />
                  <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center">
                    {preview ? (
                      <img src={preview} alt="preview" className="mx-auto h-40 w-40 object-cover rounded" />
                    ) : (
                      <p className="text-gray-600 text-sm">Click or drag image here</p>
                    )}
                  </div>
                </div>
              </div>

              <Button onClick={handleDiagnosis} disabled={!imageFile || isPending} className="w-full">
                {isPending ? <Spinner size="sm" /> : 'Analyze Image'}
              </Button>
            </div>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {isPending && (
            <Card className="p-12 space-y-4">
              <div className="flex items-center gap-4">
                <Spinner size="lg" />
                <div>
                  <p className="text-lg font-semibold">Running full diagnosis pipeline</p>
                  <p className="text-sm text-gray-600">
                    Vision, planning, diagnosis, evidence, RAG, treatment, market, economics, and report generation are in progress.
                  </p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {['Vision', 'Planner', 'Diagnosis', 'Evidence', 'RAG', 'Treatment', 'Market', 'Economics', 'Report'].map((step) => (
                  <div key={step} className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700">
                    {step}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {diagnosis && (
            <>
              <ResultsPanel data={diagnosis} />
              <PlannerPanel planner={diagnosis.planner_analysis} executionPlan={diagnosis.execution_plan} />
              <ObservationsPanel observations={diagnosis.observations} visionAnalysis={diagnosis.vision_analysis} />
              <EvidenceChain evidence={diagnosis.evidence_chain} analysis={evidenceAnalysis} />
              <RagEvidencePanel sources={diagnosis.treatment_sources} />
              <TreatmentTable treatments={diagnosis.treatment_recommendations} />
              <MarketAnalysisPanel marketData={diagnosis.market_data} />
              <EconomicsChart data={diagnosis.economics_analysis} />
              <ReportPanel diagnosis={diagnosis} />
              <ReportExport diagnosis={diagnosis} />
            </>
          )}

        </div>
      </div>
    </div>
  )
}
