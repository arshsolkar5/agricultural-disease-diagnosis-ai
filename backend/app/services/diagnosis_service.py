import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.agents.orchestrator import DiagnosisOrchestrator
from app.agents.state import DiagnosisState
from app.database.models import (
    Diagnosis,
    DiagnosisObservation,
    Farmer,
)
from app.utils.logger import get_logger

logger = get_logger("diagnosis_service")

class DiagnosisService:
    """Business logic for diagnoses."""
    
    def __init__(self):
        self.orchestrator = DiagnosisOrchestrator()
    
    async def diagnose(
        self,
        image_b64: str,
        crop_type: str,
        farmer_id: Optional[str] = None,
        location: Optional[str] = None,
        additional_context: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> dict:
        """Run diagnosis and persist to database."""
        state = await self.orchestrator.diagnose({
            "image_base64": image_b64,
            "crop_type": crop_type,
            "farmer_id": farmer_id,
            "location": location,
            "additional_context": additional_context,
        })
        
        diagnosis_id = uuid.uuid4()
        if db:
            try:
                self._persist_diagnosis(db, diagnosis_id, state)
                logger.info("diagnosis_persisted", diagnosis_id=str(diagnosis_id))
            except Exception as e:
                logger.error("persistence_failed", error=str(e))
        
        return {
            "diagnosis_id": str(diagnosis_id),
            "trace_id": state.trace_id,
            "crop_type": state.crop_type,
            "primary_disease": state.verified_diagnosis,
            "confidence": state.final_confidence,
            "image_quality_score": state.image_quality_score,
            "observations": state.observations,
            "planner_analysis": state.planner_analysis,
            "execution_plan": state.execution_plan,
            "disease_candidates": state.disease_candidates,
            "evidence_chain": state.evidence_chain,
            "follow_up_questions": state.follow_up_questions,
            "vision_analysis": state.vision_analysis,
            "diagnosis_analysis": state.diagnosis_analysis,
            "analysis_source": state.analysis_source,
            "treatment_sources": state.treatment_sources,
            "treatment_recommendations": state.treatment_recommendations,
            "market_data": state.market_data,
            "economics_analysis": state.economics_analysis,
            "report_analysis": state.report_analysis,
            "errors": state.errors,
            "created_at": state.created_at.isoformat(),
        }
    
    def _persist_diagnosis(self, db: Session, diagnosis_id: uuid.UUID, state: DiagnosisState):
        """Save diagnosis to database."""
        farmer = None
        if state.farmer_id:
            farmer = db.query(Farmer).filter_by(id=state.farmer_id).first()
        
        diagnosis = Diagnosis(
            id=diagnosis_id,
            farmer_id=farmer.id if farmer else None,
            crop_type=state.crop_type,
            primary_disease=state.verified_diagnosis,
            confidence=state.final_confidence,
            status="completed",
            image_metadata={
                "quality_score": state.image_quality_score,
                "analysis_source": state.analysis_source,
                "follow_up_questions": state.follow_up_questions,
            },
        )
        db.add(diagnosis)
        
        for obs in state.observations:
            observation = DiagnosisObservation(
                id=uuid.uuid4(),
                diagnosis_id=diagnosis_id,
                category=obs.get("category", "unknown"),
                description=obs.get("description", ""),
                confidence=obs.get("confidence", 0.0),
            )
            db.add(observation)
        
        db.commit()
    
    def get_diagnosis(self, diagnosis_id: str, db: Session) -> Optional[dict]:
        """Retrieve diagnosis by ID."""
        try:
            # Convert string to UUID
            diag_uuid = uuid.UUID(diagnosis_id)
            diagnosis = db.query(Diagnosis).filter_by(id=diag_uuid).first()
            
            if not diagnosis:
                return None
            
            return {
                "diagnosis_id": str(diagnosis.id),
                "crop_type": diagnosis.crop_type,
                "primary_disease": diagnosis.primary_disease,
                "confidence": diagnosis.confidence,
                "status": diagnosis.status,
                "created_at": diagnosis.created_at.isoformat(),
                "image_metadata": diagnosis.image_metadata,
                "observations": [
                    {
                        "category": o.category,
                        "confidence": o.confidence,
                        "description": o.description,
                    }
                    for o in diagnosis.observations
                ],
            }
        except ValueError:
            return None
    
    def get_farmer_diagnoses(self, farmer_id: str, db: Session, limit: int = 10) -> list:
        """Get farmer diagnoses."""
        try:
            farmer_uuid = uuid.UUID(farmer_id)
            diagnoses = (
                db.query(Diagnosis)
                .filter_by(farmer_id=farmer_uuid)
                .order_by(Diagnosis.created_at.desc())
                .limit(limit)
                .all()
            )
            
            return [
                {
                    "diagnosis_id": str(d.id),
                    "crop_type": d.crop_type,
                    "primary_disease": d.primary_disease,
                    "confidence": d.confidence,
                    "created_at": d.created_at.isoformat(),
                }
                for d in diagnoses
            ]
        except ValueError:
            return []
