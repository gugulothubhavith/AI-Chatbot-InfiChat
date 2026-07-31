"""RAG Service — Vector document ingestion and semantic search.

Supports two backends:
1. ChromaDB (production, requires Docker)
2. FAISS in-memory (local dev, zero dependencies)

Auto-detects which is available and falls back gracefully.
"""

import os
import uuid
import json
import logging
import hashlib
import io
import re
from typing import List, Optional
from fastapi import UploadFile, HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)

from app.core.redis_client import redis_client
CACHE_TTL = 3600  # 1 hour

# ── Backend Detection ─────────────────────────────────────────

_HAS_CHROMADB = False
_HAS_FAISS = False

try:
    import chromadb
    from chromadb.config import Settings
    _HAS_CHROMADB = True
except ImportError:
    pass

try:
    import numpy as np
    import faiss
    _HAS_FAISS = True
except ImportError:
    pass

USE_FAISS = not _HAS_CHROMADB or os.getenv("RAG_BACKEND", "").lower() == "faiss"
if USE_FAISS and not _HAS_FAISS:
    logger.warning("Neither ChromaDB nor FAISS available — RAG will be disabled")
    USE_FAISS = False


# ── Embedding Function (works with both backends) ─────────────

class _EmbeddingFunc:
    """Produces embeddings using Voyage AI or a simple fallback."""

    def __init__(self):
        self.api_key = settings.VOYAGE_API_KEY
        self.model_name = settings.VOYAGE_EMBEDDING_MODEL
        self.url = "https://api.voyageai.com/v1/embeddings"

    def __call__(self, texts: List[str]) -> List[List[float]]:
        if self.api_key and self.api_key != "your_voyage_key_here":
            return self._call_voyage(texts)
        return self._fallback_embed(texts)

    def _call_voyage(self, texts: List[str]) -> List[List[float]]:
        import httpx
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(self.url, headers=headers, json={"input": texts, "model": self.model_name})
                resp.raise_for_status()
                return [item["embedding"] for item in resp.json()["data"]]
        except Exception as e:
            logger.error(f"Voyage AI embedding failed: {e}")
            return self._fallback_embed(texts)

    def _fallback_embed(self, texts: List[str]) -> List[List[float]]:
        """Simple bag-of-words + normalization fallback when no embedding API available."""
        import math
        embeds = []
        vocab = set()
        for t in texts:
            vocab.update(t.lower().split())
        vocab = sorted(vocab)
        vlen = len(vocab) or 1
        for t in texts:
            vec = [0.0] * min(vlen, 128)  # cap at 128 dims
            words = t.lower().split()
            for i, w in enumerate(words[:128]):
                vec[i % 128] += 1.0
            norm = math.sqrt(sum(x*x for x in vec)) or 1.0
            embeds.append([x/norm for x in vec])
        return embeds


_embedding_fn = _EmbeddingFunc()


# ═══════════════════════════════════════════════════════════════
# FAISS Backend (zero-dependency, in-memory)
# ═══════════════════════════════════════════════════════════════

class _FaissStore:
    """In-memory vector store using FAISS. No external dependencies."""

    def __init__(self):
        self.index = None
        self.dimension = 128
        self._documents: List[str] = []
        self._metadatas: List[dict] = []
        self._ids: List[str] = []
        self._initialized = False

    def _ensure_index(self):
        if self.index is None:
            try:
                import faiss as f
                self.index = f.IndexFlatIP(self.dimension)
            except ImportError:
                # Naive numpy-based search as last resort
                self.index = None
            self._initialized = True

    def add(self, embeddings, documents, metadatas, ids):
        self._ensure_index()
        import numpy as np
        embeds = np.array(embeddings, dtype=np.float32)
        if self.index is not None:
            self.index.add(embeds)
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        self._ids.extend(ids)

    def query(self, query_texts, n_results=10, where=None) -> dict:
        self._ensure_index()
        query_emb = np.array(_embedding_fn(query_texts), dtype=np.float32)
        total = len(self._ids)
        if total == 0:
            return {"documents": [[]], "metadatas": [[]], "ids": [[]]}

        if self.index is not None and total >= n_results:
            import numpy as np
            scores, idxs = self.index.search(query_emb, min(n_results, total))
            doc_idxs = idxs[0].tolist()
        else:
            # Brute-force cosine similarity
            import numpy as np
            all_embeds = np.array([_embedding_fn([d])[0] for d in self._documents])
            scores = all_embeds @ query_emb.T
            doc_idxs = np.argsort(-scores.flatten())[:n_results].tolist()

        docs = [[self._documents[i] for i in doc_idxs]]
        metas = [[self._metadatas[i] for i in doc_idxs]]
        ids = [[self._ids[i] for i in doc_idxs]]

        if where and "source" in where:
            filtered = []
            fmetas = []
            fids = []
            for d, m, iid in zip(docs[0], metas[0], ids[0]):
                if m.get("source") == where["source"]:
                    filtered.append(d)
                    fmetas.append(m)
                    fids.append(iid)
            docs = [filtered]
            metas = [fmetas]
            ids = [fids]

        return {"documents": docs, "metadatas": metas, "ids": ids}

    def get(self, include=None) -> dict:
        if include and "metadatas" in include:
            return {"metadatas": self._metadatas}
        return {"metadatas": self._metadatas}

    def delete(self, where=None):
        if where and "source" in where:
            keep = [i for i, m in enumerate(self._metadatas) if m.get("source") != where["source"]]
            self._documents = [self._documents[i] for i in keep]
            self._metadatas = [self._metadatas[i] for i in keep]
            self._ids = [self._ids[i] for i in keep]
            self.index = None  # rebuild


