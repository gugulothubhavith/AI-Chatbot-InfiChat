"""Web Search API — Fast SSE streaming endpoint."""

import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.deps import get_current_user
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
async def stream_web_search(request: WebSearchRequest, user=Depends(get_current_user)):
    """
    Stream a fast web search pipeline via Server-Sent Events.

    Takes no ``db``: every database touch runs in a worker thread on its own
    short-lived Session. This coroutine is the head of an SSE stream, so a
    blocking commit here stalls every other in-flight request for its duration.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Read the ORM attribute we need before any commit. expire_on_commit=True is
    # the default, so a post-commit ``user.id`` would emit a lazy-load SELECT on
    # the event loop. A plain value is also what's safe to hand to a thread.
    user_id = user.id
    query = request.query.strip()

    from app.database.db import SessionLocal

    def _ensure_session_and_save_prompt(session_id_arg):
        """Create-or-verify the session, then record the prompt.

        Returns the session id as a plain string — never an ORM instance, which
        would be bound to the Session this thread is about to close.

        Only adopts a caller-supplied conversation id after confirming this user
        owns it. Without the ownership filter, any caller could pass someone
        else's session id and have their prompt and the resulting report written
        into that stranger's conversation. Falling back to a fresh session
        (rather than erroring) both fixes the write and keeps the response from
        revealing whether the id exists.
        """
        thread_db = SessionLocal()
        try:
            resolved = session_id_arg
            if resolved:
                owned = thread_db.query(ChatSession).filter(
                    ChatSession.id == resolved,
                    ChatSession.user_id == user_id,
                ).first()
                if not owned:
                    logger.warning(
                        "Web search: user %s supplied a conversation id they do "
                        "not own; starting a new session instead.", user_id
                    )
                    resolved = None

            if not resolved:
                import uuid
                new_session = ChatSession(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    title=query[:50],
                )
                thread_db.add(new_session)
                thread_db.commit()
                thread_db.refresh(new_session)
                resolved = str(new_session.id)

            # A failed prompt save must not kill the stream, matching the
            # original behaviour: log it and carry on with the search.
            try:
                thread_db.add(ChatMessage(
                    session_id=resolved,
                    role="user",
                    content=query,
                ))
                thread_db.commit()
            except Exception as e:
                thread_db.rollback()
                logger.error(f"Error saving web search prompt: {e}")

            return resolved
        finally:
            thread_db.close()

    session_id = await asyncio.to_thread(
        _ensure_session_and_save_prompt, request.conversation_id
    )

    def _save_report(report_content: str) -> None:
        """Persist the finished report on its own short-lived Session.

        Runs in a worker thread. This used to commit directly inside the
        background coroutine, which froze the event loop — and so every other
        live request and SSE stream — for the duration of the write.
        """
        thread_db = SessionLocal()
        try:
            thread_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=report_content,
                model="web-search",
            ))
            thread_db.commit()
        finally:
            thread_db.close()

    queue = asyncio.Queue()

    async def background_search():
        try:
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

                                await asyncio.to_thread(_save_report, report_content)
                    except Exception as inner_e:
                        logger.error(f"Failed to save web search report: {inner_e}")

                await queue.put(event)

        except Exception as e:
            # Log the detail server-side; send the client a generic, correctly
            # escaped error frame so nothing internal leaks into the stream.
            logger.exception("Web search stream failed")
            await queue.put(_sse({"type": "error", "message": "Web search failed. Please try again."}))
        finally:
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
