import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.llm import explain_with_openrouter, get_openrouter_client
from app.models.common import AgentOutput
from app.models.llm import DiagnosisAnalysis
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("agent.diagnosis")


class DiagnosisAgent(BaseAgent):
    """
    Diagnosis Agent: Ranks possible diseases based on observations.

    The agent prefers OpenRouter for reasoning and falls back to the existing
    crop-specific heuristic scoring when the API is unavailable.
    """

    DISEASE_PATTERNS = {
        "rice": {
            "leaf_blast": {
                "symptoms": ["lesion", "spot"],
                "color_indicators": ["brown", "gray"],
                "confidence_base": 0.85,
            },
            "sheath_blight": {
                "symptoms": ["spot", "necrosis"],
                "color_indicators": ["brown", "tan"],
                "confidence_base": 0.80,
            },
            "brown_spot": {
                "symptoms": ["spot", "lesion"],
                "color_indicators": ["brown"],
                "confidence_base": 0.78,
            },
            "bacterial_leaf_blight": {
                "symptoms": ["lesion", "necrosis"],
                "color_indicators": ["brown", "black"],
                "confidence_base": 0.82,
            },
        },
        "wheat": {
            "septoria": {
                "symptoms": ["lesion", "spot"],
                "color_indicators": ["brown", "tan"],
                "confidence_base": 0.82,
            },
            "powdery_mildew": {
                "symptoms": ["white_coating"],
                "color_indicators": ["white"],
                "confidence_base": 0.79,
            },
            "rust": {
                "symptoms": ["spot", "lesion"],
                "color_indicators": ["brown", "orange", "red"],
                "confidence_base": 0.85,
            },
            "fusarium": {
                "symptoms": ["necrosis", "lesion"],
                "color_indicators": ["brown", "pink"],
                "confidence_base": 0.78,
            },
        },
        "maize": {
            "northern_leaf_blight": {
                "symptoms": ["lesion", "necrosis"],
                "color_indicators": ["brown", "tan"],
                "confidence_base": 0.82,
            },
            "gray_leaf_spot": {
                "symptoms": ["spot", "lesion"],
                "color_indicators": ["gray", "brown"],
                "confidence_base": 0.80,
            },
            "common_rust": {
                "symptoms": ["spot"],
                "color_indicators": ["brown", "orange"],
                "confidence_base": 0.84,
            },
        },
        "cotton": {
            "leaf_spot": {
                "symptoms": ["spot", "lesion"],
                "color_indicators": ["brown", "black"],
                "confidence_base": 0.80,
            },
            "verticillium_wilt": {
                "symptoms": ["necrosis", "lesion"],
                "color_indicators": ["brown", "yellow"],
                "confidence_base": 0.78,
            },
        },
        "tomato": {
            "early_blight": {
                "symptoms": ["lesion", "spot", "necrotic", "shriveling", "curling", "general"],
                "color_indicators": ["brown", "black", "yellow"],
                "confidence_base": 0.85,
            },
            "late_blight": {
                "symptoms": ["lesion", "necrosis", "necrotic", "growth", "fuzzy", "whitish", "general"],
                "color_indicators": ["brown", "black", "whitish", "grey"],
                "confidence_base": 0.84,
            },
            "leaf_spot": {
                "symptoms": ["spot", "lesion", "discoloration", "general"],
                "color_indicators": ["brown", "yellow", "black"],
                "confidence_base": 0.78,
            },
            "septoria_leaf_spot": {
                "symptoms": ["spot", "lesion", "necrotic", "general"],
                "color_indicators": ["brown", "black", "yellow"],
                "confidence_base": 0.80,
            },
        },
        "potato": {
            "early_blight": {
                "symptoms": ["lesion", "spot"],
                "color_indicators": ["brown", "black"],
                "confidence_base": 0.85,
            },
            "late_blight": {
                "symptoms": ["lesion", "necrosis"],
                "color_indicators": ["brown", "black"],
                "confidence_base": 0.84,
            },
        },
        "sugarcane": {
            "red_rot": {
                "symptoms": ["necrosis", "lesion"],
                "color_indicators": ["red", "brown"],
                "confidence_base": 0.82,
            },
            "leaf_scald": {
                "symptoms": ["lesion", "necrosis"],
                "color_indicators": ["brown", "tan"],
                "confidence_base": 0.78,
            },
        },
    }

    def __init__(self):
        super().__init__(
            name="DiagnosisAgent",
            description="Ranks possible diseases based on visual observations",
        )
        self.client = get_openrouter_client()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        observations = input_data.get("observations", [])
        crop_type = input_data.get("crop_type", "unknown").lower()
        additional_context = input_data.get("additional_context", "")

        # Merge additional_context as a text-based observation
        if additional_context and additional_context.strip():
            context_observation = {
                "category": "user_reported",
                "description": additional_context.strip(),
                "confidence": 0.8,  # High confidence for user-reported symptoms
                "location": None,
                "severity": None,
                "visible_signs": [],
                "possible_cause": None,
                "affected_area_percent": None,
                "bounding_box": None,
                "source": "user_input"
            }
            observations = [context_observation] + observations
            logger.info("additional_context_merged", context_length=len(additional_context))

        if not observations:
            return AgentOutput(
                agent_name=self.name,
                status="fallback",
                result={
                    "disease_candidates": [],
                    "analysis_source": "fallback",
                    "uncertainties": ["No observations provided"],
                },
                confidence=0.0,
                reasoning="No observations provided. Cannot diagnose without visual symptoms.",
                latency_ms=0,
            )

        # Handle auto_detect by attempting to infer crop from observations or use tomato as default
        if crop_type == "auto_detect" or crop_type == "unknown":
            # Try to infer from vision analysis if available
            detected_crop = input_data.get("detected_crop_type", "").lower()
            if detected_crop and detected_crop in self.DISEASE_PATTERNS:
                crop_type = detected_crop
                logger.info("crop_detected_from_vision", crop_type=crop_type)
            else:
                # Default to tomato as it's the most common crop in the knowledge base
                crop_type = "tomato"
                logger.info("crop_fallback_to_default", crop_type=crop_type)

        if not self.client.is_configured:
            return self._heuristic_result(observations, crop_type, "OpenRouter is not configured.")

        try:
            analysis = await explain_with_openrouter(
                system_prompt=self._system_prompt(),
                user_prompt=self._user_prompt(crop_type, observations, additional_context),
                schema_model=DiagnosisAnalysis,
                temperature=0.15,
                max_tokens=1200,
                reasoning_effort="high",
                model=settings.openrouter_model,
            )
            candidates = [candidate.model_dump() for candidate in analysis.disease_candidates]
            if not candidates:
                return self._heuristic_result(
                    observations,
                    crop_type,
                    "OpenRouter returned no candidates, so the heuristic fallback was used.",
                )

            normalized = self._normalize_candidates(candidates)
            normalized.sort(key=lambda item: item["confidence"], reverse=True)
            for index, candidate in enumerate(normalized, start=1):
                candidate["rank"] = index

            confidence = round(max(0.0, min(1.0, analysis.confidence)), 3)
            reasoning = analysis.reasoning or self._generate_reasoning(normalized, observations)

            return AgentOutput(
                agent_name=self.name,
                status="success",
                result={
                    "disease_candidates": normalized,
                    "analysis_source": "openrouter",
                    "primary_disease": analysis.primary_disease or normalized[0]["disease"],
                    "uncertainties": analysis.uncertainties,
                    "next_steps": analysis.next_steps,
                },
                confidence=confidence if confidence > 0 else normalized[0]["confidence"],
                reasoning=reasoning,
                latency_ms=0,
            )
        except Exception as exc:
            logger.warning("diagnosis_openrouter_failed", error=str(exc))
            return self._heuristic_result(
                observations,
                crop_type,
                f"OpenRouter reasoning failed: {exc}",
            )

    def _system_prompt(self) -> str:
        return (
            "You are a crop disease reasoning assistant. Rank the most likely diseases "
            "from the observations and crop type. Return only structured JSON matching "
            "the provided schema. Be concise, explicit about uncertainty, and keep the "
            "reasoning grounded in visible symptoms."
        )

    def _user_prompt(self, crop_type: str, observations: List[Dict[str, Any]], additional_context: str = "") -> str:
        prompt_data = {
            "crop_type": crop_type,
            "observations": observations,
            "instructions": [
                "Rank the top diseases from most likely to least likely.",
                "Use the observation categories, descriptions, and confidence values.",
                "If evidence is weak, lower confidence and explain why.",
                "Give special consideration to user-reported symptoms (category: user_reported).",
            ],
        }
        
        if additional_context:
            prompt_data["additional_context"] = additional_context
            prompt_data["instructions"].append("User-provided context should be weighted heavily in diagnosis.")
        
        return json.dumps(prompt_data, ensure_ascii=False, indent=2)

    def _heuristic_result(
        self,
        observations: List[Dict[str, Any]],
        crop_type: str,
        reasoning_prefix: str,
    ) -> AgentOutput:
        patterns = self.DISEASE_PATTERNS.get(crop_type, {})
        if not patterns:
            return AgentOutput(
                agent_name=self.name,
                status="fallback",
                result={
                    "disease_candidates": [],
                    "analysis_source": "fallback",
                    "uncertainties": [f"No disease patterns available for crop type: {crop_type}"],
                },
                confidence=0.0,
                reasoning=f"No disease patterns available for crop type: {crop_type}",
                latency_ms=0,
            )

        ranked = self._score_diseases(observations, patterns)
        ranked.sort(key=lambda item: item["confidence"], reverse=True)
        for index, candidate in enumerate(ranked, start=1):
            candidate["rank"] = index

        reasoning = self._generate_reasoning(ranked, observations)
        if reasoning_prefix:
            reasoning = f"{reasoning_prefix} {reasoning}".strip()

        return AgentOutput(
            agent_name=self.name,
            status="success" if ranked else "fallback",
            result={
                "disease_candidates": ranked,
                "analysis_source": "heuristic",
                "primary_disease": ranked[0]["disease"] if ranked else None,
                "uncertainties": self._identify_uncertainty(observations, ranked),
                "next_steps": ["Review follow-up observations with the vision agent."],
            },
            confidence=ranked[0]["confidence"] if ranked else 0.0,
            reasoning=reasoning,
            latency_ms=0,
        )

    def _normalize_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        for candidate in candidates:
            normalized.append(
                {
                    "disease": candidate.get("disease", "unknown"),
                    "confidence": round(float(candidate.get("confidence", 0.0)), 3),
                    "rank": int(candidate.get("rank", len(normalized) + 1)),
                    "reasoning": candidate.get("reasoning", ""),
                    "matched_observations": candidate.get("matched_observations", []),
                    "uncertainties": candidate.get("uncertainties", []),
                }
            )
        return normalized

    def _score_diseases(
        self,
        observations: List[Dict[str, Any]],
        patterns: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        scores = []
        for disease_name, pattern in patterns.items():
            base_confidence = pattern.get("confidence_base", 0.5)
            symptom_keywords = set(k.lower() for k in pattern.get("symptoms", []))
            color_keywords = set(k.lower() for k in pattern.get("color_indicators", []))
            
            matched_observations = []
            for obs in observations:
                category = obs.get("category", "").lower()
                description = obs.get("description", "").lower()
                
                # Special handling for user_reported observations
                if category == "user_reported":
                    # Extract keywords from user description and match against disease patterns
                    for keyword in symptom_keywords:
                        if keyword in description:
                            matched_observations.append(obs)
                            break
                    for color in color_keywords:
                        if color in description:
                            matched_observations.append(obs)
                            break
                    # User-reported symptoms get a confidence boost
                    if obs in matched_observations:
                        base_confidence = min(1.0, base_confidence + 0.1)
                    continue
                
                # Check if category matches directly
                if category in symptom_keywords:
                    matched_observations.append(obs)
                    continue
                
                # Check if description contains symptom keywords
                for keyword in symptom_keywords:
                    if keyword in description:
                        matched_observations.append(obs)
                        break
                
                # Check if description contains color indicators
                for color in color_keywords:
                    if color in description:
                        matched_observations.append(obs)
                        break

            if not matched_observations:
                logger.debug("no_match", disease=disease_name, symptoms=list(symptom_keywords), colors=list(color_keywords))
                continue

            match_boost = min(0.15, len(matched_observations) * 0.05)
            obs_confidence = sum(o.get("confidence", 0.5) for o in observations) / len(observations)
            confidence_adjustment = (obs_confidence - 0.5) * 0.1
            final_confidence = min(1.0, base_confidence + match_boost + confidence_adjustment)

            matching_descriptions = [obs.get("description", "") for obs in matched_observations]

            scores.append(
                {
                    "disease": disease_name,
                    "confidence": round(final_confidence, 3),
                    "symptom_matches": len(matched_observations),
                    "reasoning": f"Matched {len(matched_observations)} symptoms",
                    "matched_observations": matching_descriptions,
                    "uncertainties": [],
                }
            )

        logger.debug("disease_scoring", total_scores=len(scores))
        return scores

    def _generate_reasoning(self, ranked: List[Dict[str, Any]], observations: List[Dict[str, Any]]) -> str:
        if not ranked:
            return "No diseases matched the observed symptoms."

        top_disease = ranked[0]
        obs_summary = ", ".join(sorted({o.get("category", "unknown") for o in observations}))
        return (
            f"Based on observations ({obs_summary}), "
            f"{top_disease['disease']} ranked highest "
            f"with {top_disease['confidence']:.1%} confidence. "
            f"Evidence Agent will verify."
        )

    def _identify_uncertainty(
        self,
        observations: List[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
    ) -> List[str]:
        uncertainty: List[str] = []
        if not observations:
            uncertainty.append("No visual observations available")
        if len(candidates) > 1 and abs(candidates[0]["confidence"] - candidates[1]["confidence"]) < 0.1:
            uncertainty.append("Multiple diseases with similar confidence")
        low_confidence_obs = [o for o in observations if o.get("confidence", 0.5) < 0.7]
        if low_confidence_obs:
            uncertainty.append(f"{len(low_confidence_obs)} observations with low confidence")
        return uncertainty