# ═══════════════════════════════════════════════════════════════
# ChromaDB Backend (production, Docker)
# ═══════════════════════════════════════════════════════════════

COLLECTION_NAME = "rag_knowledge_base"
_chroma_client_instance = None
_chroma_collection_instance = None
_faiss_store = None


def _get_backend():
    """Return the active vector store backend."""
    global _faiss_store, _chroma_client_instance, _chroma_collection_instance

    if USE_FAISS or not _HAS_CHROMADB:
        if _faiss_store is None:
            _faiss_store = _FaissStore()
            logger.info("RAG: Using FAISS in-memory backend")
        return _faiss_store

    # ChromaDB backend
    if _chroma_collection_instance is None:
        try:
            # Resolve from CHROMA_URL, or CHROMA_HOST/CHROMA_PORT when the
            # deployment supplies the host/port pair (docker-compose does).
            from urllib.parse import urlparse

            parsed = urlparse(settings.chroma_endpoint)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8000
            _chroma_client_instance = chromadb.HttpClient(
                host=host, port=port,
                settings=Settings(anonymized_telemetry=False)
            )
            _chroma_collection_instance = _chroma_client_instance.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=_embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"RAG: Using ChromaDB backend at {host}:{port}")
        except Exception as e:
            logger.warning(f"ChromaDB connection failed ({e}), falling back to FAISS")
            if _faiss_store is None:
                _faiss_store = _FaissStore()
            return _faiss_store

    return _chroma_collection_instance


# ── Text Processing Helpers ───────────────────────────────────

ALLOWED_MIMES = {
    "application/pdf": "_read_pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "_read_docx",
    "text/plain": "decode",
    "text/markdown": "decode",
}


async def ingest_document(file: UploadFile):
    """Upload, chunk, embed, and index a document."""
    collection = _get_backend()
    filename = file.filename

    try:
        file_bytes = await file.read()
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(413, "File exceeds 5MB limit.")

        # Validate MIME
        try:
            import magic
            mime_type = magic.from_buffer(file_bytes, mime=True)
        except ImportError:
            ext = (filename or "").lower()
            mapping = {".pdf": "application/pdf", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       ".txt": "text/plain", ".md": "text/markdown"}
            mime_type = mapping.get(ext, "application/octet-stream")

        if mime_type not in ALLOWED_MIMES:
            raise HTTPException(415, f"Unsupported file type: {mime_type}")

        # Extract text
        content = _extract_text(file_bytes, mime_type)
        if not content.strip():
            raise HTTPException(400, "File is empty or text could not be extracted")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing {filename}: {e}")
        raise HTTPException(500, f"Failed to read file: {str(e)}")

    chunks = _chunk_text(content)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

    # Generate embeddings
    try:
        embeddings = _embedding_fn(chunks)
        # Encrypt at rest if key available
        try:
            from cryptography.fernet import Fernet
            key = getattr(settings, "RAG_ENCRYPTION_KEY", None)
            if key and len(key) > 10 and key != "FwD6i249jOhYhSDB8aXvA-c4e9A8H8bFzL1h9_N0lQo=":
                f = Fernet(key.encode() if isinstance(key, str) else key)
                documents = [f.encrypt(c.encode()).decode() for c in chunks]
            else:
                documents = chunks
        except Exception:
            documents = chunks

        collection.add(embeddings=embeddings, documents=documents, metadatas=metadatas, ids=ids)

    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(500, f"Failed to index document: {e}")

    # Clear cache
    try:
        keys = redis_client.keys("rag:cache:*")
        if keys:
            redis_client.delete(*keys)
    except Exception:
        pass

    return {"filename": filename, "chunks": len(chunks), "status": "indexed"}


