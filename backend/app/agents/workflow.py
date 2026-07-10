from datetime import datetime
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph


class DiagnosisWorkflowState(TypedDict, total=False):
    image_base64: str
    crop_type: str
    farmer_id: str | None
    location: str | None
    additional_context: str | None
    trace_id: str
    observations: List[Dict[str, Any]]
    image_quality_score: float
    follow_up_questions: List[str]
    vision_analysis: Dict[str, Any]
    planner_analysis: Dict[str, Any]
    execution_plan: List[Dict[str, Any]]
    diagnosis_analysis: Dict[str, Any]
    analysis_source: str | None
    disease_candidates: List[Dict[str, Any]]
    verified_diagnosis: str | None
    final_confidence: float
    evidence_chain: List[str]
    treatment_sources: List[Dict[str, Any]]
    treatment_recommendations: List[Dict[str, Any]]
    market_data: Dict[str, Any]
    economics_analysis: List[Dict[str, Any]]
    report_analysis: Dict[str, Any]
    errors: List[str]
    created_at: datetime
    last_updated: datetime


def build_diagnosis_workflow(orchestrator: Any):
    """Compile the LangGraph workflow used by the orchestrator."""

    workflow = StateGraph(DiagnosisWorkflowState)

    async def vision_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            vision_output = await orchestrator.vision_agent.run(
                {
                    "image_base64": state["image_base64"],
                    "crop_type": state["crop_type"],
                }
            )
            detected_crop_type = vision_output.result.get("detected_crop_type")
            updated_crop_type = detected_crop_type if detected_crop_type and state["crop_type"] == "auto_detect" else state["crop_type"]
            return {
                "observations": vision_output.result.get("observations", []),
                "image_quality_score": vision_output.result.get("image_quality_score", 0.0),
                "follow_up_questions": vision_output.result.get("follow_up_questions", []),
                "vision_analysis": vision_output.result,
                "analysis_source": vision_output.result.get("analysis_source"),
                "crop_type": updated_crop_type,
            }
        except Exception as e:
            logger = get_logger("workflow.vision")
            logger.warning("vision_node_failed", error=str(e))
            return {
                "observations": [],
                "image_quality_score": 0.0,
                "follow_up_questions": [],
                "vision_analysis": {},
                "analysis_source": "error",
                "crop_type": state["crop_type"],
            }

    async def planner_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            planner_output = await orchestrator.planner_agent.run(
                {
                    "crop_type": state["crop_type"],
                    "observations": state.get("observations", []),
                    "image_quality_score": state.get("image_quality_score", 0.0),
                    "follow_up_questions": state.get("follow_up_questions", []),
                    "analysis_source": state.get("analysis_source"),
                    "additional_context": state.get("additional_context"),
                }
            )
            return {
                "planner_analysis": planner_output.result,
                "execution_plan": planner_output.result.get("plan", []),
            }
        except Exception as e:
            logger = get_logger("workflow.planner")
            logger.warning("planner_node_failed", error=str(e))
            return {
                "planner_analysis": {},
                "execution_plan": [],
            }

    async def diagnosis_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            diagnosis_output = await orchestrator.diagnosis_agent.run(
                {
                    "observations": state.get("observations", []),
                    "crop_type": state["crop_type"],
                    "additional_context": state.get("additional_context"),
                }
            )
            return {
                "disease_candidates": diagnosis_output.result.get("disease_candidates", []),
                "diagnosis_analysis": diagnosis_output.result,
                "verified_diagnosis": diagnosis_output.result.get("primary_disease"),
                "final_confidence": diagnosis_output.confidence,
            }
        except Exception as e:
            logger = get_logger("workflow.diagnosis")
            logger.warning("diagnosis_node_failed", error=str(e))
            return {
                "disease_candidates": [],
                "diagnosis_analysis": {},
                "verified_diagnosis": None,
                "final_confidence": 0.0,
            }

    async def evidence_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            evidence_output = await orchestrator.evidence_agent.run(
                {
                    "disease_candidates": state.get("disease_candidates", []),
                    "observations": state.get("observations", []),
                }
            )
            return {
                "verified_diagnosis": evidence_output.result.get("verified_diagnosis"),
                "final_confidence": evidence_output.result.get("final_confidence", 0.0),
                "evidence_chain": evidence_output.result.get("evidence_chain", []),
            }
        except Exception as e:
            logger = get_logger("workflow.evidence")
            logger.warning("evidence_node_failed", error=str(e))
            return {
                "verified_diagnosis": state.get("verified_diagnosis"),
                "final_confidence": state.get("final_confidence", 0.0),
                "evidence_chain": [],
            }

    async def rag_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        if not state.get("verified_diagnosis"):
            return {"treatment_sources": state.get("treatment_sources", [])}

        try:
            rag_output = await orchestrator.rag_agent.run(
                {
                    "disease": state["verified_diagnosis"],
                    "crop_type": state.get("crop_type", ""),
                }
            )
            return {
                "treatment_sources": rag_output.result.get("retrieved_documents", []),
            }
        except Exception as e:
            logger = get_logger("workflow.rag")
            logger.warning("rag_node_failed", error=str(e))
            return {"treatment_sources": []}

    async def treatment_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        if not state.get("verified_diagnosis"):
            return {"treatment_recommendations": state.get("treatment_recommendations", [])}

        try:
            treatment_output = await orchestrator.treatment_agent.run(
                {
                    "disease": state["verified_diagnosis"],
                    "rag_results": state.get("treatment_sources", []),
                }
            )
            return {
                "treatment_recommendations": treatment_output.result.get("recommendations", []),
            }
        except Exception as e:
            logger = get_logger("workflow.treatment")
            logger.warning("treatment_node_failed", error=str(e))
            return {"treatment_recommendations": []}

    async def market_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            market_output = await orchestrator.market_agent.run(
                {
                    "crop_type": state["crop_type"],
                    "location": state.get("location"),
                }
            )
            return {
                "market_data": market_output.result,
            }
        except Exception as e:
            logger = get_logger("workflow.market")
            logger.warning("market_node_failed", error=str(e))
            return {
                "market_data": {},
            }

    async def economics_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        if not state.get("treatment_recommendations"):
            return {"economics_analysis": state.get("economics_analysis", [])}

        try:
            market_price = state.get("market_data", {}).get("current_price_per_quintal", 1800)
            if market_price is None:
                market_price = 1800
            
            economics_output = await orchestrator.economics_agent.run(
                {
                    "treatments": state.get("treatment_recommendations", []),
                    "yield_potential": 50,
                    "market_price": market_price,
                }
            )
            return {
                "economics_analysis": economics_output.result.get("analysis", []),
            }
        except Exception as e:
            # Log error but continue workflow with empty economics
            from app.utils.logger import get_logger
            logger = get_logger("workflow.economics")
            logger.warning("economics_node_failed", error=str(e))
            return {"economics_analysis": []}

    async def report_node(state: DiagnosisWorkflowState) -> Dict[str, Any]:
        try:
            report_output = await orchestrator.report_agent.run(
                {
                    "crop_type": state["crop_type"],
                    "location": state.get("location"),
                    "observations": state.get("observations", []),
                    "execution_plan": state.get("execution_plan", []),
                    "planner_analysis": state.get("planner_analysis", {}),
                    "disease_candidates": state.get("disease_candidates", []),
                    "verified_diagnosis": state.get("verified_diagnosis"),
                    "final_confidence": state.get("final_confidence", 0.0),
                    "treatment_recommendations": state.get("treatment_recommendations", []),
                    "market_data": state.get("market_data", {}),
                    "economics_analysis": state.get("economics_analysis", []),
                    "evidence_chain": state.get("evidence_chain", []),
                    "follow_up_questions": state.get("follow_up_questions", []),
                }
            )
            return {
                "report_analysis": report_output.result,
            }
        except Exception as e:
            logger = get_logger("workflow.report")
            logger.warning("report_node_failed", error=str(e))
            return {
                "report_analysis": {},
            }

    workflow.add_node("vision", vision_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("diagnosis", diagnosis_node)
    workflow.add_node("evidence", evidence_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("treatment", treatment_node)
    workflow.add_node("market", market_node)
    workflow.add_node("economics", economics_node)
    workflow.add_node("report", report_node)

    workflow.set_entry_point("vision")
    workflow.add_edge("vision", "planner")
    workflow.add_edge("planner", "diagnosis")
    workflow.add_edge("diagnosis", "evidence")
    workflow.add_edge("evidence", "rag")
    workflow.add_edge("rag", "treatment")
    workflow.add_edge("treatment", "market")
    workflow.add_edge("market", "economics")
    workflow.add_edge("economics", "report")
    workflow.add_edge("report", END)

    return workflow.compile()
