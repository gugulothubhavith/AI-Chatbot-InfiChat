"""Deep Research API — SSE streaming endpoint."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.concurrency import deep_research_limiter, limit_concurrency
from app.core.deps import require_consent, get_db
from app.core.sse import END_OF_STREAM, SSE_HEADERS, sse_frame, sse_stream
from app.database.db import SessionLocal
from sqlalchemy.orm import Session
from app.models.chat import ChatMessage, ChatSession
from app.services.deep_research.orchestrator import run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    model: str | None = None


@router.post("/research/stream", dependencies=[Depends(limit_concurrency(deep_research_limiter))])
def stream_research(request: ResearchRequest, user=Depends(require_consent), db: Session = Depends(get_db)):
    """
    Stream a deep research pipeline via Server-Sent Events.

    A user may have only one run in flight at a time — the pipeline holds
    several key-pool leases for minutes, so an unbounded fan-out from one
    account starves everyone else. Exceeding it is a 429 before the stream
    opens, not a stalled connection.

    The client receives events in the format:
        data: {"type": "agent_status", "agent": "IntentAnalysis", "status": "running", ...}
    
    Event types:
        - agent_status: Agent started/completed/errored
        - plan: Research plan tree
        - source_found: New source discovered
        - quality_gate: Critic quality check results
        - report: Final research report
        - done: Pipeline complete
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Read the ORM attribute we need up front: a plain value is what's safe to
    # close over from the background coroutine and hand to a worker thread.
    user_id = user.id

    # Only adopt a caller-supplied conversation id after confirming this user
    # owns it. Without the ownership filter, any caller could pass someone
    # else's session id and have their prompt and the resulting report written
    # into that stranger's conversation. Falling back to a fresh session (rather
    # than erroring) both fixes the write and keeps the response from revealing
    # whether the id exists.
    session_id = request.conversation_id
    if session_id:
        owned = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        ).first()
        if not owned:
            logger.warning(
                "Research: user %s supplied a conversation id they do not own; "
                "starting a new session instead.", user_id
            )
            session_id = None

    if not session_id:
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
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
        logger.error(f"Error saving research prompt: {e}")

    def _save_report(report_content: str) -> None:
        """Persist the finished report on its own short-lived Session.

        Runs in a worker thread. This used to commit directly inside the
        background coroutine, which froze the event loop — and so every other
        live request and SSE stream — for the duration of the write. Opening the
        Session here rather than for the life of the pipeline also stops a
        pooled connection being pinned for the minutes a run can take.
        """
        thread_db = SessionLocal()
        try:
            thread_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=report_content,
                model="deep-research",
            ))
            thread_db.commit()
        finally:
            thread_db.close()

    async def background_research(queue: asyncio.Queue) -> None:
        try:
            from app.core.config import settings
            model_to_use = request.model or getattr(settings, "DEEP_RESEARCH_DEFAULT_MODEL", "nvidia/nemotron-3-ultra-550b-a55b")
            async for event in run_pipeline(request.query.strip(), model=model_to_use):
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
                                    report_content += "\n\n---\n" + cit_str

                                await asyncio.to_thread(_save_report, report_content)
                    except Exception as inner_e:
                        logger.error(f"Failed to save deep research report: {inner_e}")

                await queue.put(event)
        except asyncio.CancelledError:
            # Client went away; unwind quietly so `finally` sends END_OF_STREAM.
            raise
        except Exception:
            # Log the detail server-side and hand the client a generic frame so
            # nothing internal leaks into the stream.
            logger.exception("Deep research stream failed")
            await queue.put(sse_frame({
                "type": "error",
                "message": "Deep research failed. Please try again.",
            }))
        finally:
            await queue.put(END_OF_STREAM)

    return StreamingResponse(
        sse_stream(background_research, label=f"deep-research[{session_id}]"),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, "X-Chat-Session-ID": str(session_id)},
    )
