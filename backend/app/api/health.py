from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.engine import get_db
from app.agents import (
    VisionAgent,
    DiagnosisAgent,
    EvidenceAgent,
    PlannerAgent,
    RAGAgent,
    TreatmentAgent,
    MarketAgent,
    EconomicsAgent,
    ReportAgent,
)
from app.utils.logger import get_logger

logger = get_logger("health")
router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """System health check."""
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        db_status = "unhealthy"
    
    # Check agents can instantiate
    try:
        VisionAgent()
        PlannerAgent()
        DiagnosisAgent()
        EvidenceAgent()
        RAGAgent()
        TreatmentAgent()
        MarketAgent()
        EconomicsAgent()
        ReportAgent()
        agents_status = "healthy"
    except Exception as e:
        logger.error("agents_health_check_failed", error=str(e))
        agents_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and agents_status == "healthy" else "degraded",
        "database": db_status,
        "agents": agents_status,
        "version": "0.1.0",
    }

@router.get("/agents")
async def agents_status():
    """Get status of all agents."""
    agents = {
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
    return agents
