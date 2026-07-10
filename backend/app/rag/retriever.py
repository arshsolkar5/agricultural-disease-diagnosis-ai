from __future__ import annotations

import json
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import settings
from app.rag.chunker import DocumentChunker
from app.rag.embedder import TextEmbedder
from app.rag.index import FAISSIndex
from app.rag.loader import DocumentLoader
from app.utils.logger import get_logger

logger = get_logger("rag.retriever")


class RAGRetriever:
    """Semantic retriever over local crop documents backed by FAISS."""

    def __init__(
        self,
        db: Any = None,
        docs_path: Optional[str] = None,
        index_path: Optional[str] = None,
        embedding_model: Optional[str] = None,
        chunk_size: int = 400,
        overlap: int = 100,
        rebuild: bool = False,
    ) -> None:
        self.db = db
        self.docs_path = Path(docs_path or settings.documents_path)
        self.index_dir = Path(index_path or settings.faiss_index_path)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "index.faiss"
        self.chunk_store_path = self.index_dir / "chunks.json"
        self.manifest_path = self.index_dir / "manifest.json"
        self.embedder = TextEmbedder(embedding_model or settings.rag_embedding_model)
        self.chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
        self.index = FAISSIndex(embedding_dim=self.embedder.embedding_dim)
        self.chunk_store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

        self._ensure_index(rebuild=rebuild)

    def _ensure_index(self, rebuild: bool = False) -> None:
        with self._lock:
            stored_manifest = self._load_manifest()
            current_manifest = self._build_manifest()

            if rebuild or not self._is_index_usable(stored_manifest, current_manifest):
                self._rebuild_index(current_manifest)
                return

            self.chunk_store = self._load_chunk_store()
            if not self.chunk_store or self.index.size() != len(self.chunk_store):
                self._rebuild_index(current_manifest)

    def _is_index_usable(
        self,
        stored_manifest: Optional[Dict[str, Any]],
        current_manifest: Dict[str, Any],
    ) -> bool:
        if not self.index_path.exists() or not self.chunk_store_path.exists() or not self.manifest_path.exists():
            return False
        if stored_manifest != current_manifest:
            return False
        return self.index.size() > 0

    def _build_manifest(self) -> Dict[str, Any]:
        documents = []
        if self.docs_path.exists():
            for path in sorted(self.docs_path.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in {".md", ".markdown", ".txt"}:
                    continue
                stat = path.stat()
                documents.append(
                    {
                        "path": str(path.resolve()),
                        "size": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns,
                    }
                )

        return {
            "documents": documents,
            "docs_path": str(self.docs_path.resolve()) if self.docs_path.exists() else str(self.docs_path),
            "embedding_model": self.embedder.model_name,
            "embedding_dim": self.embedder.embedding_dim,
            "chunk_size": self.chunker.chunk_size,
            "overlap": self.chunker.overlap,
        }

    def _load_manifest(self) -> Optional[Dict[str, Any]]:
        if not self.manifest_path.exists():
            return None
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("rag_manifest_load_failed", error=str(exc))
            return None

    def _load_chunk_store(self) -> Dict[str, Dict[str, Any]]:
        if not self.chunk_store_path.exists():
            return {}
        try:
            raw = json.loads(self.chunk_store_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                return {str(key): value for key, value in raw.items() if isinstance(value, dict)}
        except Exception as exc:
            logger.warning("rag_chunk_store_load_failed", error=str(exc))
        return {}

    def _save_metadata(self, manifest: Dict[str, Any]) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        self.chunk_store_path.write_text(json.dumps(self.chunk_store, indent=2), encoding="utf-8")

    def _rebuild_index(self, manifest: Optional[Dict[str, Any]] = None) -> None:
        documents = DocumentLoader.load_all_documents(str(self.docs_path))
        chunks: List[Dict[str, Any]] = []

        for doc in documents:
            doc_chunks = self.chunker.chunk(
                doc["content"],
                {
                    "source": doc["source"],
                    "title": doc["title"],
                },
            )
            for chunk in doc_chunks:
                chunk["document_source"] = doc["source"]
                chunk["document_title"] = doc["title"]
                chunks.append(chunk)

        if not chunks:
            logger.warning("rag_index_empty", docs_path=str(self.docs_path))
            self.index.reset()
            self.chunk_store = {}
            self._save_metadata(manifest or self._build_manifest())
            return

        embeddings = self.embedder.embed_batch([chunk["text"] for chunk in chunks])
        ids = list(range(1, len(chunks) + 1))

        self.index.reset()
        self.index.add(embeddings, ids)

        self.chunk_store = {
            str(chunk_id): {**chunk, "embedding_id": chunk_id}
            for chunk_id, chunk in zip(ids, chunks)
        }
        self._save_metadata(manifest or self._build_manifest())

        logger.info(
            "rag_index_rebuilt",
            document_count=len(documents),
            chunk_count=len(chunks),
            embedding_model=self.embedder.model_name,
        )

    def retrieve(self, query: str, top_k: int = 5, k: Optional[int] = None, crop_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return the most relevant document chunks for a query."""
        limit = k if k is not None else top_k
        if limit <= 0:
            return []

        with self._lock:
            if not self.chunk_store or self.index.size() == 0:
                self._rebuild_index()
                if not self.chunk_store:
                    return []

            query_embedding = self.embedder.embed(query)
            search_k = min(max(limit * 4, limit), self.index.size())
            distances, indices = self.index.search(query_embedding, k=search_k)

            candidates: List[Dict[str, Any]] = []
            for distance, embedding_id in zip(distances, indices):
                if int(embedding_id) == -1:
                    continue

                chunk = self._get_chunk(int(embedding_id))
                if not chunk:
                    continue

                # Crop-aware filtering: penalize documents from irrelevant crops
                crop_boost = 0.0
                if crop_type:
                    doc_title = chunk.get("document_title", "").lower()
                    doc_source = chunk.get("source", "").lower()
                    doc_text = chunk.get("text", "").lower()
                    crop_lower = crop_type.lower()
                    
                    # Check if document is relevant to the specified crop
                    crop_keywords = {
                        "tomato": ["tomato", "solanaceous", "lycopersici"],
                        "rice": ["rice", "oryzae", "oryza"],
                        "wheat": ["wheat", "triticum"],
                        "potato": ["potato", "solanum tuberosum"],
                        "maize": ["maize", "corn", "zea"],
                        "cotton": ["cotton", "gossypium"],
                        "sugarcane": ["sugarcane", "saccharum"],
                        "soybean": ["soybean", "glycine"],
                        "groundnut": ["groundnut", "peanut", "arachis"],
                        "chickpea": ["chickpea", "gram", "cicer"],
                        "banana": ["banana", "musa"],
                        "mango": ["mango", "mangifera"],
                        "citrus": ["citrus", "orange", "lemon", "lime"],
                    }
                    
                    # Get keywords for the target crop
                    target_keywords = crop_keywords.get(crop_lower, [crop_lower])
                    
                    # Check if document contains target crop keywords
                    doc_content = f"{doc_title} {doc_source} {doc_text}"
                    has_target_crop = any(keyword in doc_content for keyword in target_keywords)
                    
                    if has_target_crop:
                        crop_boost = 0.2
                    else:
                        # Penalize if document clearly belongs to a different crop
                        for other_crop, keywords in crop_keywords.items():
                            if other_crop != crop_lower:
                                if any(keyword in doc_content for keyword in keywords):
                                    crop_boost = -0.4
                                    break

                semantic_score = self._distance_to_score(float(distance))
                lexical_score = self._lexical_score(query, str(chunk.get("text", "")))
                title_boost = self._title_boost(query, chunk)
                score = max(
                    0.0,
                    min(1.0, round((semantic_score * 0.6) + (lexical_score * 0.15) + title_boost + crop_boost, 3)),
                )

                enriched = dict(chunk)
                enriched.update(
                    {
                        "embedding_id": int(embedding_id),
                        "score": score,
                        "semantic_score": round(semantic_score, 3),
                        "lexical_score": round(lexical_score, 3),
                        "distance": round(float(distance), 4),
                    }
                )
                candidates.append(enriched)

            candidates.sort(key=lambda item: item.get("score", 0.0), reverse=True)
            return candidates[:limit]

    def _get_chunk(self, embedding_id: int) -> Optional[Dict[str, Any]]:
        return self.chunk_store.get(str(embedding_id)) or self.chunk_store.get(embedding_id)

    def _distance_to_score(self, distance: float) -> float:
        if distance < 0:
            return 0.0
        return 1.0 / (1.0 + distance)

    def _lexical_score(self, query: str, text: str) -> float:
        query_terms = {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2}
        text_terms = {term for term in re.findall(r"[a-z0-9]+", text.lower()) if len(term) > 2}
        if not query_terms or not text_terms:
            return 0.0

        overlap = len(query_terms & text_terms)
        if overlap == 0:
            return 0.0
        return min(1.0, overlap / max(1, len(query_terms)))

    def _title_boost(self, query: str, chunk: Dict[str, Any]) -> float:
        title = f"{chunk.get('title', '')} {chunk.get('source', '')}".lower()
        if not title.strip():
            return 0.0
        query_terms = {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 3}
        if any(term in title for term in query_terms):
            return 0.05
        return 0.0
