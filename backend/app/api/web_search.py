"""Web Search API — Fast SSE streaming endpoint."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.deps import get_current_user, get_db
from sqlalchemy.orm import Session
from app.models.chat import ChatMessage, ChatSession
from app.services.web_search.orchestrator import run_web_search

logger = logging.getLogger(__name__)

router = APIRouter()


def _sse(payload: dict) -> str:
    """Serialise an SSE data frame safely.

    Hand-building JSON with f-strings let raw exception text (quotes, newlines)
    break the frame and leak internals to the client. json.dumps escapes it.
    """
    return f"data: {json.dumps(payload)}\n\n"


class WebSearchRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    model: str | None = None


@router.post("/web_search/stream")
async def stream_web_search(request: WebSearchRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Stream a fast web search pipeline via Server-Sent Events.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    session_id = request.conversation_id
    if not session_id:
        import uuid
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=request.query[:50]
        )
        db.add(new_session)
        session_id = new_session.id
        db.commit()

    try:
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.query.strip()
        )
        db.add(user_msg)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving web search prompt: {e}")

    from app.database.db import SessionLocal
    queue = asyncio.Queue()

    async def background_search():
        bg_db = None
        try:
            bg_db = SessionLocal()
            from app.core.config import settings
            model_to_use = request.model or getattr(settings, "WEB_SEARCH_MODEL", "nvidia/llama-3_3-nemotron-super-49b-v1_5")

            async for event in run_web_search(request.query.strip(), model=model_to_use):
                if event.startswith("data: "):
                    try:
                        data_str = event[6:].strip()
                        if data_str:
                            data = json.loads(data_str)
                            if data.get("type") == "report":
                                report_content = data.get("content", "")
                                citations = data.get("citations", [])
                                if citations:
                                    cit_str = "\n".join([f"[{c.get('index')}] [{c.get('title')}]({c.get('url')})" for c in citations])
                                    report_content += "\n\n---\n**Sources:**\n" + cit_str

                                asst_msg = ChatMessage(
                                    session_id=session_id,
                                    role="assistant",
                                    content=report_content,
                                    model="web-search"
                                )
                                bg_db.add(asst_msg)
                                bg_db.commit()
                    except Exception as inner_e:
                        bg_db.rollback()
                        logger.error(f"Failed to save web search report: {inner_e}")

                await queue.put(event)

        except Exception as e:
            # Log the detail server-side; send the client a generic, correctly
            # escaped error frame so nothing internal leaks into the stream.
            logger.exception("Web search stream failed")
            await queue.put(_sse({"type": "error", "message": "Web search failed. Please try again."}))
        finally:
            if bg_db:
                bg_db.close()
            await queue.put(None)  # Sentinel value to stop generator

    async def event_generator():
        task = asyncio.create_task(background_search())
        while True:
            event = await queue.get()
            if event is None:
                break
            yield event
        await task

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
