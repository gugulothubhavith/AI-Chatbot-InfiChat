from app.schemas.chat import ChatRequest, ChatResponse
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.llm_router import call_llm
from app.services.rag_service import query_rag
from app.services.memory_service import get_relevant_memories, extract_and_store_memories
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
import asyncio
import logging
import json
from datetime import datetime, timezone

from app.core.redis_client import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)

SESSION_TTL = 86400  # 24 hours

async def generate_title(content: str) -> str:
    """Generate a concise title for a new chat session."""
    prompt = f"Generate a very concise title (max 6 words) for a chat that starts with this message: '{content}'. Return ONLY the title text."
    try:
        resp = await call_llm("chat", {"model": settings.DEFAULT_CHAT_MODEL, "messages": [{"role": "user", "content": prompt}]})
        title = resp['choices'][0]['message']['content'].strip(' "')
        return title[:100]
    except Exception:
        return content[:50] + "..."

async def process_chat(payload: ChatRequest, user: User, background_tasks: BackgroundTasks = None, stream: bool = False):
    """Run one chat turn, streaming or not.

    Takes no ``db``: every database touch here runs in a worker thread on its
    own short-lived Session. Two reasons. A Session is not safe to share across
    threads, and on the streaming path this coroutine's work outlives the
    request handler — holding a request-scoped connection for the length of a
    model response starves the pool (20 + 40 overflow) after a handful of
    concurrent chats.

    ``user`` is still a live ORM instance, so the attributes needed are copied
    into plain locals before the first commit; see below.
    """
    logger.info(f"Process Chat Start: user={user.email}, session={payload.conversation_id}, model={payload.model}")
    from app.services.privacy_service import scrub_text
    
    # Pre-process: PII Scrubbing
    if payload.messages:
        last_msg = payload.messages[-1]
        last_msg.content = scrub_text(last_msg.content)

    session_id = payload.conversation_id
    last_msg = payload.messages[-1]

    # Read the ORM attributes we need *before* any commit. The request-scoped
    # ``db`` uses expire_on_commit=True, so touching user.settings after a commit
    # would emit a lazy-load SELECT — on the event loop, in the middle of a
    # stream. Plain values are also what's safe to hand to a worker thread.
    user_id = user.id
    user_settings = user.settings or {}

    # 1. Ensure the session exists, and learn whether this turn needs a title.
    #
    # Every DB touch below runs in a worker thread with its own Session. Two
    # reasons it does not reuse ``db``: a Session is not safe to share across
    # threads, and the streaming path lives for as long as the model talks — a
    # request-scoped connection held open that whole time starves the pool
    # (20 + 40 overflow) under a handful of concurrent chats.
    def _ensure_session(session_id_arg, workspace):
        from app.database.db import SessionLocal
        thread_db = SessionLocal()
        try:
            if not session_id_arg:
                session = ChatSession(user_id=user_id, workspace=workspace or "personal")
                thread_db.add(session)
                thread_db.commit()
                thread_db.refresh(session)
                # Brand-new session: no messages yet, so this turn titles it.
                return session.id, True

            session = thread_db.query(ChatSession).filter(
                ChatSession.id == session_id_arg,
                ChatSession.user_id == user_id,
            ).first()
            if not session:
                # Distinguish 'not found' from 'not yours' for the log only; both
                # surface to the caller as a ValueError so neither leaks the
                # existence of another user's session.
                exists = thread_db.query(ChatSession).filter(
                    ChatSession.id == session_id_arg
                ).first()
                if exists:
                    logger.error(
                        "UNAUTHORIZED ACCESS ATTEMPT: User %s tried to access session %s owned by %s",
                        user_id, session_id_arg, exists.user_id,
                    )
                    raise ValueError("Unauthorized: You do not own this session")
                logger.warning("Session %s not found in database for user %s", session_id_arg, user_id)
                raise ValueError("Session not found")

            # Counted before the user message is inserted, matching the original
            # ordering (autoflush=False meant the pending add never counted).
            message_count = thread_db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id_arg
            ).count()
            return session_id_arg, message_count <= 1
        finally:
            thread_db.close()

    session_id, needs_title = await asyncio.to_thread(
        _ensure_session, session_id, payload.workspace
    )

    # 2. Title generation is an LLM call, so it belongs on the loop, not in the
    # thread that writes it.
    title = await generate_title(last_msg.content) if needs_title else None

    # 3. Persist the user message (and the title, in the same transaction).
    def _save_user_message(title_arg):
        from app.database.db import SessionLocal
        thread_db = SessionLocal()
        try:
            thread_db.add(ChatMessage(
                session_id=session_id,
                role="user",
                content=last_msg.content,
                image_url=last_msg.image,
                file_name=last_msg.file_name,
                file_type=last_msg.file_type,
            ))
            if title_arg is not None:
                thread_db.query(ChatSession).filter(
                    ChatSession.id == session_id
                ).update({"title": title_arg}, synchronize_session=False)
            thread_db.commit()
        finally:
            thread_db.close()

    await asyncio.to_thread(_save_user_message, title)

    # --- REDIS SESSION TRACKING (Sync user message) ---
    try:
        redis_key = f"session:history:{session_id}"
        msg_json = json.dumps({"role": "user", "content": last_msg.content})
        redis_client.rpush(redis_key, msg_json)
        redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        logger.warning(f"Failed to push user message to Redis: {e}")

    # (Web search feature removed)

    # 4. Build full context for LLM (Redis first, DB fallback)
    redis_key = f"session:history:{session_id}"

    def _load_history():
        """Newest-first query, reversed to chronological, as plain dicts.

        Returns dicts rather than ORM instances deliberately: the objects would
        be bound to a Session this thread is about to close, so any attribute
        read on the loop afterwards would raise DetachedInstanceError.
        """
        from app.database.db import SessionLocal
        thread_db = SessionLocal()
        try:
            history_query = thread_db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc())
            if payload.history_limit:
                history_query = history_query.limit(payload.history_limit)
            history = history_query.all()
            history.reverse()
            return [{"role": h.role, "content": h.content} for h in history]
        finally:
            thread_db.close()

    try:
        cached_history = redis_client.lrange(redis_key, 0, -1)
        if cached_history:
            logger.info(f"Chat Session Cache Hit: {redis_key}")
            messages = [json.loads(m) for m in cached_history]
        else:
            logger.info(f"Chat Session Cache Miss: {redis_key}")
            messages = await asyncio.to_thread(_load_history)

            # Populate Redis for next time
            if messages:
                redis_client.delete(redis_key)
                redis_client.rpush(redis_key, *[json.dumps(m) for m in messages])
                redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        # Covers both a Redis outage and a malformed cache entry. The DB is the
        # source of truth, so fall back to it rather than failing the turn.
        logger.warning(f"Fast session tracking failed: {e}. Falling back to standard DB retrieval.")
        messages = await asyncio.to_thread(_load_history)
    
    # 6. RAG Integration (Attachment-Driven)
    try:
        attached_file = getattr(last_msg, 'file_name', None)
        # ONLY trigger RAG if a file is present in the current Turn 
        if attached_file:
            query = last_msg.content or "What is this document about?"
            logger.info(f"Querying RAG for turn-attached file: {attached_file}")
            # Vector search plus an embedding call — both blocking, both off-loop.
            context = await asyncio.to_thread(query_rag, query, filename_filter=attached_file)
            if context and messages:
                rag_instructions = (
                    "You are an AI assistant with access to a knowledge base. "
                    "Below is the relevant context retrieved from uploaded documents. "
                    "Use ONLY this context to answer the user's question as accurately and comprehensively as possible. "
                    "If the answer is not contained within the provided context, state that you do not have enough information from the documents to answer, but you can answer based on your general knowledge if appropriate (clearly distinguishing between the two). "
                    "Important: Always cite your sources by mentioning the [Source: filename] provided in the context for each piece of information used.\n\n"
                    f"--- CONTEXT START ---\n{context}\n--- CONTEXT END ---\n\n"
                    f"User Question: {query}"
                )
                messages[-1]["content"] = rag_instructions
    except Exception as e:
        logger.warning(f"RAG Lookup failed: {e}")

    # 7. Memory & System Prompt Injection
    system_messages = []

    # Records whether an auto web-search actually grounded this turn, so the
    # stream can surface a "Searched the web automatically" affordance.
    auto_searched = False

    # 7.5 Auto-Trigger Web Search (intent-driven, unmetered, abuse-capped).
    #
    # This escalates a plain chat turn to a grounded web search WITHOUT the user
    # flipping the manual toggle. Per product spec it is NOT metered against the
    # web_search quota — that quota is only consumed on the explicit /web_search/
    # endpoint. A per-user daily ceiling (Redis) stops it being a free bypass.
    #
    # Users can disable auto-search entirely from settings; the client signals
    # that by setting `web_search=False` intent off via the `auto_web_search`
    # flag on the request (defaults to enabled).
    auto_search_enabled = getattr(payload, "auto_web_search", True)
    if (
        auto_search_enabled
        and not attached_file
        and payload.model != "research_agent"
        and last_msg.content
    ):
        from app.services.web_search.intent import (
            should_auto_search,
            within_auto_search_cap,
            record_auto_search,
        )

        try:
            intent = await should_auto_search(last_msg.content)
            if intent.should_search:
                if not within_auto_search_cap(str(user_id)):
                    logger.info(
                        "Auto-search suppressed: user %s over daily cap", user_id
                    )
                else:
                    logger.info(
                        "Auto-Triggering Web Search (reason=%s) for user %s",
                        intent.reason, user_id,
                    )
                    from app.services.web_search.orchestrator import run_web_search

                    search_report = ""
                    async for event in run_web_search(
                        last_msg.content,
                        model=payload.model or settings.DEFAULT_CHAT_MODEL,
                    ):
                        if not event.startswith("data: "):
                            continue
                        data_str = event[6:].strip()
                        if not data_str:
                            continue
                        try:
                            data = json.loads(data_str)
                        except Exception:
                            continue
                        if data.get("type") == "report":
                            report_content = data.get("content", "")
                            citations = data.get("citations", [])
                            if citations:
                                cit_str = "\n".join(
                                    f"[{c.get('index')}] [{c.get('title')}]({c.get('url')})"
                                    for c in citations
                                )
                                report_content += "\n\n---\n**Sources:**\n" + cit_str
                            search_report = report_content

                    if search_report:
                        record_auto_search(str(user_id))
                        auto_searched = True
                        system_messages.append(
                            "Web Search Results (Real-time data):\n"
                            f"{search_report}\n\n"
                            "Use this information to accurately answer the user's query. "
                            "Cite sources inline using the [n] markers provided."
                        )
        except Exception as e:
            # Auto-search must never break a normal reply.
            logger.warning(f"Auto-Trigger Web Search failed: {e}")


    # User Custom System Prompt
    if payload.system_prompt:
        system_messages.append(f"Custom Instruction:\n{payload.system_prompt}")

    # User Personalization from Settings (hoisted above, pre-commit)
    personal_info = []
    if user_settings.get("nickname"):
        personal_info.append(f"The user's nickname is: {user_settings.get('nickname')}")
    if user_settings.get("occupation"):
        personal_info.append(f"The user's occupation is: {user_settings.get('occupation')}")
    if user_settings.get("moreAboutYou"):
        personal_info.append(f"About the user: {user_settings.get('moreAboutYou')}")
    if user_settings.get("customInstructions"):
        personal_info.append(f"Custom Instructions: {user_settings.get('customInstructions')}")
    
    if personal_info:
        system_messages.append("User Personalization:\n" + "\n".join(personal_info))

    try:
        memories = await asyncio.to_thread(get_relevant_memories, user_id)
        if memories:
            system_messages.append(f"System Memory (Authoritative):\n{memories}")
    except Exception as e:
         logger.warning(f"Memory lookup failed: {e}")

    if system_messages:
        messages.insert(0, {"role": "system", "content": "\n\n".join(system_messages)})

    # 8. Local Document Parsing (Omni-Parser)
    if last_msg.image:
        from app.services.attachment_extractor import process_attachment_via_unstructured
        
        # Send attachment to local Docker Unstructured API
        extracted_markdown = await process_attachment_via_unstructured(
            last_msg.image, 
            file_name=last_msg.file_name
        )
        
        # Inject extracted text into standard prompt context
        new_content = (last_msg.content or "Please review the attached document.") + "\n\n"
        new_content += "--- EXTRACTED ATTACHMENT CONTENT ---\n"
        new_content += extracted_markdown
        new_content += "\n------------------------------------\n"
        
        messages[-1]["content"] = new_content
        
        llm_model = payload.model or settings.DEFAULT_CHAT_MODEL
        key_group = "rag" if payload.use_rag else "chat"
    else:
        llm_model = payload.model or settings.DEFAULT_CHAT_MODEL
        key_group = "rag" if payload.use_rag else "chat"

    llm_payload = {
        "messages": messages,
        "model": llm_model,
        "stream": stream,
        "temperature": payload.temperature if payload.temperature is not None else 0.7,
        "max_tokens": payload.max_tokens if payload.max_tokens is not None else 2048,
        "top_p": payload.top_p if payload.top_p is not None else 1.0,
        "frequency_penalty": payload.frequency_penalty if payload.frequency_penalty is not None else 0.0,
        "presence_penalty": payload.presence_penalty if payload.presence_penalty is not None else 0.0,
    }

    if stream:
        async def stream_wrapper():
            try:
                logger.info(f"Stream Wrapper starting for model: {llm_model}")
                # Surface the auto web-search affordance up front so the UI can
                # show "Searched the web automatically" before the answer streams.
                if auto_searched:
                    yield {"type": "web_search_auto", "active": True}
                full_content = ""
                # call_llm returns an async generator for stream=True
                generator = await call_llm("chat", llm_payload, key_group=key_group, stream=True)
                logger.info(f"call_llm returned generator of type: {type(generator)}")
                async for chunk in generator:
                     full_content += chunk
                     yield chunk

                # Once stream ends, save to DB — offload to worker thread so the
                # commit doesn't block the loop while the client drains the queue.
                def _save_assistant_message(content):
                    from app.database.db import SessionLocal
                    thread_db = SessionLocal()
                    try:
                        thread_db.add(ChatMessage(
                            session_id=session_id,
                            role="assistant",
                            content=content,
                        ))
                        thread_db.commit()
                    finally:
                        thread_db.close()

                await asyncio.to_thread(_save_assistant_message, full_content)

                if background_tasks:
                     background_tasks.add_task(extract_and_store_memories, user_id, last_msg.content, full_content)

                # Save Assistant Message to Redis
                try:
                    redis_key = f"session:history:{session_id}"
                    redis_client.rpush(redis_key, json.dumps({"role": "assistant", "content": full_content}))
                    redis_client.expire(redis_key, SESSION_TTL)
                except Exception as e:
                    logger.warning(f"Failed to push assistant message to Redis: {e}")
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Stream Wrapper Critical Failure: {e}\n{error_trace}")
                yield f"\n\n❌ **[System Error]**: {str(e)}"

        return stream_wrapper(), session_id

    # Non-streaming
    response_data = await call_llm("chat", llm_payload, key_group=key_group)
    content = response_data.get('choices', [])[0].get('message', {}).get('content', "No content")

    # Save Assistant Message — off-loop, same as the streaming path.
    def _save_assistant_message(assistant_content):
        from app.database.db import SessionLocal
        thread_db = SessionLocal()
        try:
            thread_db.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
            ))
            thread_db.commit()
        finally:
            thread_db.close()

    await asyncio.to_thread(_save_assistant_message, content)

    if background_tasks:
         background_tasks.add_task(extract_and_store_memories, user_id, last_msg.content, content)

    # Save Assistant Message to Redis
    try:
        redis_key = f"session:history:{session_id}"
        redis_client.rpush(redis_key, json.dumps({"role": "assistant", "content": content}))
        redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        logger.warning(f"Failed to push assistant message to Redis: {e}")

    return ChatResponse(role="assistant", content=content), session_id

def delete_user_chat_history(user_id: str, db: Session):
    """Delete all chat sessions and their messages for a user.

    The passed ``db`` is the request-scoped session from the route dependency.
    This function does not live for minutes like a stream, so reusing the
    scoped session is safe here.
    """
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    for session in sessions:
        db.delete(session)
    db.commit()

def export_user_chat_history(user_id: str, db: Session):
    """Export all chat sessions and messages for a user as JSON.

    Same scoping note as ``delete_user_chat_history``: the request-scoped
    session is safe here because this is a synchronous read that finishes in
    under a second.
    """
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    export_data = []
    for session in sessions:
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.asc()).all()
        session_data = {
            "id": str(session.id),
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat()
                } for msg in messages
            ]
        }
        export_data.append(session_data)

    return {"sessions": export_data, "generated_at": datetime.now(timezone.utc).isoformat()}