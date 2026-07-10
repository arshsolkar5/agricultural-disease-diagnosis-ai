from fastapi import APIRouter
from app.agents import (
    VisionAgent,
    PlannerAgent,
    DiagnosisAgent,
    EvidenceAgent,
    RAGAgent,
    TreatmentAgent,
    MarketAgent,
    EconomicsAgent,
    ReportAgent,
)
from app.database.models import AgentMetrics
from app.database.engine import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(prefix="/agents", tags=["agents"])

@router.get("/status")
async def agents_status():
    """Get detailed agent status from database."""
    try:
        db: Session = SessionLocal()
        try:
            all_metrics = db.query(AgentMetrics).all()
            metrics_dict = {m.agent_name: m for m in all_metrics}
            
            # Define all expected agents
            agent_classes = {
                "vision": VisionAgent,
                "planner": PlannerAgent,
                "diagnosis": DiagnosisAgent,
                "evidence": EvidenceAgent,
                "rag": RAGAgent,
                "treatment": TreatmentAgent,
                "market": MarketAgent,
                "economics": EconomicsAgent,
                "report": ReportAgent,
            }
            
            result = {}
            for agent_name, agent_class in agent_classes.items():
                if agent_name in metrics_dict:
                    m = metrics_dict[agent_name]
                    success_rate = (
                        (m.total_executions - m.error_count) / m.total_executions
                        if m.total_executions > 0
                        else 0.0
                    )
                    result[agent_name] = {
                        "agent_name": m.agent_name,
                        "total_executions": m.total_executions,
                        "error_count": m.error_count,
                        "success_rate": success_rate,
                        "average_latency_ms": m.average_latency_ms,
                        "last_execution_time": m.last_execution_time.isoformat() if m.last_execution_time else None,
                        "last_status": m.last_status
                    }
                else:
                    # Initialize with default values if no metrics exist
                    result[agent_name] = {
                        "agent_name": agent_name,
                        "total_executions": 0,
                        "error_count": 0,
                        "success_rate": 0.0,
                        "average_latency_ms": 0.0,
                        "last_execution_time": None,
                        "last_status": None
                    }
            
            return result
        finally:
            db.close()
    except Exception as e:
        # Fallback to instance-based status if database fails
        return {
            "vision": VisionAgent().get_status(),
            "planner": PlannerAgent().get_status(),
            "diagnosis": DiagnosisAgent().get_status(),
            "evidence": EvidenceAgent().get_status(),
            "rag": RAGAgent().get_status(),
            "treatment": TreatmentAgent().get_status(),
            "market": MarketAgent().get_status(),
            "economics": EconomicsAgent().get_status(),
            "report": ReportAgent().get_status(),
        }
