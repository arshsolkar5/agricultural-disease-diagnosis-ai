from typing import Dict, Any
from app.agents.base import BaseAgent
from app.models.common import AgentOutput
from app.rag.retriever import RAGRetriever
from app.utils.logger import get_logger

logger = get_logger("agent.rag")

class RAGAgent(BaseAgent):
    """RAG Agent: Retrieves treatment knowledge."""
    
    def __init__(self, db=None):
        super().__init__(
            name="RAGAgent",
            description="Retrieves treatment knowledge from RAG system"
        )
        self.retriever = RAGRetriever(db)
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentOutput:
        """
        Retrieve treatment info for disease.
        
        Input:
        {"disease": "leaf_blast", "crop_type": "rice"}
        
        Output:
        {"retrieved_documents": [...], "sources": [...]}
        """
        try:
            disease = input_data.get("disease", "unknown")
            crop_type = input_data.get("crop_type", "")
            
            # Query RAG with crop context for better relevance
            if crop_type:
                query = f"How to treat {disease} in {crop_type}? Treatment methods, fungicides, recovery"
            else:
                query = f"How to treat {disease}? Treatment methods, fungicides, recovery"
            results = self.retriever.retrieve(query, top_k=3, crop_type=crop_type)
            
            if not results:
                return AgentOutput(
                    agent_name=self.name,
                    status="fallback",
                    result={"retrieved_documents": [], "sources": []},
                    confidence=0.0,
                    reasoning="No treatment documents found in knowledge base",
                    latency_ms=0,
                )
            
            return AgentOutput(
                agent_name=self.name,
                status="success",
                result={
                    "retrieved_documents": results,
                    "sources": list(set(r.get("source", "") for r in results)),
                    "document_count": len(results),
                },
                confidence=0.95,
                reasoning=f"Retrieved {len(results)} relevant treatment documents",
                latency_ms=0,
            )
        
        except Exception as e:
            logger.error("rag_agent_error", error=str(e))
            raise
