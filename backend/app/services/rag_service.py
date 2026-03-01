import os
import uuid
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from fastapi import UploadFile, HTTPException
import pypdf
import docx
import io
import httpx
import json
import redis
import hashlib
from app.core.config import settings

logger = logging.getLogger(__name__)

from app.core.redis_client import redis_client
CACHE_TTL = 3600  # 1 hour

CHROMA_HOST = os.getenv("CHROMA_URL", "http://chromadb:8000")
COLLECTION_NAME = "rag_knowledge_base"

class VoyageEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.url = "https://api.voyageai.com/v1/embeddings"

    def __call__(self, input: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": input,
            "model": self.model_name
        }
        
        # Using synchronous request here because ChromaDB's EmbeddingFunction is synchronous
        with httpx.Client(timeout=60.0) as client:
            try:
                response = client.post(self.url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]
            except Exception as e:
                logger.error(f"Voyage AI Embedding Failed: {e}")
                # Return zero embeddings as fallback or raise? Chroma expects embeddings.
                raise HTTPException(status_code=502, detail=f"Voyage AI Error: {str(e)}")

# Global Client & Collection
_client = None
_collection = None
_embedding_fn = None

def get_chroma_client():
    global _client, _collection, _embedding_fn
    
    if _client is None:
        try:
            logger.info(f"Connecting to ChromaDB at {CHROMA_HOST}...")
            # Parse host/port from URL if necessary, but HttpClient takes host/port
            # Assuming CHROMA_URL is "http://chromadb:8000"
            host_url = CHROMA_HOST.replace("http://", "").split(":")
            host = host_url[0]
            port = int(host_url[1]) if len(host_url) > 1 else 8000
            
            _client = chromadb.HttpClient(host=host, port=port)
            
            logger.info(f"Using Voyage AI embedding model: {settings.VOYAGE_EMBEDDING_MODEL}")
            _embedding_fn = VoyageEmbeddingFunction(
                api_key=settings.VOYAGE_API_KEY,
                model_name=settings.VOYAGE_EMBEDDING_MODEL
            )
            
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=_embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("RAG Service Initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise e
            
    return _collection

async def ingest_document(file: UploadFile):
    collection = get_chroma_client()
    
    filename = file.filename
    content = ""
    
    # 1. Extract Text
    try:
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext == "pdf":
            content = _read_pdf(await file.read())
        elif ext == "docx":
            content = _read_docx(await file.read())
        elif ext in ["txt", "md"]:
            content = (await file.read()).decode("utf-8")
        else:
            raise HTTPException(400, f"Unsupported file type: {ext}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise HTTPException(500, f"Failed to read file: {str(e)}")

    if not content.strip():
        raise HTTPException(400, "File is empty or could not extract text")

    # 2. Chunk Text
    chunks = _chunk_text(content)
    logger.info(f"Extracted {len(chunks)} chunks from {filename}")

    # 3. Embed & Store
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]
    
    try:
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
    except Exception as e:
        logger.error(f"Chroma add error: {e}")
        raise HTTPException(500, f"Failed to index document: {e}")

    # 4. Clear Cache
    try:
        # Simple invalidation: clear all RAG cache on document update
        # For production, we might use granular tags/prefixes
        keys = redis_client.keys("rag:cache:*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Cleared {len(keys)} RAG cache entries.")
    except Exception as e:
        logger.warning(f"Failed to clear RAG cache: {e}")

    return {"filename": filename, "chunks": len(chunks), "status": "indexed"}

def query_rag(query_text: str, n_results: int = 10, filename_filter: str = None): 
    # Use fallback query if empty
    if not query_text or not query_text.strip():
        query_text = "What is this document about?"

    # --- REDIS CACHE CHECK ---
    cache_string = f'{query_text}:{n_results}'
    if filename_filter:
        cache_string += f':{filename_filter}'
    cache_key = f"rag:cache:{hashlib.md5(cache_string.encode()).hexdigest()}"
    try:
        cached_context = redis_client.get(cache_key)
        if cached_context:
            logger.info(f"RAG Cache Hit: {cache_key}")
            return cached_context
    except Exception as e:
        logger.warning(f"Redis cache check failed: {e}")

    collection = get_chroma_client()
    
    # 1. Initial Retrieval
    query_params = {
        "query_texts": [query_text],
        "n_results": 20
    }
    if filename_filter:
        query_params["where"] = {"source": filename_filter}

    results = collection.query(**query_params)
    
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    
    if not docs:
        return ""
        
    # 2. Reranking using Voyage AI
    if settings.VOYAGE_API_KEY and settings.VOYAGE_RERANK_MODEL:
        try:
            logger.info(f"Reranking results with {settings.VOYAGE_RERANK_MODEL}...")
            url = "https://api.voyageai.com/v1/rerank"
            headers = {
                "Authorization": f"Bearer {settings.VOYAGE_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "query": query_text,
                "documents": docs,
                "model": settings.VOYAGE_RERANK_MODEL,
                "top_k": n_results
            }
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                resp.raise_for_status()
                reranked_data = resp.json()["data"]
                
                # Re-sort docs and metas based on reranked indices
                new_docs = []
                new_metas = []
                for item in reranked_data:
                    idx = item["index"]
                    new_docs.append(docs[idx])
                    new_metas.append(metas[idx])
                docs, metas = new_docs, new_metas
        except Exception as e:
            logger.error(f"Reranking failed: {e}. Falling back to initial results.")
            # Fall back to first n_results
            docs = docs[:n_results]
            metas = metas[:n_results]
    else:
        # No reranker, just take top results
        docs = docs[:n_results]
        metas = metas[:n_results]
    
    # 3. Format Context
    context = ""
    for i, doc in enumerate(docs):
        source = metas[i].get('source', 'unknown')
        context += f"\n[Source: {source}]\n{doc}\n"
    
    # --- REDIS CACHE SET ---
    try:
        redis_client.setex(cache_key, CACHE_TTL, context)
        logger.info(f"RAG Cache Set: {cache_key}")
    except Exception as e:
        logger.warning(f"Redis cache set failed: {e}")
        
    return context

# Helpers
def _read_pdf(file_bytes):
    pdf = pypdf.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def _read_docx(file_bytes):
    doc = docx.Document(io.BytesIO(file_bytes))
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def _chunk_text(text, chunk_size=1000, overlap=200):
    """
    Recursive character text splitter logic.
    Prioritizes splitting by: Paragraphs (\n\n) -> Sentences (\n) -> Punctuation (.) -> Space ( )
    """
    if not text:
        return []
        
    separators = ["\n\n", "\n", ". ", " "]
    chunks = []
    start = 0
    text_len = len(text)
    
    # Simple recursive-like approach using the separators
    # For now, just a robust paragraph-aware splitter to keep it simple but effective
    import re
    
    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    current_chunk = ""
    
    for para in paragraphs:
        # If paragraph fits, add it
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            # Paragraph is too big or current chunk is full
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            # If paragraph itself is larger than chunk_size, split by newlines
            if len(para) > chunk_size:
                sub_lines = para.split("\n")
                sub_chunk = ""
                for line in sub_lines:
                    if len(sub_chunk) + len(line) + 1 <= chunk_size:
                        sub_chunk += line + "\n"
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk.strip())
                        # If line is still too huge, hard split
                        if len(line) > chunk_size:
                            for i in range(0, len(line), chunk_size - overlap):
                                chunks.append(line[i:i + chunk_size])
                            sub_chunk = ""
                        else:
                            sub_chunk = line + "\n"
                if sub_chunk:
                    current_chunk = sub_chunk
            else:
                current_chunk = para + "\n\n"
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def list_documents():
    """List all unique documents in the store."""
    collection = get_chroma_client()
    # Chroma doesn't have a direct "list distinct metadata" efficiently yet for large datasets,
    # but for this scale using get() is fine.
    # Fetch all metadata
    try:
        # Limit to reasonable amount or paginate in future. 
        # For now, fetching first 1000 items' metadata to extract sources.
        # Ideally we maintain a separate 'documents' table in SQL for this.
        # But to be self-contained in RAG service:
        result = collection.get(include=["metadatas"])
        metas = result['metadatas']
        
        sources = set()
        for m in metas:
            if m and 'source' in m:
                sources.add(m['source'])
                
        return sorted(list(sources))
    except Exception as e:
        logger.error(f"List documents error: {e}")
        return []

def delete_document(filename: str):
    """Delete all chunks for a specific file."""
    collection = get_chroma_client()
    try:
        collection.delete(
            where={"source": filename}
        )
        return True
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(500, f"Failed to delete document: {e}")