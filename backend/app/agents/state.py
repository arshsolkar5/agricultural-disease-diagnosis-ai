from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DiagnosisState(BaseModel):
    """Shared state across all agents."""
    image_base64: str
    crop_type: str
    farmer_id: Optional[str] = None
    location: Optional[str] = None
    additional_context: Optional[str] = None
    trace_id: str
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    image_quality_score: float = 0.0
    follow_up_questions: List[str] = Field(default_factory=list)
    vision_analysis: Dict[str, Any] = Field(default_factory=dict)
    planner_analysis: Dict[str, Any] = Field(default_factory=dict)
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    diagnosis_analysis: Dict[str, Any] = Field(default_factory=dict)
    disease_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    verified_diagnosis: Optional[str] = None
    final_confidence: float = 0.0
    evidence_chain: List[str] = Field(default_factory=list)
    treatment_sources: List[Dict[str, Any]] = Field(default_factory=list)
    treatment_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    market_data: Dict[str, Any] = Field(default_factory=dict)
    economics_analysis: List[Dict[str, Any]] = Field(default_factory=list)
    report_analysis: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    analysis_source: Optional[str] = None
    created_at: datetime
    last_updated: datetime
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiagnosisState":
        return cls(**data)
