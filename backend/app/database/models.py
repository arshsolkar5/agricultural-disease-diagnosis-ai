from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.database.base import Base

class Farmer(Base):
    """User/farmer profile."""
    __tablename__ = "farmers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    location = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    diagnoses = relationship("Diagnosis", back_populates="farmer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Farmer {self.email}>"

class Diagnosis(Base):
    """Single diagnosis record."""
    __tablename__ = "diagnoses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    farmer_id = Column(UUID(as_uuid=True), ForeignKey("farmers.id"), nullable=True, index=True)
    crop_type = Column(String(100), nullable=False, index=True)
    primary_disease = Column(String(255), nullable=True)
    confidence = Column(Float, default=0.0)  # 0.0-1.0
    image_metadata = Column(JSON, nullable=True)  # {filename, size, format}
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    farmer = relationship("Farmer", back_populates="diagnoses")
    observations = relationship("DiagnosisObservation", back_populates="diagnosis", cascade="all, delete-orphan")
    evidence = relationship("DiagnosisEvidence", back_populates="diagnosis", cascade="all, delete-orphan")
    treatments = relationship("Treatment", back_populates="diagnosis", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="diagnosis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Diagnosis {self.id} {self.crop_type}>"

class DiagnosisObservation(Base):
    """Visual symptom observed by Vision Agent."""
    __tablename__ = "diagnosis_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # lesion, necrosis, spot, etc.
    description = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    location = Column(String(255), nullable=True)
    bounding_box = Column(JSON, nullable=True)  # {x, y, w, h}
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="observations")
    
    def __repr__(self):
        return f"<Observation {self.category}>"

class DiagnosisEvidence(Base):
    """Disease hypothesis with supporting/contradicting evidence."""
    __tablename__ = "diagnosis_evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"), nullable=False, index=True)
    disease_name = Column(String(255), nullable=False, index=True)
    confidence = Column(Float, default=0.0)
    rank = Column(Integer, default=0)  # 1 = primary, 2 = secondary, etc.
    observed_symptoms = Column(JSON, nullable=True)  # [symptom1, symptom2, ...]
    supporting_evidence = Column(JSON, nullable=True)  # [evidence1, evidence2, ...]
    contradicting_evidence = Column(JSON, nullable=True)  # [evidence1, ...]
    reasoning = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="evidence")
    
    def __repr__(self):
        return f"<Evidence {self.disease_name} {self.confidence:.2f}>"

class Treatment(Base):
    """Recommended treatment action."""
    __tablename__ = "treatments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"), nullable=False, index=True)
    treatment_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    estimated_cost = Column(Float, nullable=True)
    expected_yield_recovery = Column(Float, nullable=True)  # percentage
    estimated_days_to_recovery = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="treatments")
    
    def __repr__(self):
        return f"<Treatment {self.treatment_name}>"

class AgentLog(Base):
    """Agent execution trace for observability."""
    __tablename__ = "agent_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey("diagnoses.id"), nullable=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # pending, running, success, fallback, error
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    diagnosis = relationship("Diagnosis", back_populates="agent_logs")
    
    def __repr__(self):
        return f"<AgentLog {self.agent_name} {self.status}>"

class Document(Base):
    """RAG knowledge base document metadata."""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source = Column(String(500), nullable=False, index=True)  # URL or file path
    content_type = Column(String(50), nullable=False)  # pdf, markdown, html, etc.
    chunk_count = Column(Integer, default=0)
    is_indexed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Document {self.title}>"


class VisionObservationCache(Base):
    """Cached structured output for Gemini vision analysis."""

    __tablename__ = "vision_observation_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_hash = Column(String(64), nullable=False, unique=True, index=True)
    original_hash = Column(String(64), nullable=True, index=True)
    crop_type = Column(String(100), nullable=True, index=True)
    gemini_model = Column(String(100), nullable=False, default="gemini-2.0-flash-exp")
    image_bytes = Column(Integer, nullable=True)
    preprocessed_bytes = Column(Integer, nullable=True)
    image_quality_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    observations = Column(JSON, nullable=False, default=list)
    uncertainties = Column(JSON, nullable=False, default=list)
    follow_up_questions = Column(JSON, nullable=False, default=list)
    quality_notes = Column(JSON, nullable=False, default=list)
    summary = Column(Text, nullable=True)
    needs_follow_up = Column(Boolean, default=False)
    source = Column(String(50), default="gemini")
    raw_response = Column(JSON, nullable=True)
    cache_hits = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VisionObservationCache {self.image_hash[:12]}>"


class AgentMetrics(Base):
    """Persistent metrics for agent execution tracking."""
    __tablename__ = "agent_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(100), nullable=False, unique=True, index=True)
    total_executions = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    average_latency_ms = Column(Float, default=0.0)
    last_execution_time = Column(DateTime, nullable=True)
    last_status = Column(String(50), nullable=True)  # success, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentMetrics {self.agent_name} exec={self.total_executions} err={self.error_count}>"
