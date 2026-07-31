"""Deep Thinking API — SSE streaming endpoint for chain-of-thought reasoning."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.core.sse import END_OF_STREAM, SSE_HEADERS, sse_frame, sse_stream
from app.database.db import SessionLocal
from app.models.user import User
from app.models.chat import ChatMessage, ChatSession
from app.services.deep_thinking.orchestrator import run_thinking_pipeline

logger = logging.getLogger(__name__)

router = APIRouter()


class ThinkingRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    model: str | None = None


@router.post("/thinking/stream")
async def stream_thinking(
    request: ThinkingRequest,
    user: User = Depends(get_current_user),
):
    """
    Stream a deep thinking pipeline via Server-Sent Events.

    The client receives events in the format:
        data: {"type": "thinking_progress", "stage": "analyzing", ...}

    Event types:
        - thinking_progress: Current stage and progress info
        - reasoning_step: Each reasoning step as generated
        - thinking_complete: Final report with full reasoning chain
        - error: Error message
        - done: Pipeline complete

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

    def _ensure_session_and_save_prompt(session_id_arg):
        """Create-or-verify the session, then record the prompt.

        Returns the session id as a plain string — never an ORM instance, which
        would be bound to the Session this thread is about to close.

        Preserves the original fallback: an unknown or unowned session id yields
        a brand-new session rather than an error. The ownership filter means a
        caller passing someone else's id simply gets their own new session, so
        this leaks nothing.
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
                    resolved = None

            if not resolved:
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
            # original behaviour: log it and carry on with the pipeline.
            try:
                thread_db.add(ChatMessage(
                    session_id=resolved,
                    role="user",
                    content=query,
                    model="deep-thinking",
                ))
                thread_db.commit()
            except Exception as e:
                thread_db.rollback()
                logger.error(f"Error saving thinking prompt: {e}")

            return resolved
        finally:
            thread_db.close()

    session_id = await asyncio.to_thread(
        _ensure_session_and_save_prompt, request.conversation_id
    )

    queue = asyncio.Queue()

    def _save_report(report_content):
        """Persist the finished report on its own short-lived Session.

        Runs in a worker thread: this used to commit directly inside the
        create_task coroutine, which froze the loop — and therefore every other
        live request and SSE stream — for the duration of the write.
        """
        thread_db = SessionLocal()
        try:
            thread_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=report_content,
                model="deep-thinking",
            ))
            thread_db.commit()
        finally:
            thread_db.close()

    async def background_thinking():
        try:
            model_to_use = request.model or None
            async for event in run_thinking_pipeline(
                request.query.strip(), model=model_to_use
            ):
                if event.startswith("data: "):
                    try:
                        data_str = event[6:].strip()
                        if data_str:
                            data = json.loads(data_str)
                            if data.get("type") == "thinking_complete":
                                report = data.get("report", {})
                                executive_summary = report.get("executive_summary", "")
                                conclusion = report.get("conclusion", "")
                                key_findings = report.get("key_findings", [])

                                # Build a rich markdown report
                                report_content = f"# Deep Thinking Analysis\n\n"
                                report_content += f"## Executive Summary\n\n{executive_summary}\n\n"

                                if key_findings:
                                    report_content += "## Key Findings\n\n"
                                    for f in key_findings:
                                        report_content += f"- {f}\n"
                                    report_content += "\n"

                                report_content += f"## Conclusion\n\n{conclusion}\n\n"

                                reasoning_chain = report.get("reasoning_chain", [])
                                if reasoning_chain:
                                    report_content += "## Reasoning Process\n\n"
                                    for step in reasoning_chain:
                                        status_icon = "✅" if step.get("status") == "verified" else "⚠️"
                                        report_content += f"### {status_icon} Step {step.get('step_number')}: {step.get('title', '')}\n\n"
                                        report_content += f"{step.get('content', '')}\n\n"
                                        conf = step.get("confidence", 0)
                                        report_content += f"> Confidence: {conf:.0%}\n\n"

                                confidence = report.get("confidence_score", 0)
                                caveats = report.get("caveats", [])
                                report_content += f"---\n\n**Overall Confidence:** {confidence:.0%}\n\n"
                                if caveats:
                                    report_content += "**Caveats:**\n\n"
                                    for c in caveats:
                                        report_content += f"- {c}\n"

                                # Persist the finished report off-loop.
                                await asyncio.to_thread(_save_report, report_content)
                    except Exception as inner_e:
                        logger.error(
                            f"Failed to save deep thinking report: {inner_e}"
                        )
                await queue.put(event)
            await queue.put(None)
        except Exception as e:
            logger.error(f"Deep thinking stream error: {e}")
            await queue.put(f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
            await queue.put(None)

    asyncio.create_task(background_thinking())

    async def event_stream():
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event
        except asyncio.CancelledError:
            print(f"Client disconnected for session {session_id}, deep thinking continues in background.")
            raise

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Chat-Session-ID": str(session_id),
        },
    )
