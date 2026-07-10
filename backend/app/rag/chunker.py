from typing import List, Dict, Any
from app.utils.logger import get_logger

logger = get_logger("rag.chunker")

class DocumentChunker:
    """Split documents into chunks with overlap."""
    
    def __init__(self, chunk_size: int = 400, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Chunk text into overlapping segments.
        
        Returns:
        [
            {"text": "chunk content", "chunk_id": 0, "source": "doc_id", ...metadata}
        ]
        """
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text.strip()) < 50:  # Skip tiny chunks
                continue
            
            chunk_id = i // (self.chunk_size - self.overlap)
            chunks.append({
                "text": chunk_text,
                "chunk_id": chunk_id,
                "source": metadata.get("source", "unknown"),
                "title": metadata.get("title", ""),
                "page": metadata.get("page", 0),
                "metadata": metadata,
            })
        
        logger.info("document_chunked", source=metadata.get("source"), chunk_count=len(chunks))
        return chunks
