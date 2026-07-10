import pytest
from app.agents.base import BaseAgent
from app.models.common import AgentOutput
from typing import Dict, Any

class MockAgent(BaseAgent):
    """Mock agent for testing."""
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        return AgentOutput(
            agent_name=self.name,
            status="success",
            result={"test": "output"},
            confidence=0.95,
            reasoning="Test reasoning",
            latency_ms=10.0,
        )

@pytest.mark.asyncio
async def test_agent_execution():
    """Test basic agent execution."""
    agent = MockAgent("test_agent", "Test agent for unit tests")
    output = await agent.run({"test": "input"})
    
    assert output.agent_name == "test_agent"
    assert output.status == "success"
    assert output.confidence == 0.95
    assert output.result == {"test": "output"}

@pytest.mark.asyncio
async def test_agent_status():
    """Test agent status tracking."""
    agent = MockAgent("test_agent")
    await agent.run({"test": "input"})
    
    status = agent.get_status()
    assert status["agent_name"] == "test_agent"
    assert status["total_executions"] == 1
    assert status["error_count"] == 0
