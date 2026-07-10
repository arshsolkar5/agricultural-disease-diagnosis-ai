from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.models.common import AgentOutput
from app.services.openrouter_vision_service import OpenRouterVisionService
from app.utils.logger import get_logger

logger = get_logger("agent.vision")


class VisionAgent(BaseAgent):
    """Vision Agent: converts uploaded crop images into structured observations."""

    def __init__(self, db: Optional[Session] = None):
        super().__init__(
            name="VisionAgent",
            description="Detects visual symptoms from crop images using OpenRouter",
        )
        self.db = db
        self.service = OpenRouterVisionService()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        image_b64 = input_data.get("image_base64", "")
        crop_type = input_data.get("crop_type", "unknown")

        try:
            payload = await self.service.analyze(
                image_base64=image_b64,
                crop_type=crop_type,
                db=self.db,
            )
            observations = self._normalize_observations(payload.get("observations", []))
            confidence = self._clamp(payload.get("confidence", 0.0))
            image_quality_score = self._clamp(payload.get("image_quality_score", 0.0))
            reasoning = payload.get("summary") or "Structured visual observations produced by Gemini."

            detected_crop_type = payload.get("crop_type") or crop_type
            return AgentOutput(
                agent_name=self.name,
                status="fallback" if payload.get("source") != "gemini" else "success",
                result={
                    "observations": observations,
                    "image_quality_score": image_quality_score,
                    "confidence": confidence,
                    "uncertainties": payload.get("uncertainties", []),
                    "follow_up_questions": payload.get("follow_up_questions", []),
                    "needs_follow_up": payload.get("needs_follow_up", False),
                    "quality_notes": payload.get("quality_notes", []),
                    "summary": reasoning,
                    "crop_type": crop_type,
                    "detected_crop_type": detected_crop_type,
                    "detected_regions": len(observations),
                    "analysis_source": payload.get("source", "gemini"),
                    "gemini_model": payload.get("gemini_model"),
                    "image_hash": payload.get("image_hash"),
                    "cache_hit": payload.get("cache_hit", False),
                },
                confidence=confidence,
                reasoning=reasoning,
                latency_ms=0,
            )
        except Exception as exc:
            logger.warning("vision_agent_failed", error=str(exc))
            return AgentOutput(
                agent_name=self.name,
                status="error",
                result={
                    "observations": [],
                    "image_quality_score": 0.0,
                    "confidence": 0.0,
                    "uncertainties": [str(exc)],
                    "follow_up_questions": [
                        "Please upload a clear, well-lit image of the affected crop area.",
                    ],
                    "needs_follow_up": True,
                    "quality_notes": ["Vision analysis failed before a structured response could be produced."],
                    "summary": str(exc),
                    "crop_type": crop_type,
                    "detected_regions": 0,
                    "analysis_source": "error",
                    "cache_hit": False,
                },
                confidence=0.0,
                reasoning=str(exc),
                latency_ms=0,
            )

    def _normalize_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for obs in observations:
            if hasattr(obs, "model_dump"):
                normalized.append(obs.model_dump())
            elif isinstance(obs, dict):
                normalized.append(obs)
        return normalized

    def _clamp(self, value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(1.0, round(numeric, 3)))
