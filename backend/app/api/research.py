"""Deep Research API — SSE streaming endpoint."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.concurrency import deep_research_limiter, limit_concurrency
from app.core.deps import get_current_user, get_db
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
def stream_research(request: ResearchRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
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

    session_id = request.conversation_id
    if not session_id:
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
        logger.error(f"Error saving research prompt: {e}")

    async def background_research(queue: asyncio.Queue) -> None:
        bg_db = None
        try:
            bg_db = SessionLocal()
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
                                
                                asst_msg = ChatMessage(
                                    session_id=session_id,
                                    role="assistant",
                                    content=report_content,
                                    model="deep-research"
                                )
                                bg_db.add(asst_msg)
                                bg_db.commit()
                    except Exception as inner_e:
                        bg_db.rollback()
                        logger.error(f"Failed to save deep research report: {inner_e}")

                await queue.put(event)
        except asyncio.CancelledError:
            # Client went away; unwind quietly so `finally` closes the session.
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
            if bg_db:
                bg_db.close()
            await queue.put(END_OF_STREAM)

    return StreamingResponse(
        sse_stream(background_research, label=f"deep-research[{session_id}]"),
        media_type="text/event-stream",
        headers={**SSE_HEADERS, "X-Chat-Session-ID": str(session_id)},
    )
