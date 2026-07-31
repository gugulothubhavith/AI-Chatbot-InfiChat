from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import logging
import json
from app.core.auth import decode_token
from app.database.db import SessionLocal
from app.services.agent_service import run_orchestration
from app.services.code_orchestrator.orchestrator import run_coding_pipeline
from typing import Optional
from app.models.chat import ChatMessage, ChatSession

router = APIRouter(prefix="/ws", tags=["WebSocket"])
logger = logging.getLogger(__name__)

@router.websocket("/code/squad")
async def websocket_code_squad(
    websocket: WebSocket,
    session_id: Optional[str] = None,
    token: Optional[str] = None,
):
    """Run the code squad pipeline over a WebSocket.

    Takes no ``db``: the history write runs in a worker thread on its own
    short-lived Session, so it never blocks the event loop.
    """
    await websocket.accept()

    # The ``token`` query parameter was accepted but never verified, leaving this
    # endpoint open to anyone who could reach it — it drives an LLM pipeline and
    # writes chat history. The frontend already sends ?token=<jwt> (see
    # api.connectWS), so validating it here matches the existing client.
    if not token:
        await websocket.send_text(json.dumps({
            "type": "error", "message": "Authentication required"
        }))
        await websocket.close(1008)
        return

    try:
        payload = decode_token(token)
    except Exception as e:
        logger.warning(f"Code Squad auth failed: {e}")
        payload = None

    if not payload:
        await websocket.send_text(json.dumps({
            "type": "error", "message": "Invalid or expired token"
        }))
        await websocket.close(1008)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.send_text(json.dumps({
            "type": "error", "message": "Invalid or expired token"
        }))
        await websocket.close(1008)
        return

    logger.info(f"Code Squad WebSocket connected (user_id: {user_id}, session_id: {session_id})")

    write_lock = asyncio.Lock()

    try:
        data = await websocket.receive_json()
        prompt = data.get("prompt")

        if not prompt:
            async with write_lock:
                await websocket.send_text(json.dumps({"type": "error", "message": "No prompt provided"}))
            await websocket.close()
            return

        collected_raw = ""

        async for event in run_coding_pipeline(prompt):
            if not event.startswith("data: "):
                continue

            data_str = event[6:].strip()
            if not data_str:
                continue

            try:
                # We simply forward the JSON from the coding pipeline straight to the frontend
                # It contains "agent_status", "code_generated", "report", etc.
                parsed_data = json.loads(data_str)

                if parsed_data.get("type") == "code_chunk":
                    collected_raw += parsed_data.get("chunk", "")

                async with write_lock:
                    await websocket.send_text(json.dumps(parsed_data))
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Failed to forward update: {e}")

        # Persist the complete code history if a session was supplied. Runs in a
        # worker thread: this write was synchronous inside the ``async def``, so
        # inline it froze the event loop — and every other request with it —
        # for the duration of the commit.
        if session_id and collected_raw:
            def _save_history():
                thread_db = SessionLocal()
                try:
                    # Only adopt the session if the caller owns it. Without the
                    # filter, an attacker could pass someone else's session_id and
                    # inject their prompt and output into that stranger's history.
                    owned = thread_db.query(ChatSession).filter(
                        ChatSession.id == session_id,
                        ChatSession.user_id == user_id,
                    ).first()

                    if not owned:
                        logger.warning(
                            "Code Squad: user %s supplied a session_id they do not "
                            "own; write dropped.", user_id
                        )
                        return

                    # Check if the prompt is already saved as a user message
                    existing = thread_db.query(ChatMessage).filter(
                        ChatMessage.session_id == session_id,
                        ChatMessage.role == "user"
                    ).first()
                    if not existing:
                        thread_db.add(ChatMessage(
                            session_id=session_id, role="user", content=prompt
                        ))

                    thread_db.add(ChatMessage(
                        session_id=session_id, role="assistant", content=collected_raw
                    ))
                    thread_db.commit()
                    logger.info(f"Saved generated code history for session {session_id}")
                except Exception as e:
                    logger.error(f"Failed to save code history: {e}")
                finally:
                    thread_db.close()

            await asyncio.to_thread(_save_history)

    except WebSocketDisconnect:
        logger.info("Code Squad WebSocket disconnected")
    except Exception as e:
        logger.error(f"Code Squad error: {e}", exc_info=True)
        try:
            async with write_lock:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
