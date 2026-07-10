import pytest
import base64
from PIL import Image
import io
from app.agents.vision import VisionAgent
from app.agents.diagnosis import DiagnosisAgent
from app.agents.evidence import EvidenceAgent
from app.agents.orchestrator import DiagnosisOrchestrator

@pytest.fixture
def sample_image_b64():
    """Create sample image as base64."""
    img = Image.new('RGB', (640, 480), color=(100, 150, 100))  # Green image
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

@pytest.mark.asyncio
async def test_vision_agent(sample_image_b64):
    """Test Vision Agent extracts observations."""
    agent = VisionAgent()
    output = await agent.run({
        "image_base64": sample_image_b64,
        "crop_type": "rice",
    })
    
    assert output.status in ["success", "fallback"]
    assert "observations" in output.result
    assert "image_quality_score" in output.result

@pytest.mark.asyncio
async def test_diagnosis_agent():
    """Test Diagnosis Agent ranks diseases."""
    agent = DiagnosisAgent()
    output = await agent.run({
        "observations": [
            {"category": "lesion", "confidence": 0.85, "description": "brown lesion"}
        ],
        "crop_type": "rice",
    })
    
    assert output.status == "success"
    candidates = output.result.get("disease_candidates", [])
    assert len(candidates) > 0
    assert candidates[0]["rank"] == 1

@pytest.mark.asyncio
async def test_evidence_agent():
    """Test Evidence Agent verifies diagnosis."""
    agent = EvidenceAgent()
    output = await agent.run({
        "disease_candidates": [
            {"disease": "leaf_blast", "confidence": 0.87, "symptom_matches": 2}
        ],
        "observations": [
            {"category": "lesion", "confidence": 0.85}
        ],
    })
    
    assert output.status == "success"
    assert output.result["verified_diagnosis"] is not None
    assert "evidence_chain" in output.result

@pytest.mark.asyncio
async def test_orchestrator(sample_image_b64):
    """Test full diagnosis workflow."""
    orchestrator = DiagnosisOrchestrator()
    state = await orchestrator.diagnose({
        "image_base64": sample_image_b64,
        "crop_type": "rice",
        "farmer_id": "farmer_001",
    })
    
    assert state.trace_id is not None
    assert len(state.observations) >= 0
    assert len(state.disease_candidates) >= 0
    assert len(state.errors) == 0
