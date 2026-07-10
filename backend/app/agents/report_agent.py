import json
from typing import Any, Dict

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.config import settings
from app.llm import explain_with_openrouter, get_openrouter_client
from app.models.common import AgentOutput
from app.models.llm import ReportAnalysis
from app.utils.logger import get_logger

logger = get_logger("agent.report")


class _ReportPlan(BaseModel):
    report: Dict[str, Any] = Field(default_factory=dict)


class ReportAgent(BaseAgent):
    """Report Agent: produces the final structured report."""

    def __init__(self):
        super().__init__(
            name="ReportAgent",
            description="Generates final diagnosis report",
        )
        self.client = get_openrouter_client()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        if self.client.is_configured:
            try:
                analysis = await explain_with_openrouter(
                    system_prompt=self._system_prompt(),
                    user_prompt=self._user_prompt(input_data),
                    schema_model=ReportAnalysis,
                    temperature=0.15,
                    max_tokens=1800,
                    reasoning_effort="medium",
                    model=settings.openrouter_model,
                )
                return AgentOutput(
                    agent_name=self.name,
                    status="success",
                    result={"report": analysis.model_dump(), "analysis_source": "openrouter"},
                    confidence=1.0,
                    reasoning=analysis.executive_summary,
                    latency_ms=0,
                )
            except Exception as exc:
                logger.warning("report_openrouter_failed", error=str(exc))

        report = self._fallback_report(input_data)
        return AgentOutput(
            agent_name=self.name,
            status="success",
            result={"report": report, "analysis_source": "fallback"},
            confidence=0.8,
            reasoning=report["executive_summary"],
            latency_ms=0,
        )

    def _system_prompt(self) -> str:
        return (
            "You are a report generation assistant for crop diagnosis. "
            "Summarize findings, diagnosis, treatment, market, and economics into a clean structured report. "
            "Return JSON only."
        )

    def _user_prompt(self, input_data: Dict[str, Any]) -> str:
        return json.dumps(
            {
                "crop_type": input_data.get("crop_type"),
                "location": input_data.get("location"),
                "observations": input_data.get("observations", []),
                "execution_plan": input_data.get("execution_plan", []),
                "planner_analysis": input_data.get("planner_analysis", {}),
                "disease_candidates": input_data.get("disease_candidates", []),
                "verified_diagnosis": input_data.get("verified_diagnosis"),
                "final_confidence": input_data.get("final_confidence", 0.0),
                "treatment_recommendations": input_data.get("treatment_recommendations", []),
                "market_data": input_data.get("market_data", {}),
                "economics_analysis": input_data.get("economics_analysis", []),
                "evidence_chain": input_data.get("evidence_chain", []),
                "follow_up_questions": input_data.get("follow_up_questions", []),
                "instructions": [
                    "Produce a final report with executive summary, key findings, diagnosis summary, treatment summary, market summary, economics summary, and recommended actions.",
                    "Keep the tone professional but farmer-friendly.",
                    "Do not invent facts beyond the provided inputs.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    def _fallback_report(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        diagnosis = input_data.get("verified_diagnosis") or "unknown"
        treatment_count = len(input_data.get("treatment_recommendations", []))
        market_data = input_data.get("market_data", {})
        observations = input_data.get("observations", [])
        crop_type = input_data.get("crop_type", "unknown")
        confidence = input_data.get("final_confidence", 0.0)
        
        # Build a more professional executive summary
        if diagnosis == "unknown":
            if confidence == 0.0:
                exec_summary = "Unable to determine a specific diagnosis from the provided image. Additional information or a clearer image may be required for accurate assessment."
            else:
                exec_summary = f"Preliminary analysis completed with {confidence:.1%} confidence. Further verification recommended for definitive diagnosis."
        else:
            exec_summary = f"Analysis indicates {diagnosis} with {confidence:.1%} confidence. {treatment_count} treatment option(s) identified for management."
        
        # Build key findings
        key_findings = [
            f"Primary diagnosis: {diagnosis if diagnosis != 'unknown' else 'Not determined'}",
        ]
        
        if input_data.get('image_quality_score'):
            key_findings.append(f"Image quality: {input_data.get('image_quality_score', 0):.1%}")
        else:
            key_findings.append(f"Observations reviewed: {len(observations)}")
        
        if treatment_count > 0:
            key_findings.append(f"Treatment options: {treatment_count}")
        if market_data:
            key_findings.append(f"Market analysis: Available")
        
        # Build diagnosis summary
        if diagnosis == "unknown":
            diagnosis_summary = "Unable to confirm a specific disease. The observed symptoms may indicate early-stage infection, environmental stress, or require additional context for accurate identification."
        else:
            diagnosis_summary = f"Based on visual analysis, the most likely condition is {diagnosis}. This assessment should be confirmed with additional observations if possible."
        
        # Build treatment summary
        if treatment_count > 0:
            treatment_summary = f"{treatment_count} treatment recommendation(s) provided based on the identified condition and available agricultural best practices."
        else:
            treatment_summary = "Specific treatment recommendations require a confirmed diagnosis. Please provide additional image details or consult with an agricultural expert."
        
        # Build market summary
        if market_data:
            market_trend = market_data.get('market_trend', 'stable')
            price = market_data.get('current_price_per_quintal')
            if price:
                market_summary = f"Current market price: ₹{price}/quintal with {market_trend} trend"
            else:
                market_summary = f"Market conditions indicate {market_trend} trend"
        else:
            market_summary = "Market analysis not available for this assessment"
        
        # Build recommended actions
        recommended_actions = []
        if diagnosis == "unknown":
            recommended_actions.append("Upload a clearer, well-lit image showing the affected area")
            recommended_actions.append("Include multiple angles if possible")
            recommended_actions.append("Provide information about crop type and growth stage")
        elif treatment_count > 0:
            recommended_actions.append("Review and implement the top-ranked treatment option")
            recommended_actions.append("Monitor plant response to treatment")
            recommended_actions.append("Follow preventive measures to reduce recurrence")
        else:
            recommended_actions.append("Consult with local agricultural extension service")
            recommended_actions.append("Consider preventive cultural practices")
        
        return {
            "title": "AgriSense Crop Diagnosis Report",
            "executive_summary": exec_summary,
            "key_findings": key_findings,
            "diagnosis_summary": diagnosis_summary,
            "treatment_summary": treatment_summary,
            "market_summary": market_summary,
            "economics_summary": "Economic analysis requires confirmed diagnosis and treatment selection",
            "recommended_actions": recommended_actions,
            "follow_up_questions": input_data.get("follow_up_questions", []),
        }
