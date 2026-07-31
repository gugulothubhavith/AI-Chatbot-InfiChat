"""Deep Thinking API — SSE streaming endpoint for chain-of-thought reasoning."""

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
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
    db: Session = Depends(get_db),
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
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Create or use existing session
    session_id = request.conversation_id
    if not session_id:
        new_session = ChatSession(
            id=str(uuid.uuid4()),
            user_id=user.id,
            title=request.query[:50],
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = str(new_session.id)
    else:
        # Verify session ownership
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        ).first()
        if not session:
            # Create a new one if session doesn't exist
            import uuid
            new_session = ChatSession(
                id=str(uuid.uuid4()),
                user_id=user.id,
                title=request.query[:50],
            )
            db.add(new_session)
            db.commit()
            db.refresh(new_session)
            session_id = str(new_session.id)

    # Save user message
    try:
        user_msg = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.query.strip(),
            model="deep-thinking",
        )
        db.add(user_msg)
        db.commit()
    except Exception as e:
        db.rollback()
        logger = __import__("logging").getLogger(__name__)
        logger.error(f"Error saving thinking prompt: {e}")

    import asyncio
    from app.database.db import SessionLocal
    queue = asyncio.Queue()

    async def background_thinking():
        bg_db = None
        try:
            bg_db = SessionLocal()
            model_to_use = request.model or None
            async for event in run_thinking_pipeline(
                request.query.strip(), model=model_to_use
            ):
                if event.startswith("data: "):
                    try:
                        import json
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

                                # Save to database
                                asst_msg = ChatMessage(
                                    session_id=session_id,
                                    role="assistant",
                                    content=report_content,
                                    model="deep-thinking",
                                )
                                bg_db.add(asst_msg)
                                bg_db.commit()
                    except Exception as inner_e:
                        import logging
                        logging.getLogger(__name__).error(
                            f"Failed to save deep thinking report: {inner_e}"
                        )
                        bg_db.rollback()
                await queue.put(event)
            await queue.put(None)
        except Exception as e:
            import json
            logger = __import__("logging").getLogger(__name__)
            logger.error(f"Deep thinking stream error: {e}")
            await queue.put(f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n")
            await queue.put(None)
        finally:
            if bg_db:
                bg_db.close()

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
