from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StructuredObservation(BaseModel):
    """Structured visual observation returned by the vision model."""

    category: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    location: Optional[str] = None
    severity: Optional[str] = None
    visible_signs: List[str] = Field(default_factory=list)
    possible_cause: Optional[str] = None
    affected_area_percent: Optional[float] = None
    bounding_box: Optional[Dict[str, float]] = None


class VisionAnalysis(BaseModel):
    """Structured response contract for the vision agent."""

    crop_type: Optional[str] = None
    image_quality_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    observations: List[StructuredObservation] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    needs_follow_up: bool = False
    summary: str = ""
    quality_notes: List[str] = Field(default_factory=list)


class DiagnosisCandidate(BaseModel):
    """Candidate disease returned by the reasoning agent."""

    disease: str
    confidence: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    reasoning: str = ""
    matched_observations: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


class DiagnosisAnalysis(BaseModel):
    """Structured response contract for the reasoning agent."""

    crop_type: Optional[str] = None
    primary_disease: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    disease_candidates: List[DiagnosisCandidate] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    reasoning: str = ""
    next_steps: List[str] = Field(default_factory=list)


class EvidenceAnalysis(BaseModel):
    """Structured response contract for evidence verification."""

    verified_diagnosis: Optional[str] = None
    final_confidence: float = Field(ge=0.0, le=1.0)
    evidence_chain: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    uncertainty_sources: List[str] = Field(default_factory=list)
    alternative_diseases: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: str = ""


class TreatmentOption(BaseModel):
    """Structured treatment recommendation option."""

    name: str
    description: str
    cost_per_acre: Optional[float] = None
    yield_recovery_percent: Optional[float] = None
    days_to_recovery: Optional[int] = None
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    precautions: List[str] = Field(default_factory=list)


class TreatmentAnalysis(BaseModel):
    """Structured response contract for treatment planning."""

    disease: Optional[str] = None
    crop_type: Optional[str] = None
    recommendations: List[TreatmentOption] = Field(default_factory=list)
    best_option: Optional[TreatmentOption] = None
    summary: str = ""
    uncertainties: List[str] = Field(default_factory=list)


class MarketAnalysis(BaseModel):
    """Structured response contract for market intelligence."""

    crop_type: Optional[str] = None
    location: Optional[str] = None
    current_price_per_quintal: Optional[float] = None
    market_trend: str = "stable"
    price_volatility: str = "medium"
    recommendation: str = ""
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainties: List[str] = Field(default_factory=list)


class EconomicsLineItem(BaseModel):
    """Structured economic impact line item."""

    treatment: str
    cost_per_acre: float
    expected_yield_gain_quintals: float
    revenue_gain_rupees: float
    net_profit_rupees: float
    roi_percent: float
    break_even_days: float
    confidence: float = Field(ge=0.0, le=1.0)


class EconomicsAnalysis(BaseModel):
    """Structured response contract for treatment economics."""

    analysis: List[EconomicsLineItem] = Field(default_factory=list)
    summary: str = ""
    assumptions: List[str] = Field(default_factory=list)


class ReportAnalysis(BaseModel):
    """Structured final report contract."""

    title: str
    executive_summary: str
    key_findings: List[str] = Field(default_factory=list)
    diagnosis_summary: str = ""
    treatment_summary: str = ""
    market_summary: str = ""
    economics_summary: str = ""
    recommended_actions: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
