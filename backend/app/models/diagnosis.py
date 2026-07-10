from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DiagnosisRequest(BaseModel):
    """Request to diagnose a crop image."""
    image_base64: str
    crop_type: str  # rice, wheat, corn, etc.
    farmer_id: Optional[str] = None
    location: Optional[str] = None
    additional_context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DiagnosisResponse(BaseModel):
    """Complete diagnosis result."""
    diagnosis_id: str
    timestamp: datetime
    crop_type: str
    primary_disease: str
    confidence: float = Field(ge=0.0, le=1.0)
    alternative_diseases: List[Dict[str, Any]]
    observed_symptoms: List[str]
    treatment_recommendations: List[str]
    estimated_yield_loss: Optional[float] = None
    recommended_market_action: Optional[str] = None
    explainability: Dict[str, Any]
    image_quality_score: Optional[float] = None
    follow_up_questions: List[str] = Field(default_factory=list)
    vision_analysis: Dict[str, Any] = Field(default_factory=dict)
    planner_analysis: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    diagnosis_analysis: Dict[str, Any] = Field(default_factory=dict)
    analysis_source: Optional[str] = None
    evidence_chain: List[str] = Field(default_factory=list)
    treatment_sources: List[Dict[str, Any]] = Field(default_factory=list)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    economics_analysis: List[Dict[str, Any]] = Field(default_factory=list)
