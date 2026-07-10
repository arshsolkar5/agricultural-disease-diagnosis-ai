import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.base import Base
from app.database.models import Farmer, Diagnosis
import uuid

@pytest.fixture
def test_db():
    """In-memory SQLite for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_farmer_creation(test_db):
    """Test farmer model creation."""
    farmer = Farmer(
        id=uuid.uuid4(),
        name="Arsh Sharma",
        email="arsh@example.com",
        location="Ratnagiri",
        region="Maharashtra",
    )
    test_db.add(farmer)
    test_db.commit()
    
    retrieved = test_db.query(Farmer).filter_by(email="arsh@example.com").first()
    assert retrieved is not None
    assert retrieved.name == "Arsh Sharma"

def test_diagnosis_relationship(test_db):
    """Test farmer-diagnosis relationship."""
    farmer = Farmer(
        id=uuid.uuid4(),
        name="Test Farmer",
        email="test@example.com",
    )
    diagnosis = Diagnosis(
        id=uuid.uuid4(),
        farmer_id=farmer.id,
        crop_type="rice",
        primary_disease="leaf_blast",
        confidence=0.87,
    )
    test_db.add(farmer)
    test_db.add(diagnosis)
    test_db.commit()
    
    retrieved_farmer = test_db.query(Farmer).filter_by(email="test@example.com").first()
    assert len(retrieved_farmer.diagnoses) == 1
    assert retrieved_farmer.diagnoses[0].crop_type == "rice"
