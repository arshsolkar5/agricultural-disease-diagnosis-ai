from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.models.common import AgentOutput
from app.models.llm import EvidenceAnalysis
from app.llm import explain_with_openrouter, get_openrouter_client
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("agent.evidence")

class EvidenceAgent(BaseAgent):
    """
    Evidence Agent: Verifies diagnosis and builds evidence chain.
    
    Input: disease_candidates from Diagnosis Agent
    Output: Verified primary diagnosis with evidence breakdown
    
    Responsibilities:
    1. Check for contradicting evidence
    2. Verify confidence is justified
    3. Identify uncertainty sources
    4. Build evidence chain for explainability
    """
    
    # Contradicting patterns: disease → symptoms that rule it out
    CONTRADICTION_CHECKS = {
        "leaf_blast": {
            "rules_out": [],  # No weather-dependent contradictions for MVP
        },
        "sheath_blight": {
            "rules_out": [],
        },
    }
    
    def __init__(self):
        super().__init__(
            name="EvidenceAgent",
            description="Verifies diagnosis and builds evidence chain"
        )
        self.client = get_openrouter_client()
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        Verify diagnosis with evidence.
        
        Input:
        {
            "disease_candidates": [
                {"disease": "leaf_blast", "confidence": 0.87, "rank": 1},
                ...
            ],
            "observations": [{"category": "lesion", "confidence": 0.92}]
        }
        
        Output:
        {
            "verified_diagnosis": "leaf_blast",
            "final_confidence": 0.85,
            "evidence_chain": ["Lesion observed", "Color match: brown", ...],
            "uncertainty_sources": ["Low observation confidence"],
            "supporting_evidence": [...],
            "contradicting_evidence": [...]
        }
        """
        try:
            disease_candidates = input_data.get("disease_candidates", [])
            observations = input_data.get("observations", [])
            
            if not disease_candidates:
                return AgentOutput(
                    agent_name=self.name,
                    status="fallback",
                    result={
                        "verified_diagnosis": None,
                        "final_confidence": 0.0,
                        "evidence_chain": [],
                    },
                    confidence=0.0,
                    reasoning="No disease candidates to verify.",
                    latency_ms=0,
                )
            
            if self.client.is_configured:
                try:
                    analysis = await explain_with_openrouter(
                        system_prompt=self._system_prompt(),
                        user_prompt=self._user_prompt(disease_candidates, observations),
                        schema_model=EvidenceAnalysis,
                        temperature=0.1,
                        max_tokens=1000,
                        reasoning_effort="medium",
                        model=settings.openrouter_model,
                    )
                    return AgentOutput(
                        agent_name=self.name,
                        status="success",
                        result={
                            "verified_diagnosis": analysis.verified_diagnosis or disease_candidates[0].get("disease"),
                            "final_confidence": analysis.final_confidence,
                            "evidence_chain": analysis.evidence_chain,
                            "supporting_evidence": analysis.supporting_evidence,
                            "contradicting_evidence": analysis.contradicting_evidence,
                            "uncertainty_sources": analysis.uncertainty_sources,
                            "alternative_diseases": analysis.alternative_diseases,
                            "analysis_source": "openrouter",
                        },
                        confidence=analysis.final_confidence,
                        reasoning=analysis.reasoning or "Evidence verified by OpenRouter reasoning.",
                        latency_ms=0,
                    )
                except Exception as exc:
                    logger.warning("evidence_openrouter_failed", error=str(exc))

            primary_disease = disease_candidates[0]
            
            # Build evidence chain
            evidence_chain = self._build_evidence_chain(primary_disease, observations)
            
            # Check for contradictions
            contradictions = self._check_contradictions(primary_disease, observations)
            
            # Calculate adjusted confidence
            final_confidence = self._adjust_confidence(
                primary_disease["confidence"],
                len(evidence_chain),
                len(contradictions)
            )
            
            # Identify uncertainty sources
            uncertainty = self._identify_uncertainty(observations, disease_candidates)
            
            return AgentOutput(
                agent_name=self.name,
                status="success",
                result={
                    "verified_diagnosis": primary_disease["disease"],
                    "final_confidence": final_confidence,
                    "evidence_chain": evidence_chain,
                    "supporting_evidence": [f"✓ {e}" for e in evidence_chain],
                    "contradicting_evidence": contradictions,
                    "uncertainty_sources": uncertainty,
                    "alternative_diseases": [
                        {
                            "disease": d["disease"],
                            "confidence": d["confidence"],
                            "reason_ranked_lower": f"Fewer symptom matches ({d.get('symptom_matches', 0)} vs {primary_disease.get('symptom_matches', 0)})"
                        }
                        for d in disease_candidates[1:3]  # Top 2 alternatives
                    ]
                },
                confidence=final_confidence,
                reasoning=f"Diagnosis verified with {final_confidence:.1%} confidence. {len(evidence_chain)} supporting observations. {len(contradictions)} potential contradictions noted.",
                latency_ms=0,
            )
        
        except Exception as e:
            self.logger.error("evidence_agent_error", error=str(e))
            raise

    def _system_prompt(self) -> str:
        return (
            "You are an evidence verification assistant for crop diagnosis. "
            "Use only the provided candidates and observations. Return structured JSON only. "
            "Do not invent new diseases. Keep explanations concise and grounded in the inputs."
        )

    def _user_prompt(self, disease_candidates: List[Dict[str, Any]], observations: List[Dict[str, Any]]) -> str:
        return (
            f"Candidates: {disease_candidates}\n"
            f"Observations: {observations}\n"
            "Verify the most likely diagnosis, adjust confidence, and identify evidence and uncertainties."
        )
    
    def _build_evidence_chain(self, disease: Dict, observations: List[Dict]) -> List[str]:
        """Build list of supporting evidence."""
        chain = []
        
        for obs in observations:
            category = obs.get("category", "")
            confidence = obs.get("confidence", 0.0)
            description = obs.get("description", "")
            
            chain.append(
                f"{category.replace('_', ' ').title()} observed ({confidence:.0%} confidence): {description}"
            )
        
        return chain
    
    def _check_contradictions(self, disease: Dict, observations: List[Dict]) -> List[str]:
        """Check for contradicting evidence."""
        contradictions = []
        
        # Simple heuristic: if average observation confidence is low, flag it
        avg_confidence = (
            sum(o.get("confidence", 0.5) for o in observations) / len(observations)
            if observations
            else 0.5
        )
        
        if avg_confidence < 0.6:
            contradictions.append("Low average observation confidence (< 0.6)")
        
        return contradictions
    
    def _adjust_confidence(self, base_confidence: float, evidence_count: int, contradiction_count: int) -> float:
        """Adjust confidence based on evidence and contradictions."""
        adjusted = base_confidence
        
        # Boost for strong evidence
        if evidence_count >= 3:
            adjusted += 0.05
        elif evidence_count < 1:
            adjusted -= 0.1
        
        # Penalize for contradictions
        adjusted -= (contradiction_count * 0.08)
        
        # Cap at [0, 1]
        return max(0.0, min(1.0, round(adjusted, 3)))
    
    def _identify_uncertainty(self, observations: List[Dict], candidates: List[Dict]) -> List[str]:
        """Identify sources of uncertainty."""
        uncertainty = []
        
        if not observations:
            uncertainty.append("No visual observations available")
        
        if len(candidates) > 1 and abs(candidates[0]["confidence"] - candidates[1]["confidence"]) < 0.1:
            uncertainty.append("Multiple diseases with similar confidence")
        
        low_confidence_obs = [o for o in observations if o.get("confidence", 0.5) < 0.7]
        if low_confidence_obs:
            uncertainty.append(f"{len(low_confidence_obs)} observations with low confidence")
        
        return uncertainty
