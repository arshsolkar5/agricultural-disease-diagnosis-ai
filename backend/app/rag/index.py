import faiss
import numpy as np
import os
from typing import List, Tuple
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.index")

class FAISSIndex:
    """FAISS vector index management."""
    
    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.index_dir = settings.faiss_index_path
        os.makedirs(self.index_dir, exist_ok=True)
        self.index_path = os.path.join(self.index_dir, "index.faiss")
        
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info("faiss_index_loaded", path=self.index_path)
            except Exception as exc:
                logger.warning("faiss_index_load_failed", path=self.index_path, error=str(exc))
                self.index = faiss.IndexIDMap(faiss.IndexFlatL2(embedding_dim))
                self._save()
        else:
            base_index = faiss.IndexFlatL2(embedding_dim)
            self.index = faiss.IndexIDMap(base_index)
            logger.info("faiss_index_created", dim=embedding_dim)
    
    def add(self, embeddings: np.ndarray, ids: List[int]) -> None:
        """Add embeddings to index."""
        if embeddings.shape[0] == 0:
            return
        
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.index.add_with_ids(embeddings, np.array(ids, dtype=np.int64))
        self._save()
        logger.info("embeddings_added", count=len(ids))
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
        """Search index."""
        # Ensure 2D shape: (1, embedding_dim)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = np.ascontiguousarray(query_embedding, dtype=np.float32)
        distances, indices = self.index.search(query_embedding, k)
        return distances[0], indices[0]
    
    def _save(self) -> None:
        """Save index to disk."""
        faiss.write_index(self.index, self.index_path)

    def reset(self) -> None:
        """Reset the index to an empty state."""
        self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.embedding_dim))
        self._save()

    def size(self) -> int:
        """Get number of vectors in index."""
        return self.index.ntotal
