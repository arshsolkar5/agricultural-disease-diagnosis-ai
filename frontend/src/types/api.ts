export interface DiagnosisRequest {
  image_base64: string
  crop_type: string
  farmer_id?: string
  location?: string
  additional_context?: string
}

export interface Observation {
  category: string
  confidence: number
  description: string
  location?: string | null
  severity?: string | null
  visible_signs?: string[]
  possible_cause?: string | null
  affected_area_percent?: number | null
  bounding_box?: {
    x: number
    y: number
    w: number
    h: number
  } | null
}

export interface DiseaseCandidate {
  disease: string
  confidence: number
  rank: number
  reasoning?: string
  matched_observations?: string[]
  uncertainties?: string[]
  symptom_matches?: number
}

export interface PlannerStep {
  step: number
  agent: string
  action: string
  inputs?: string[]
  outputs?: string[]
  input?: string
  output?: string
  notes?: string
}

export interface PlannerAnalysis {
  plan: PlannerStep[]
  analysis_source?: string
  crop_type?: string
}

export interface VisionAnalysis {
  crop_type?: string | null
  image_quality_score: number
  confidence: number
  observations: Observation[]
  uncertainties: string[]
  follow_up_questions: string[]
  needs_follow_up: boolean
  summary: string
  quality_notes: string[]
  analysis_source?: string
  image_hash?: string
  original_hash?: string
  image_bytes?: number
  preprocessed_bytes?: number
  gemini_model?: string
  cache_hit?: boolean
  gemini_error?: string
  created_at?: string
}

export interface DiagnosisAnalysis {
  crop_type?: string | null
  primary_disease?: string | null
  confidence: number
  disease_candidates: DiseaseCandidate[]
  uncertainties: string[]
  reasoning: string
  next_steps: string[]
  analysis_source?: string
}

export interface EvidenceAnalysis {
  verified_diagnosis?: string | null
  final_confidence: number
  evidence_chain: string[]
  supporting_evidence: string[]
  contradicting_evidence: string[]
  uncertainty_sources: string[]
  alternative_diseases: Array<{
    disease: string
    confidence: number
    reason_ranked_lower: string
  }>
  reasoning: string
  analysis_source?: string
}

export interface TreatmentRecommendation {
  name: string
  description: string
  cost_per_acre?: number | null
  yield_recovery_percent?: number | null
  days_to_recovery?: number | null
  confidence: number
  rationale: string
  precautions: string[]
}

export interface TreatmentSource {
  text?: string
  title?: string
  source?: string
  score?: number
  semantic_score?: number
  lexical_score?: number
  distance?: number
  embedding_id?: number
  document_title?: string
  document_source?: string
}

export interface MarketData {
  crop_type?: string
  location?: string
  current_price_per_quintal?: number
  market_trend?: string
  price_volatility?: string
  recommendation?: string
  confidence?: number
  uncertainties?: string[]
  analysis_source?: string
}

export interface EconomicsLineItem {
  treatment: string
  cost_per_acre: number
  expected_yield_gain_quintals: number
  revenue_gain_rupees: number
  net_profit_rupees: number
  roi_percent: number
  break_even_days: number
  confidence: number
}

export interface EconomicsAnalysis {
  analysis: EconomicsLineItem[]
  summary?: string
  assumptions?: string[]
  analysis_source?: string
}

export interface ReportContent {
  title: string
  executive_summary: string
  key_findings: string[]
  diagnosis_summary: string
  treatment_summary: string
  market_summary: string
  economics_summary: string
  recommended_actions: string[]
  follow_up_questions: string[]
}

export interface ReportAnalysis {
  report?: ReportContent
  analysis_source?: string
}

export interface AgentRuntimeStatus {
  agent_name: string
  total_executions: number
  error_count: number
  success_rate: number
  average_latency_ms: number
  last_execution_time: string | null
  last_status: string | null
}

export interface AgentStatusResponse {
  vision: AgentRuntimeStatus
  diagnosis: AgentRuntimeStatus
  evidence: AgentRuntimeStatus
  planner: AgentRuntimeStatus
  rag: AgentRuntimeStatus
  treatment: AgentRuntimeStatus
  market: AgentRuntimeStatus
  economics: AgentRuntimeStatus
  report: AgentRuntimeStatus
}

export interface DiagnosisResponse {
  diagnosis_id: string
  trace_id: string
  crop_type: string
  primary_disease: string
  confidence: number
  image_quality_score: number
  observations: Observation[]
  disease_candidates: DiseaseCandidate[]
  evidence_chain: string[]
  planner_analysis?: PlannerAnalysis
  execution_plan?: PlannerStep[]
  follow_up_questions?: string[]
  vision_analysis?: VisionAnalysis
  diagnosis_analysis?: DiagnosisAnalysis
  analysis_source?: string
  treatment_sources?: TreatmentSource[]
  treatment_recommendations?: TreatmentRecommendation[]
  market_data?: MarketData
  economics_analysis?: EconomicsLineItem[]
  report_analysis?: ReportAnalysis
  errors?: string[]
  created_at: string
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  database: 'healthy' | 'unhealthy'
  agents: 'healthy' | 'unhealthy'
}

export interface ApiError {
  detail: string
  trace_id?: string
  code?: string
}
