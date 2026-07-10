from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgentExecutionLog(BaseModel):
    """Execution trace for an agent."""
    agent_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str  # pending, running, success, fallback, error
    input_summary: str
    output_summary: str
    confidence: float
    latency_ms: float
    error_message: Optional[str] = None
    retry_count: int = 0

class AgentStatusResponse(BaseModel):
    """Current status of an agent."""
    agent_name: str
    status: str  # idle, processing, success, error
    last_execution: Optional[datetime] = None
    success_rate: float
    average_latency_ms: float
    total_executions: int
