import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def sample_diagnosis_request():
    """Sample diagnosis request data."""
    return {
        "image_base64": "placeholder_base64_string",
        "crop_type": "rice",
        "farmer_id": "test_farmer_001",
        "location": "Maharashtra",
    }
