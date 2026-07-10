import json
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.config import settings
from app.llm import explain_with_openrouter, get_openrouter_client
from app.models.common import AgentOutput
from app.models.llm import EconomicsAnalysis
from app.utils.logger import get_logger

logger = get_logger("agent.economics")


class EconomicsAgent(BaseAgent):
    """Economics Agent: calculates treatment cost-benefit."""

    DEFAULT_YIELD = 50
    DEFAULT_PRICE = 1800

    def __init__(self):
        super().__init__(
            name="EconomicsAgent",
            description="Calculates treatment ROI and economics",
        )
        self.client = get_openrouter_client()

    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        treatments = input_data.get("treatments", [])
        yield_pot = input_data.get("yield_potential", self.DEFAULT_YIELD)
        price = input_data.get("market_price", self.DEFAULT_PRICE)

        if self.client.is_configured and treatments:
            try:
                analysis = await explain_with_openrouter(
                    system_prompt=self._system_prompt(),
                    user_prompt=self._user_prompt(treatments, yield_pot, price),
                    schema_model=EconomicsAnalysis,
                    temperature=0.1,
                    max_tokens=1200,
                    reasoning_effort="medium",
                    model=settings.openrouter_model,
                )
                # If LLM returns empty analysis, use fallback
                if not analysis.analysis:
                    logger.warning("economics_openrouter_empty_analysis", error="LLM returned empty analysis array")
                    raise ValueError("Empty analysis from LLM")
                
                # Validate that economics values are varied (not all identical)
                analysis_dicts = [line.model_dump() for line in analysis.analysis]
                if len(analysis_dicts) > 1:
                    net_profits = [item.get("net_profit_rupees", 0) for item in analysis_dicts]
                    rois = [item.get("roi_percent", 0) for item in analysis_dicts]
                    
                    # Check if all values are identical (within small tolerance)
                    profits_identical = all(abs(p - net_profits[0]) < 1 for p in net_profits)
                    rois_identical = all(abs(r - rois[0]) < 0.1 for r in rois)
                    
                    if profits_identical and rois_identical:
                        logger.warning(
                            "economics_openrouter_identical_values",
                            error="LLM returned identical economics values for all treatments, using fallback",
                            net_profits=net_profits,
                            rois=rois,
                        )
                        raise ValueError("LLM returned identical values for all treatments")
                
                return AgentOutput(
                    agent_name=self.name,
                    status="success",
                    result={
                        "analysis": analysis_dicts,
                        "summary": analysis.summary,
                        "assumptions": analysis.assumptions,
                        "analysis_source": "openrouter",
                    },
                    confidence=0.95 if analysis.analysis else 0.0,
                    reasoning=analysis.summary or "Economics evaluated by OpenRouter.",
                    latency_ms=0,
                )
            except Exception as exc:
                logger.warning("economics_openrouter_failed", error=str(exc))

        if not treatments:
            return AgentOutput(
                agent_name=self.name,
                status="fallback",
                result={"analysis": [], "analysis_source": "fallback"},
                confidence=0.0,
                reasoning="No treatments to analyze",
                latency_ms=0,
            )

        analysis = self._fallback_analysis(treatments, yield_pot, price)
        analysis.sort(key=lambda x: x["roi_percent"], reverse=True)
        return AgentOutput(
            agent_name=self.name,
            status="success",
            result={"analysis": analysis, "analysis_source": "fallback"},
            confidence=0.95,
            reasoning=f"Analyzed economics for {len(analysis)} treatments",
            latency_ms=0,
        )

    def _system_prompt(self) -> str:
        return (
            "You are an agricultural economics assistant. Calculate practical ROI and "
            "break-even estimates from the provided treatment options. Return structured JSON only."
        )

    def _user_prompt(self, treatments: List[Dict[str, Any]], yield_pot: float, price: float) -> str:
        return json.dumps(
            {
                "treatments": treatments,
                "yield_potential": yield_pot,
                "market_price": price,
                "instructions": [
                    "Estimate yield gain, revenue gain, net profit, ROI, and break-even days for each treatment.",
                    "Use conservative assumptions if the treatment data is incomplete.",
                    "Include a short summary and the assumptions used.",
                    "IMPORTANT: Each treatment MUST have different economics values based on their specific costs and yield recovery percentages.",
                    "Do not return identical values for different treatments - calculate each one individually.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )

    def _fallback_analysis(
        self,
        treatments: List[Dict[str, Any]],
        yield_pot: float,
        price: float,
    ) -> List[Dict[str, Any]]:
        analysis = []
        # Default price if None
        if price is None:
            price = 1800.0
        
        for treatment in treatments:
            cost = treatment.get("cost_per_acre", treatment.get("cost", 0)) or 0
            recovery_raw = treatment.get("yield_recovery_percent", treatment.get("yield_recovery"))
            recovery_pct = (float(recovery_raw) if recovery_raw is not None else 0) / 100.0
            yield_gain = yield_pot * recovery_pct
            revenue_gain = yield_gain * price
            roi = ((revenue_gain - cost) / cost * 100) if cost > 0 else 0
            break_even_days = (cost / (revenue_gain / 365)) if revenue_gain > 0 else 999

            logger.info(
                "economics_fallback_calculation",
                treatment=treatment.get("name", "Unknown"),
                cost=cost,
                recovery_raw=recovery_raw,
                recovery_pct=recovery_pct,
                yield_gain=yield_gain,
                revenue_gain=revenue_gain,
                roi=roi,
                break_even_days=break_even_days,
            )

            analysis.append(
                {
                    "treatment": treatment.get("name", "Unknown"),
                    "cost_per_acre": cost,
                    "expected_yield_gain_quintals": round(yield_gain, 2),
                    "revenue_gain_rupees": round(revenue_gain, 0),
                    "net_profit_rupees": round(revenue_gain - cost, 0),
                    "roi_percent": round(roi, 1),
                    "break_even_days": round(break_even_days, 0),
                    "confidence": treatment.get("confidence", 0.8),
                }
            )
        return analysis
