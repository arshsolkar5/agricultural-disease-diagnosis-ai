import pytest
from app.agents.economics_agent import EconomicsAgent
from app.agents.market_agent import MarketAgent

@pytest.mark.asyncio
async def test_economics_agent():
    """Test economics calculations."""
    agent = EconomicsAgent()
    output = await agent.run({
        "treatments": [
            {"name": "Fungicide", "cost_per_acre": 750, "yield_recovery_percent": 70, "days_to_recovery": 10, "confidence": 0.9}
        ],
        "yield_potential": 50,
        "market_price": 1800,
    })
    assert output.status == "success"
    assert "analysis" in output.result
    assert len(output.result["analysis"]) > 0
    assert output.result["analysis"][0]["roi_percent"] > 0

@pytest.mark.asyncio
async def test_market_agent():
    """Test market intelligence."""
    agent = MarketAgent()
    output = await agent.run({
        "crop_type": "rice",
        "location": "maharashtra",
    })
    assert output.status == "success"
    assert output.result["current_price_per_quintal"] > 0
    assert "recommendation" in output.result