def query_rag(query_text: str, n_results: int = 10, filename_filter: str = None) -> str:
    """Semantic search over indexed documents."""
    if not query_text or not query_text.strip():
        query_text = "What is this document about?"

    # Redis cache check
    cache_key = f"rag:cache:{hashlib.md5(f'{query_text}:{n_results}:{filename_filter}'.encode()).hexdigest()}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return cached
    except Exception:
        pass

    collection = _get_backend()

    query_params = {"query_texts": [query_text], "n_results": 20}
    if filename_filter:
        query_params["where"] = {"source": filename_filter}

    try:
        results = collection.query(**query_params)
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return ""

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]

    if not docs:
        return ""

    # Decrypt
    try:
        from cryptography.fernet import Fernet
        key = getattr(settings, "RAG_ENCRYPTION_KEY", None)
        if key and len(key) > 10 and key != "FwD6i249jOhYhSDB8aXvA-c4e9A8H8bFzL1h9_N0lQo=":
            f = Fernet(key.encode() if isinstance(key, str) else key)
            decrypted = []
            for d in docs:
                try:
                    decrypted.append(f.decrypt(d.encode()).decode())
                except Exception:
                    decrypted.append(d)
            docs = decrypted
    except Exception:
        pass

    # Rerank if available
    if settings.VOYAGE_API_KEY and settings.VOYAGE_RERANK_MODEL and settings.VOYAGE_API_KEY != "your_voyage_key_here":
        try:
            import httpx
            resp = httpx.post(
                "https://api.voyageai.com/v1/rerank",
                headers={"Authorization": f"Bearer {settings.VOYAGE_API_KEY}", "Content-Type": "application/json"},
                json={"query": query_text, "documents": docs, "model": settings.VOYAGE_RERANK_MODEL, "top_k": n_results},
                timeout=30,
            )
            if resp.status_code == 200:
                reranked = resp.json()["data"]
                docs = [docs[item["index"]] for item in reranked]
                metas = [metas[item["index"]] for item in reranked]
            else:
                docs = docs[:n_results]
                metas = metas[:n_results]
        except Exception:
            docs = docs[:n_results]
            metas = metas[:n_results]
    else:
        docs = docs[:n_results]
        metas = metas[:n_results]

    # Format context
    context = ""
    for i, doc in enumerate(docs):
        source = metas[i].get("source", "unknown") if i < len(metas) else "unknown"
        context += f"\n[Source: {source}]\n{doc}\n"

    # Cache
    try:
        redis_client.setex(cache_key, CACHE_TTL, context)
    except Exception:
        pass

    return context


# ── Helpers ───────────────────────────────────────────────────

def _extract_text(file_bytes: bytes, mime_type: str) -> str:
    if mime_type == "text/plain" or mime_type == "text/markdown":
        return file_bytes.decode("utf-8", errors="replace")
    if mime_type == "application/pdf":
        import pypdf
        pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in pdf.pages)
    if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    return file_bytes.decode("utf-8", errors="replace")


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Recursive character text splitter."""
    if not text:
        return []
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current += para + "\n\n"
        else:
            if current.strip():
                chunks.append(current.strip())
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i:i + chunk_size - overlap])
                current = ""
            else:
                current = para + "\n\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def list_documents() -> List[str]:
    """List all unique document sources."""
    collection = _get_backend()
    try:
        result = collection.get(include=["metadatas"])
        metas = result.get("metadatas", [])
        sources = set()
        for m in metas:
            if m and "source" in m:
                sources.add(m["source"])
        return sorted(sources)
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return []


def delete_document(filename: str) -> bool:
    """Delete all chunks for a specific file."""
    collection = _get_backend()
    try:
        collection.delete(where={"source": filename})
        return True
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(500, f"Failed to delete document: {e}")

def purge_old_research(months_old: int = 6) -> int:
    """Deletes deep research data older than the specified number of months."""
    import time
    
    collection = _get_backend()
    
    # Check if we fell back to FAISS (which doesn't support metadata deletion natively via the same API)
    if isinstance(collection, _FaissStore):
        logger.info("Auto-TTL purge not supported for FAISS backend.")
        return 0
    
    # Calculate timestamp threshold
    seconds_in_month = 30 * 24 * 60 * 60
    threshold_ts = int(time.time()) - (months_old * seconds_in_month)
    
    try:
        # ChromaDB syntax for metadata filtering
        # We target items from deep_research that have a timestamp older than threshold
        where_filter = {
            "$and": [
                {"source": "deep_research"},
                {"timestamp": {"$lt": threshold_ts}}
            ]
        }
        
        # In Chroma, delete() doesn't return the count directly, so we can do a get() to see how many match
        matching = collection.get(where=where_filter, include=["metadatas"])
        count = len(matching["ids"]) if matching and "ids" in matching else 0
        
        if count > 0:
            collection.delete(where=where_filter)
            logger.info(f"Auto-TTL: Purged {count} expired deep research items older than {months_old} months.")
        else:
            logger.info("Auto-TTL: No expired deep research items found.")
            
        return count
    except Exception as e:
        logger.error(f"Auto-TTL purge error: {e}")
        return 0
