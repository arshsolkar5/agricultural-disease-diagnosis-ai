import uuid
from datetime import datetime
from typing import Dict, Any
from app.agents.state import DiagnosisState
from app.agents.workflow import build_diagnosis_workflow
from app.agents.vision import VisionAgent
from app.agents.planner import PlannerAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.evidence import EvidenceAgent
from app.agents.rag_agent import RAGAgent
from app.agents.treatment_agent import TreatmentAgent
from app.agents.economics_agent import EconomicsAgent
from app.agents.market_agent import MarketAgent
from app.agents.report_agent import ReportAgent
from app.utils.logger import get_logger

logger = get_logger("orchestrator")

class DiagnosisOrchestrator:
    """Orchestrates full diagnosis workflow."""
    
    def __init__(self, db=None):
        self.db = db
        self.vision_agent = VisionAgent(db)
        self.planner_agent = PlannerAgent()
        self.diagnosis_agent = DiagnosisAgent()
        self.evidence_agent = EvidenceAgent()
        self.rag_agent = RAGAgent(db)
        self.treatment_agent = TreatmentAgent()
        self.economics_agent = EconomicsAgent()
        self.market_agent = MarketAgent()
        self.report_agent = ReportAgent()
        self.workflow = build_diagnosis_workflow(self)
    
    async def diagnose(self, request: Dict[str, Any]) -> DiagnosisState:
        """Run full diagnosis workflow."""
        trace_id = str(uuid.uuid4())
        initial_state = DiagnosisState(
            image_base64=request.get("image_base64", ""),
            crop_type=request.get("crop_type", ""),
            farmer_id=request.get("farmer_id"),
            location=request.get("location"),
            additional_context=request.get("additional_context"),
            trace_id=trace_id,
            created_at=datetime.utcnow(),
            last_updated=datetime.utcnow(),
        )
        state = initial_state
        
        logger.info("diagnosis_started", trace_id=trace_id)
        
        try:
            state_dict = await self.workflow.ainvoke(initial_state.model_dump())
            state = DiagnosisState.model_validate(state_dict)
            
            logger.info("diagnosis_complete", diagnosis=state.verified_diagnosis)
            state.last_updated = datetime.utcnow()
            return state
        
        except Exception as e:
            logger.error("orchestration_error", error=str(e))
            # Preserve the partial state from the workflow execution
            # The error is already added to state by the failing agent
            state.last_updated = datetime.utcnow()
            return state
