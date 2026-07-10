import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.config import settings
from app.llm import explain_with_openrouter, get_openrouter_client
from app.models.common import AgentOutput
from app.utils.logger import get_logger

logger = get_logger("agent.planner")


class PlannerAgent(BaseAgent):
    """Planner Agent: coordinates the diagnosis workflow."""

    def __init__(self):
        super().__init__(
            name="PlannerAgent",
            description="Orchestrates diagnosis workflow",
        )
        self.client = get_openrouter_client()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        crop_type = input_data.get("crop_type", "")
        observations = input_data.get("observations", [])
        image_quality_score = float(input_data.get("image_quality_score", 0.0) or 0.0)

        if not crop_type:
            return AgentOutput(
                agent_name=self.name,
                status="error",
                result={"plan": []},
                confidence=0.0,
                reasoning="Missing required input: crop_type",
                latency_ms=0,
            )

        if self.client.is_configured:
            try:
                plan = await explain_with_openrouter(
                    system_prompt=self._system_prompt(),
                    user_prompt=self._user_prompt(crop_type, observations, image_quality_score),
                    schema_model=self._plan_schema(),
                    temperature=0.1,
                    max_tokens=800,
                    reasoning_effort="low",
                    model=settings.openrouter_model,
                )
                return AgentOutput(
                    agent_name=self.name,
                    status="success",
                    result={
                        "plan": plan.model_dump().get("plan", []),
                        "analysis_source": "openrouter",
                        "crop_type": crop_type,
                    },
                    confidence=1.0,
                    reasoning="Workflow planned by OpenRouter.",
                    latency_ms=0,
                )
            except Exception as exc:
                logger.warning("planner_openrouter_failed", error=str(exc))

        plan = self._fallback_plan(crop_type, observations, image_quality_score)
        return AgentOutput(
            agent_name=self.name,
            status="success",
            result={
                "plan": plan,
                "analysis_source": "fallback",
                "crop_type": crop_type,
            },
            confidence=1.0,
            reasoning="Fallback workflow plan generated locally.",
            latency_ms=0,
        )

    def _system_prompt(self) -> str:
        return (
            "You are a workflow planner for a crop diagnosis system. Output a concise execution plan as structured JSON only."
        )

    def _user_prompt(self, crop_type: str, observations: List[Dict[str, Any]], image_quality_score: float) -> str:
        return json.dumps(
            {
                "crop_type": crop_type,
                "observations": observations,
                "image_quality_score": image_quality_score,
                "steps": [
                    "Review the structured Gemini observations",
                    "Diagnose with Qwen using observations only",
                    "Verify evidence",
                    "Retrieve knowledge base context",
                    "Generate treatment recommendations",
                    "Assess market guidance",
                    "Calculate economics",
                    "Generate final report",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    def _plan_schema(self):
        from pydantic import BaseModel, Field

        class PlanSchema(BaseModel):
            plan: List[Dict[str, Any]] = Field(default_factory=list)

        return PlanSchema

    def _fallback_plan(
        self,
        crop_type: str,
        observations: List[Dict[str, Any]],
        image_quality_score: float,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "step": 1,
                "agent": "VisionAgent",
                "action": "Structured Gemini observations already available",
                "inputs": ["observations", "crop_type"],
                "outputs": ["observations", "image_quality_score"],
            },
            {
                "step": 2,
                "agent": "PlannerAgent",
                "action": "Prepare workflow plan from structured observations",
                "inputs": ["observations", "crop_type", "image_quality_score"],
                "outputs": ["plan"],
            },
            {
                "step": 3,
                "agent": "DiagnosisAgent",
                "action": "Rank possible diseases from observations",
                "inputs": ["observations", "crop_type"],
                "outputs": ["disease_candidates", "primary_disease"],
            },
            {
                "step": 4,
                "agent": "EvidenceAgent",
                "action": "Verify diagnosis with evidence",
                "inputs": ["disease_candidates", "observations"],
                "outputs": ["verified_diagnosis", "final_confidence"],
            },
            {
                "step": 5,
                "agent": "RAGAgent",
                "action": "Retrieve local knowledge base context",
                "inputs": ["verified_diagnosis"],
                "outputs": ["retrieved_documents"],
            },
            {
                "step": 6,
                "agent": "TreatmentAgent",
                "action": "Detail treatment options",
                "inputs": ["verified_diagnosis", "retrieved_documents"],
                "outputs": ["recommendations"],
            },
            {
                "step": 7,
                "agent": "MarketAgent",
                "action": "Provide market context",
                "inputs": ["crop_type", "location"],
                "outputs": ["market_data"],
            },
            {
                "step": 8,
                "agent": "EconomicsAgent",
                "action": "Calculate cost-benefit",
                "inputs": ["treatments", "market_price"],
                "outputs": ["analysis"],
            },
            {
                "step": 9,
                "agent": "ReportAgent",
                "action": "Generate final report",
                "inputs": ["observations", "verified_diagnosis", "treatment_recommendations"],
                "outputs": ["report"],
            },
        ]
