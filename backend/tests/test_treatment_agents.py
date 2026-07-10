import pytest
from app.agents.rag_agent import RAGAgent
from app.agents.treatment_agent import TreatmentAgent

@pytest.mark.asyncio
async def test_rag_agent():
    """Test RAG agent retrieves docs."""
    agent = RAGAgent()
    output = await agent.run({"disease": "leaf_blast", "crop_type": "rice"})
    assert output.status in ["success", "fallback"]
    assert "retrieved_documents" in output.result

@pytest.mark.asyncio
async def test_treatment_agent():
    """Test treatment agent generates recommendations."""
    agent = TreatmentAgent()
    output = await agent.run({
        "disease": "leaf_blast",
        "rag_results": [],
    })
    assert output.status == "success"
    assert "recommendations" in output.result
    assert len(output.result["recommendations"]) > 0
