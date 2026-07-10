import hashlib
from pathlib import Path
from typing import Any, List, Optional, Union

import numpy as np

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.embedder")


class TextEmbedder:
    """Embed text using SentenceTransformers, with a deterministic fallback."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name or settings.rag_embedding_model
        self.model: Optional[Any] = None
        self.embedding_dim = 384
        self.fallback_mode = True
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            cached_model_path = self._find_cached_model_path()
            if cached_model_path is None:
                raise FileNotFoundError(f"No cached SentenceTransformer model found for {self.model_name}")

            self.model = SentenceTransformer(str(cached_model_path))
            self.embedding_dim = int(self.model.get_sentence_embedding_dimension())
            self.fallback_mode = False
            logger.info(
                "embedder_loaded",
                model=self.model_name,
                dim=self.embedding_dim,
            )
        except Exception as exc:
            self.model = None
            self.fallback_mode = True
            logger.warning(
                "embedder_fallback_enabled",
                model=self.model_name,
                dim=self.embedding_dim,
                reason=str(exc),
            )

    def _find_cached_model_path(self) -> Optional[Path]:
        model_slug = self.model_name.replace("/", "--")
        hub_root = Path.home() / ".cache" / "huggingface" / "hub"
        snapshots_root = hub_root / f"models--{model_slug}" / "snapshots"
        if not snapshots_root.exists():
            return None

        for snapshot in sorted(path for path in snapshots_root.iterdir() if path.is_dir()):
            modules_file = snapshot / "modules.json"
            config_file = snapshot / "config_sentence_transformers.json"
            if modules_file.exists() and config_file.exists():
                return snapshot
        return None

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]

        if self.model is None:
            return self._fallback_embed(texts)

        return self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        if self.model is None:
            return self._fallback_embed(texts)

        return self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def _fallback_embed(self, texts: List[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            repeated = (digest * ((self.embedding_dim // len(digest)) + 2))[: self.embedding_dim]
            vector = np.frombuffer(repeated, dtype=np.uint8).astype(np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector /= norm
            vectors.append(vector)

        return np.vstack(vectors)
