from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, SharedChat
from app.schemas.chat import ChatRequest, ChatResponse, ChatSessionSchema, ChatSessionUpdate, ChatExport
from app.services.chat_service import process_chat, delete_user_chat_history, export_user_chat_history
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.get("/sessions", response_model=List[ChatSessionSchema])
async def list_sessions(
    workspace: Optional[str] = Query("personal"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.workspace == workspace
    ).order_by(ChatSession.is_pinned.desc(), ChatSession.updated_at.desc()).all()
    return sessions

@router.post("/sessions", response_model=ChatSessionSchema)
async def create_session(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_session = ChatSession(user_id=user.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.patch("/sessions/{session_id}", response_model=ChatSessionSchema)
async def update_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if update_data.title is not None: session.title = update_data.title
    if update_data.is_pinned is not None: session.is_pinned = update_data.is_pinned
    if update_data.is_archived is not None: session.is_archived = update_data.is_archived
    
    db.commit()
    db.refresh(session)
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Cascade delete shared_chats references first to avoid FK violations
    from sqlalchemy import text
    db.execute(text("DELETE FROM shared_chats WHERE session_id = :sid"), {"sid": session_id})
    
    db.delete(session)
    db.commit()
    return {"status": "deleted"}

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages

@router.get("/search")
async def search_chats(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Search in session titles and message content
    results = db.query(ChatSession).join(ChatMessage).filter(
        ChatSession.user_id == user.id,
        (ChatSession.title.ilike(f"%{q}%")) | (ChatMessage.content.ilike(f"%{q}%"))
    ).distinct().all()
    
    return [ChatSessionSchema.from_orm(s) for s in results]

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    from app.services.chat_service import process_chat
    response, session_id = await process_chat(payload, user, db)
    # Wrap in JSONResponse to add custom header
    from fastapi.responses import JSONResponse
    from fastapi.encoders import jsonable_encoder
    return JSONResponse(
        content=jsonable_encoder(response),
        headers={"X-Chat-Session-ID": str(session_id)}
    )

@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        # Assuming process_chat is modified to return a tuple: (async_generator, session_id)
        generator, session_id = await process_chat(payload, user, db, stream=True)

        async def event_generator_wrapper():
            async for chunk in generator:
                # Use JSON to safely transport chunks that might contain newlines
                try:
                    data = json.dumps({"content": chunk})
                    yield f"data: {data}\n\n"
                except:
                    yield f"data: {str(chunk)}\n\n"
        
        return StreamingResponse(
            event_generator_wrapper(),
            media_type="text/event-stream",
            headers={"X-Chat-Session-ID": str(session_id)}
        )
    except ValueError as e:
        # Handle specific session/auth errors with 400-level codes
        error_msg = str(e)
        if "Unauthorized" in error_msg:
            status_code = 403
        elif "not found" in error_msg:
            status_code = 404
        else:
            status_code = 400
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=status_code, content={"detail": error_msg})
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"CHAT CRITICAL ERROR: {e}\n{error_trace}") # Print to console too
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"detail": str(e), "traceback": error_trace}
        )

@router.delete("/history")
async def delete_all_history(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    delete_user_chat_history(user.id, db)
    return {"status": "success", "message": "All chat history deleted"}

@router.get("/export")
async def export_data(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    data = export_user_chat_history(user.id, db)
    return data

@router.post("/sessions/{session_id}/share")
async def share_session(
    session_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if already shared
    existing_share = db.query(SharedChat).filter(SharedChat.session_id == session_id).first()
    if existing_share:
        return {"share_token": existing_share.share_token}

    # Create snapshot
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    snapshot = [
        {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in messages
    ]
    
    shared = SharedChat(
        session_id=session.id,
        snapshot_json=snapshot
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)
    
    return {"share_token": shared.share_token}

@router.get("/shared")
async def list_shared_chats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all chats shared by the user."""
    shared = db.query(SharedChat).join(ChatSession).filter(ChatSession.user_id == user.id).all()
    return [
        {
            "token": s.share_token,
            "title": s.session.title,
            "created_at": s.created_at.isoformat(),
            "session_id": str(s.session_id)
        }
        for s in shared
    ]

@router.delete("/shared/{token}")
async def unshare_chat(
    token: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Remove a shared link."""
    shared = db.query(SharedChat).join(ChatSession).filter(
        SharedChat.share_token == token,
        ChatSession.user_id == user.id
    ).first()
    
    if not shared:
        raise HTTPException(status_code=404, detail="Shared link not found")
        
    db.delete(shared)
    db.commit()
    return {"status": "success"}

@router.get("/archived")
async def list_archived_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """List all archived sessions."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user.id,
        ChatSession.is_archived == True
    ).order_by(ChatSession.updated_at.desc()).all()
    return sessions

@router.get("/shared/{token}")
async def get_shared_chat(
    token: str,
    db: Session = Depends(get_db)
):
    shared = db.query(SharedChat).filter(SharedChat.share_token == token).first()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared chat not found")
    
    session = db.query(ChatSession).filter(ChatSession.id == shared.session_id).first()
    
    return {
        "title": session.title if session else "Shared Chat",
        "messages": shared.snapshot_json,
        "created_at": shared.created_at.isoformat()
    }