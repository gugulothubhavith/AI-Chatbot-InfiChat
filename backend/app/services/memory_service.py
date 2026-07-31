import logging
import asyncio
from sqlalchemy.orm import Session
from app.models.memory import Memory
from app.services.llm_router import call_llm
from app.database.db import SessionLocal
from app.core.config import settings
import random

logger = logging.getLogger(__name__)

async def extract_and_store_memories(user_id: int, user_message: str, assistant_response: str):
    """
    Background task to extract facts from the conversation and store them.
    This runs asynchronously to not block the chat response.
    """
    logger.info(f"Starting memory extraction for user {user_id}...")
    try:
        # Prompt Llama 3.3 to act as a memory extractor
        prompt = (
            f"Analyze the following conversation interaction.\n"
            f"User: {user_message}\n"
            f"Assistant: {assistant_response}\n\n"
            "Extract any permanent user facts, preferences, or project details that should be remembered for future sessions.\n"
            "Examples: 'User is learning Python', 'User prefers dark mode', 'Project is a weather app'.\n"
            "Return ONLY the extracted facts as a bulleted list. If there are no new important facts, return 'NO_MEMORY'.\n"
        )
        
        api_keys = [settings.DEFAULT_CHAT_API_KEY, getattr(settings, "PLANNER_API_KEY", None), getattr(settings, "CODER_API_KEY", None)]
        valid_keys = list(set(k for k in api_keys if k and k.startswith("nvapi")))
        chosen_key = random.choice(valid_keys) if valid_keys else settings.DEFAULT_CHAT_API_KEY

        payload = {
            "model": getattr(settings, "MEMORY_EXTRACTOR_MODEL", "nvidia/nemotron-3-ultra-550b-a55b"),
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "api_key": chosen_key
        }
        
        response = await call_llm("chat", payload)
        content = response['choices'][0]['message']['content']
        logger.info(f"Memory Extractor Output: {content}")
        
        if "NO_MEMORY" in content or not content.strip():
            return
            
        # Parse bullet points
        facts = [line.strip().replace("- ", "").replace("* ", "") for line in content.split("\n") if line.strip().startswith(("-", "*"))]
        
        if not facts:
            return

        def _store(extracted_facts: list[str]) -> None:
            """Write the extracted facts on this thread's own Session.

            Synchronous by design: the caller offloads it with
            ``asyncio.to_thread`` so the insert stays off the event loop. This
            function is reached after an ``await``, so committing inline would
            block the loop — and every concurrent request with it — for the
            duration of the write.
            """
            db = SessionLocal()
            try:
                for fact in extracted_facts:
                    logger.info(f"🧠 Storing Memory for User {user_id}: {fact}")
                    db.add(Memory(user_id=user_id, content=fact))
                db.commit()
            finally:
                db.close()

        await asyncio.to_thread(_store, facts)

    except Exception as e:
        logger.error(f"Memory extraction failed: {e}")

def get_relevant_memories(user_id: int, limit: int = 5) -> str:
    """
    Retrieve recent memories for the user to inject into context.
    Real implementation would use vector search, but for now we fetch latest 5.
    """
    db = SessionLocal()
    try:
        # Get latest 5 memories
        memories = db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.created_at.desc()).limit(limit).all()
        if not memories:
            return ""
            
        memory_text = "\n".join([f"- {m.content}" for m in memories])
        return f"User Core Memories:\n{memory_text}\n"
    finally:
        db.close()