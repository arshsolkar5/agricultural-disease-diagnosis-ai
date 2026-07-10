import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.config import settings
from app.llm import explain_with_openrouter, get_openrouter_client
from app.models.common import AgentOutput
from app.models.llm import TreatmentAnalysis
from app.utils.logger import get_logger

logger = get_logger("agent.treatment")


class TreatmentAgent(BaseAgent):
    """Treatment Agent: produces ranked treatment recommendations."""

    TREATMENT_TEMPLATES = {
        "early_blight": {
            "options": [
                {
                    "name": "Chemical Control - Chlorothalonil",
                    "description": "Fungicide spray 2-3g/L every 7-10 days",
                    "cost_per_acre": 600,
                    "yield_recovery_percent": 55,
                    "days_to_recovery": 10,
                    "confidence": 0.90,
                },
                {
                    "name": "Chemical Control - Copper-based",
                    "description": "Copper fungicide 2-3g/L preventive sprays",
                    "cost_per_acre": 500,
                    "yield_recovery_percent": 50,
                    "days_to_recovery": 12,
                    "confidence": 0.85,
                },
                {
                    "name": "Cultural Control - Remove Infected Leaves",
                    "description": "Remove infected leaves and plant debris, improve air circulation",
                    "cost_per_acre": 200,
                    "yield_recovery_percent": 40,
                    "days_to_recovery": 14,
                    "confidence": 0.75,
                },
                {
                    "name": "Systemic Fungicide - Azoxystrobin",
                    "description": "Systemic fungicide 1-1.5mL/L for curative action",
                    "cost_per_acre": 800,
                    "yield_recovery_percent": 60,
                    "days_to_recovery": 7,
                    "confidence": 0.88,
                },
            ]
        },        "leaf_blast": {
            "options": [
                {
                    "name": "Chemical Control - Carbendazim",
                    "description": "Fungicide spray 1g/L every 10 days",
                    "cost_per_acre": 750,
                    "yield_recovery_percent": 70,
                    "days_to_recovery": 10,
                    "confidence": 0.92,
                },
                {
                    "name": "Preventive - Resistant Varieties",
                    "description": "Use disease-resistant cultivars",
                    "cost_per_acre": 200,
                    "yield_recovery_percent": 85,
                    "days_to_recovery": 0,
                    "confidence": 0.88,
                },
            ]
        },
        "sheath_blight": {
            "options": [
                {
                    "name": "Water Management",
                    "description": "Improve drainage, reduce humidity",
                    "cost_per_acre": 500,
                    "yield_recovery_percent": 60,
                    "days_to_recovery": 14,
                    "confidence": 0.85,
                },
                {
                    "name": "Chemical - Hexaconazole",
                    "description": "Fungicide spray 1.5 mL/L",
                    "cost_per_acre": 900,
                    "yield_recovery_percent": 75,
                    "days_to_recovery": 12,
                    "confidence": 0.90,
                },
            ]
        },
    }

    def __init__(self):
        super().__init__(
            name="TreatmentAgent",
            description="Generates treatment recommendations",
        )
        self.client = get_openrouter_client()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        disease = input_data.get("disease", "unknown")
        crop_type = input_data.get("crop_type", "unknown")
        rag_results = input_data.get("rag_results", [])

        if self.client.is_configured:
            try:
                analysis = await explain_with_openrouter(
                    system_prompt=self._system_prompt(),
                    user_prompt=self._user_prompt(crop_type, disease, rag_results),
                    schema_model=TreatmentAnalysis,
                    temperature=0.15,
                    max_tokens=1400,
                    reasoning_effort="high",
                    model=settings.openrouter_model,
                )
                recommendations = [option.model_dump() for option in analysis.recommendations]
                # Ensure numeric fields have valid values
                for rec in recommendations:
                    if rec.get("yield_recovery_percent") is None:
                        rec["yield_recovery_percent"] = 50.0  # Default to 50% recovery
                    if rec.get("cost_per_acre") is None:
                        rec["cost_per_acre"] = 500.0  # Default cost
                    if rec.get("days_to_recovery") is None:
                        rec["days_to_recovery"] = 10  # Default days

                return AgentOutput(
                    agent_name=self.name,
                    status="success",
                    result={
                        "disease": analysis.disease or disease,
                        "crop_type": analysis.crop_type or crop_type,
                        "recommendations": recommendations,
                        "best_option": analysis.best_option.model_dump() if analysis.best_option else None,
                        "summary": analysis.summary,
                        "uncertainties": analysis.uncertainties,
                        "analysis_source": "openrouter",
                    },
                    confidence=self._best_confidence(analysis.recommendations),
                    reasoning=analysis.summary or "Treatment plan generated by OpenRouter.",
                    latency_ms=0,
                )
            except Exception as exc:
                logger.warning("treatment_openrouter_failed", error=str(exc))

        ranked = self._fallback_ranked_treatments(disease)
        if not ranked:
            return AgentOutput(
                agent_name=self.name,
                status="fallback",
                result={"recommendations": [], "best_option": None, "analysis_source": "fallback"},
                confidence=0.3,
                reasoning=f"Limited treatment data for {disease}. Recommend consulting an agronomist.",
                latency_ms=0,
            )

        return AgentOutput(
            agent_name=self.name,
            status="success",
            result={
                "disease": disease,
                "crop_type": crop_type,
                "recommendations": ranked,
                "best_option": ranked[0],
                "summary": "Fallback treatment recommendations generated from local templates.",
                "uncertainties": ["OpenRouter unavailable; fallback template used."],
                "analysis_source": "fallback",
            },
            confidence=ranked[0].get("confidence", 0.5),
            reasoning=f"Generated {len(ranked)} fallback treatment options ranked by yield recovery.",
            latency_ms=0,
        )

    def _system_prompt(self) -> str:
        return (
            "You are an agronomy treatment planner. Use the diagnosis and RAG excerpts to "
            "recommend practical, safe, and cost-aware treatments. Return structured JSON only."
        )

    def _user_prompt(self, crop_type: str, disease: str, rag_results: List[Dict[str, Any]]) -> str:
        return json.dumps(
            {
                "crop_type": crop_type,
                "disease": disease,
                "rag_results": rag_results,
                "instructions": [
                    "Rank treatment options from most effective to least effective.",
                    "Include costs, expected recovery, time to recovery, precautions, and confidence.",
                    "Do not invent chemical claims that are not supported by the provided context.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    def _fallback_ranked_treatments(self, disease: str) -> List[Dict[str, Any]]:
        templates = self.TREATMENT_TEMPLATES.get(disease, {}).get("options", [])
        if not templates:
            return []

        ranked = sorted(templates, key=lambda x: x["yield_recovery_percent"], reverse=True)
        return ranked

    def _best_confidence(self, recommendations: List[Any]) -> float:
        if not recommendations:
            return 0.0
        top = recommendations[0]
        confidence = getattr(top, "confidence", None)
        try:
            return float(confidence)
        except (TypeError, ValueError):
            return 0.0
