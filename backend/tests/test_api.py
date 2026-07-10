import pytest
import base64
from PIL import Image
import io
import numpy as np
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_image_b64():
    """Create sample image with brown spots."""
    img_array = np.ones((480, 640, 3), dtype=np.uint8) * 100
    img_array[100:200, 100:200] = [80, 100, 120]
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_agents_status():
    """Test agent status endpoint."""
    response = client.get("/agents/status")
    assert response.status_code == 200
    assert "vision" in response.json()

def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "AgriSense AI"

def test_diagnosis_creation(sample_image_b64):
    """Test diagnosis creation."""
    response = client.post("/diagnosis", json={
        "image_base64": sample_image_b64,
        "crop_type": "rice",
        "farmer_id": "farmer_001",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "diagnosis_id" in data
    assert "trace_id" in data
    assert data["crop_type"] == "rice"

def test_diagnosis_validation():
    """Test input validation."""
    response = client.post("/diagnosis", json={
        "image_base64": "",
        "crop_type": "rice",
    })
    
    assert response.status_code == 400

def test_diagnosis_retrieval(sample_image_b64):
    """Test diagnosis retrieval."""
    # Create
    create_response = client.post("/diagnosis", json={
        "image_base64": sample_image_b64,
        "crop_type": "rice",
    })
    diagnosis_id = create_response.json()["diagnosis_id"]
    
    # Retrieve
    get_response = client.get(f"/diagnosis/{diagnosis_id}")
    assert get_response.status_code == 200
    assert get_response.json()["diagnosis_id"] == diagnosis_id
