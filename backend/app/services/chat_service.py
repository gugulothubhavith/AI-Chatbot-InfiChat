from app.schemas.chat import ChatRequest, ChatResponse
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.services.llm_router import call_llm
from app.services.rag_service import query_rag
from app.services.memory_service import get_relevant_memories, extract_and_store_memories
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
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

async def process_chat(payload: ChatRequest, user: User, db: Session, background_tasks: BackgroundTasks = None, stream: bool = False):
    logger.info(f"Process Chat Start: user={user.email}, session={payload.conversation_id}, model={payload.model}")
    from app.services.privacy_service import scrub_text
    
    # Pre-process: PII Scrubbing
    if payload.messages:
        last_msg = payload.messages[-1]
        last_msg.content = scrub_text(last_msg.content)

    session_id = payload.conversation_id
    
    # 1. Ensure Session exists
    if not session_id:
        # Create new session if none provided
        session = ChatSession(user_id=user.id, workspace=payload.workspace or "personal")
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    else:
        logger.info(f"Looking up session: session_id={session_id} (type={type(session_id)}), user_id={user.id} (type={type(user.id)})")
        session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
        if not session:
            # Check if it exists AT ALL in the DB to distinguish between 'not found' and 'unauthorized'
            exists = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if exists:
                logger.error(f"UNAUTHORIZED ACCESS ATTEMPT: User {user.id} tried to access session {session_id} owned by {exists.user_id}")
                raise ValueError("Unauthorized: You do not own this session")
            else:
                logger.warning(f"Session {session_id} not found in database for user {user.id}")
                raise ValueError("Session not found")

    # 2. Save User Message
    last_msg = payload.messages[-1]
    db_user_msg = ChatMessage(
        session_id=session_id, 
        role="user", 
        content=last_msg.content, 
        image_url=last_msg.image,
        file_name=last_msg.file_name,
        file_type=last_msg.file_type
    )
    db.add(db_user_msg)
    
    # 3. Auto-Title if needed
    message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
    if message_count <= 1:
        session.title = await generate_title(last_msg.content)
    
    db.commit()

    # --- REDIS SESSION TRACKING (Sync user message) ---
    try:
        redis_key = f"session:history:{session_id}"
        msg_json = json.dumps({"role": "user", "content": last_msg.content})
        redis_client.rpush(redis_key, msg_json)
        redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        logger.warning(f"Failed to push user message to Redis: {e}")

    # (Web search feature removed)

    # 5. Build full context for LLM (Redis first, DB fallback)
    messages = []
    redis_key = f"session:history:{session_id}"
    
    try:
        cached_history = redis_client.lrange(redis_key, 0, -1)
        if cached_history:
            logger.info(f"Chat Session Cache Hit: {redis_key}")
            messages = [json.loads(m) for m in cached_history]
        else:
            logger.info(f"Chat Session Cache Miss: {redis_key}")
            # Load from DB
            history_query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc())
            if payload.history_limit:
                history_query = history_query.limit(payload.history_limit)
            
            history = history_query.all()
            history.reverse()
            
            for h in history:
                messages.append({"role": h.role, "content": h.content})
            
            # Populate Redis for next time
            if messages:
                redis_client.delete(redis_key)
                redis_client.rpush(redis_key, *[json.dumps(m) for m in messages])
                redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        logger.warning(f"Fast session tracking failed: {e}. Falling back to standard DB retrieval.")
        # Re-run standard DB retrieval if Redis completely fails
        history_query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc())
        if payload.history_limit:
            history_query = history_query.limit(payload.history_limit)
        history = history_query.all()
        history.reverse()
        messages = [{"role": h.role, "content": h.content} for h in history]
    
    # 6. RAG Integration (Attachment-Driven)
    try:
        attached_file = getattr(last_msg, 'file_name', None)
        # ONLY trigger RAG if a file is present in the current Turn 
        if attached_file:
            query = last_msg.content or "What is this document about?"
            logger.info(f"Querying RAG for turn-attached file: {attached_file}")
            context = query_rag(query, filename_filter=attached_file)
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
                if not within_auto_search_cap(str(user.id)):
                    logger.info(
                        "Auto-search suppressed: user %s over daily cap", user.id
                    )
                else:
                    logger.info(
                        "Auto-Triggering Web Search (reason=%s) for user %s",
                        intent.reason, user.id,
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
                        record_auto_search(str(user.id))
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

    # User Personalization from Settings
    user_settings = user.settings or {}
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
        memories = get_relevant_memories(user.id)
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
                
                # Once stream ends, save to DB
                db_assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=full_content)
                db.add(db_assistant_msg)
                db.commit()
                if background_tasks:
                     background_tasks.add_task(extract_and_store_memories, user.id, last_msg.content, full_content)
                
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
    
    # Save Assistant Message
    db_assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=content)
    db.add(db_assistant_msg)
    db.commit()

    if background_tasks:
         background_tasks.add_task(extract_and_store_memories, user.id, last_msg.content, content)

    # Save Assistant Message to Redis
    try:
        redis_key = f"session:history:{session_id}"
        redis_client.rpush(redis_key, json.dumps({"role": "assistant", "content": content}))
        redis_client.expire(redis_key, SESSION_TTL)
    except Exception as e:
        logger.warning(f"Failed to push assistant message to Redis: {e}")

    return ChatResponse(role="assistant", content=content), session_id

def delete_user_chat_history(user_id: str, db: Session):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).all()
    for session in sessions:
        db.delete(session)
    db.commit()

def export_user_chat_history(user_id: str, db: Session):
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