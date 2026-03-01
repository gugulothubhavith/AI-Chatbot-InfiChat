from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from app.core.deps import get_current_user
from app.models.user import User
from app.services.rag_service import ingest_document, query_rag

router = APIRouter(prefix="/rag", tags=["RAG"])

from fastapi import Form
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models.chat import ChatMessage, ChatSession

@router.post("/upload")
async def rag_upload(
    file: UploadFile = File(...),
    conversation_id: str = Form(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(f"RAG Upload Request: {file.filename} (user: {user.email})")
    res = await ingest_document(file)
    
    return res

@router.post("/query")
def rag_query(
    payload: dict,
    user: User = Depends(get_current_user)
):
    query_text = payload.get("query")
    n_results = payload.get("n_results", 5)
    
    # We want raw chunks for the RAG testing page
    from app.services.rag_service import get_chroma_client
    collection = get_chroma_client()
    results = collection.query(query_texts=[query_text], n_results=n_results)
    
    return {"results": results['documents'][0]}

@router.get("/documents")
def get_documents(user: User = Depends(get_current_user)):
    from app.services.rag_service import list_documents
    return {"documents": list_documents()}

@router.delete("/documents/{filename}")
def delete_document_endpoint(filename: str, user: User = Depends(get_current_user)):
    from app.services.rag_service import delete_document
    delete_document(filename)
    return {"status": "deleted", "filename": filename}