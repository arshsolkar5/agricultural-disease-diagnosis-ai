class AgriSenseException(Exception):
    """Base exception for all AgriSense errors."""
    pass

class AgentException(AgriSenseException):
    """Raised when an agent fails."""
    def __init__(self, agent_name: str, message: str, fallback_available: bool = False):
        self.agent_name = agent_name
        self.message = message
        self.fallback_available = fallback_available
        super().__init__(f"Agent {agent_name} failed: {message}")

class ValidationException(AgriSenseException):
    """Raised when input validation fails."""
    pass

class DiagnosisException(AgriSenseException):
    """Raised during diagnosis pipeline."""
    pass

class RAGException(AgriSenseException):
    """Raised by RAG service."""
    pass

class ImageProcessingException(AgriSenseException):
    """Raised by vision processing."""
    pass

class OpenRouterException(AgriSenseException):
    """Raised when OpenRouter integration fails."""
    pass

class OpenRouterAuthenticationException(OpenRouterException):
    """Raised when the OpenRouter API key is missing or invalid."""
    pass

class OpenRouterTimeoutException(OpenRouterException):
    """Raised when OpenRouter requests time out."""
    pass

class OpenRouterResponseException(OpenRouterException):
    """Raised when OpenRouter returns an invalid or unexpected response."""
    pass
