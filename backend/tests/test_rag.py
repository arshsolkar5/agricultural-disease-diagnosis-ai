import numpy as np

from app.rag.chunker import DocumentChunker
from app.rag.embedder import TextEmbedder
from app.rag.index import FAISSIndex
from app.rag.retriever import RAGRetriever

def test_embedder():
    """Test text embedding."""
    embedder = TextEmbedder()
    embedding = embedder.embed("Leaf blast treatment")
    assert embedding.shape == (1, 384)  # Returns (1, 384) for single text

def test_chunker():
    """Test document chunking."""
    chunker = DocumentChunker(chunk_size=100, overlap=20)
    text = "This is a sample document. " * 50
    chunks = chunker.chunk(text, {"source": "test", "title": "Test Doc"})
    assert len(chunks) > 0
    assert all("text" in c for c in chunks)

def test_faiss_index():
    """Test FAISS index."""
    index = FAISSIndex(embedding_dim=384)
    embeddings = np.random.randn(5, 384).astype(np.float32)
    ids = list(range(5))
    index.add(embeddings, ids)
    assert index.size() >= 5

def test_retriever():
    """Test semantic retrieval over the local crop corpus."""
    retriever = RAGRetriever(rebuild=True)
    results = retriever.retrieve("brown leaf lesions and fungicide treatment", top_k=2)
    assert len(results) > 0
    assert any("leaf_blast" in result.get("source", "") or "leaf blast" in result.get("title", "").lower() for result in results)
