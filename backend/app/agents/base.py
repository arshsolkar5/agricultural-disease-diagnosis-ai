from abc import ABC, abstractmethod
import time
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.common import AgentOutput
from app.utils.logger import get_logger, log_agent_execution
from app.utils.exceptions import AgentException
from app.database.engine import SessionLocal
from app.database.models import AgentMetrics

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.logger = get_logger(f"agent.{name}")
        self.execution_count = 0
        self.error_count = 0
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        Execute the agent with given input.
        
        Must return AgentOutput with:
        - status: success, fallback, or error
        - result: processed output
        - confidence: 0.0-1.0
        - reasoning: why this result
        - latency_ms: execution time
        """
        pass
    
    async def run(self, input_data: Dict[str, Any]) -> AgentOutput:
        """Wrapper around execute with error handling and logging."""
        start_time = time.time()
        self.execution_count += 1
        status = "success"
        
        try:
            output = await self.execute(input_data)
            latency_ms = (time.time() - start_time) * 1000
            output.latency_ms = latency_ms
            
            log_agent_execution(
                agent_name=self.name,
                input_data=self._sanitize_payload(input_data),
                output_data=output.result,
                confidence=output.confidence,
                latency_ms=latency_ms,
            )
            
            self._update_metrics(success=True, latency_ms=latency_ms)
            
            return output
            
        except Exception as e:
            self.error_count += 1
            status = "error"
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error(
                "agent_error",
                agent=self.name,
                error=str(e),
                latency_ms=latency_ms,
            )
            self._update_metrics(success=False, latency_ms=latency_ms)
            raise AgentException(
                agent_name=self.name,
                message=str(e),
                fallback_available=False
            )

    def _sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remove oversized or sensitive fields from logs."""
        sanitized = dict(payload)
        if "image_base64" in sanitized:
            sanitized["image_base64"] = "[redacted]"
        return sanitized
    
    def _update_metrics(self, success: bool, latency_ms: float) -> None:
        """Update agent metrics in database."""
        try:
            db: Session = SessionLocal()
            try:
                metrics = db.query(AgentMetrics).filter(AgentMetrics.agent_name == self.name).first()
                
                if metrics is None:
                    metrics = AgentMetrics(
                        agent_name=self.name,
                        total_executions=1,
                        error_count=0 if success else 1,
                        average_latency_ms=latency_ms,
                        last_execution_time=datetime.fromtimestamp(time.time()),
                        last_status="success" if success else "error"
                    )
                    db.add(metrics)
                else:
                    metrics.total_executions += 1
                    if not success:
                        metrics.error_count += 1
                    # Update average latency using weighted average
                    metrics.average_latency_ms = (
                        (metrics.average_latency_ms * (metrics.total_executions - 1) + latency_ms) / 
                        metrics.total_executions
                    )
                    metrics.last_execution_time = datetime.fromtimestamp(time.time())
                    metrics.last_status = "success" if success else "error"
                
                db.commit()
            except Exception as e:
                db.rollback()
                self.logger.warning("metrics_update_failed", agent=self.name, error=str(e))
            finally:
                db.close()
        except Exception as e:
            # Don't fail agent execution if metrics update fails
            self.logger.warning("metrics_db_error", agent=self.name, error=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Return agent status metrics from database."""
        try:
            db: Session = SessionLocal()
            try:
                metrics = db.query(AgentMetrics).filter(AgentMetrics.agent_name == self.name).first()
                
                if metrics is None:
                    # Return default status if no metrics exist yet
                    return {
                        "agent_name": self.name,
                        "total_executions": 0,
                        "error_count": 0,
                        "success_rate": 0.0,
                        "average_latency_ms": 0.0,
                        "last_execution_time": None,
                        "last_status": None
                    }
                
                success_rate = (
                    (metrics.total_executions - metrics.error_count) / metrics.total_executions
                    if metrics.total_executions > 0
                    else 0.0
                )
                
                return {
                    "agent_name": metrics.agent_name,
                    "total_executions": metrics.total_executions,
                    "error_count": metrics.error_count,
                    "success_rate": success_rate,
                    "average_latency_ms": metrics.average_latency_ms,
                    "last_execution_time": metrics.last_execution_time.isoformat() if metrics.last_execution_time else None,
                    "last_status": metrics.last_status
                }
            finally:
                db.close()
        except Exception as e:
            self.logger.warning("metrics_read_failed", agent=self.name, error=str(e))
            # Fallback to instance-level metrics
            success_rate = (
                (self.execution_count - self.error_count) / self.execution_count
                if self.execution_count > 0
                else 0.0
            )
            return {
                "agent_name": self.name,
                "total_executions": self.execution_count,
                "error_count": self.error_count,
                "success_rate": success_rate,
                "average_latency_ms": 0.0,
                "last_execution_time": None,
                "last_status": None
            }
