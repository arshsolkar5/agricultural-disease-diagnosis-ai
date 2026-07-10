from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime

class AgentInput(BaseModel):
    """Standard input contract for all agents."""
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

class AgentOutput(BaseModel):
    """Standard output contract for all agents."""
    agent_name: str
    status: str = "success"  # success, fallback, error
    result: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    error: Optional[str] = None
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Observation(BaseModel):
    """Visual observation from Vision Agent."""
    category: str  # lesion, necrosis, spot, etc.
    location: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0)
    description: str
    bounding_box: Optional[Dict[str, float]] = None  # x, y, w, h
    severity: Optional[str] = None
    visible_signs: List[str] = Field(default_factory=list)
    possible_cause: Optional[str] = None
    affected_area_percent: Optional[float] = None

class DiagnosisEvidence(BaseModel):
    """Evidence for a disease diagnosis."""
    disease_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    observed_symptoms: List[str]
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    rank: int

class HealthStatus(BaseModel):
    """System health status."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    checks: Dict[str, str] = Field(default_factory=dict)
