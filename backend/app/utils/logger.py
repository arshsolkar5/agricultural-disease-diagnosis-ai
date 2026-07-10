import structlog
import logging
from typing import Any, Dict
from app.config import settings

# Respect the configured runtime log level.
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
)

# Configure structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

def log_agent_execution(
    agent_name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    confidence: float,
    latency_ms: float,
    error: str = None,
) -> None:
    """Log agent execution with structured data."""
    logger = get_logger(f"agent.{agent_name}")
    logger.info(
        "agent_execution",
        agent=agent_name,
        input=input_data,
        output=output_data,
        confidence=confidence,
        latency_ms=latency_ms,
        error=error,
    )
