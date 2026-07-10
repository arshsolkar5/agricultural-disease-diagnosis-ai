import os
from typing import List, Dict, Any
from pathlib import Path
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("rag.loader")

class DocumentLoader:
    """Load documents from disk."""
    
    @staticmethod
    def load_markdown(file_path: str) -> str:
        """Load markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def load_text(file_path: str) -> str:
        """Load text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def load_all_documents(docs_path: str = None) -> List[Dict[str, Any]]:
        """Load all markdown/text documents from directory."""
        if docs_path is None:
            docs_path = settings.documents_path
        
        documents = []
        
        if not os.path.exists(docs_path):
            logger.warning("documents_path_not_found", path=docs_path)
            return documents
        
        for file_path in sorted(Path(docs_path).rglob("*")):
            if not file_path.is_file() or file_path.suffix.lower() not in {".md", ".markdown", ".txt"}:
                continue
            try:
                loader = DocumentLoader.load_markdown if file_path.suffix.lower() in {".md", ".markdown"} else DocumentLoader.load_text
                content = loader(str(file_path))
                documents.append({
                    "source": str(file_path),
                    "title": file_path.stem,
                    "content": content,
                })
                logger.info("document_loaded", source=file_path.stem)
            except Exception as e:
                logger.error("document_load_failed", file=str(file_path), error=str(e))
        
        return documents
