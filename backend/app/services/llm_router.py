import httpx
import os
from fastapi import HTTPException
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

# API ENDPOINTS
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

MODEL_MAP = {
    # Groq Models (Updated for Decommissions)
    "llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
    "llama3-70b": "llama-3.3-70b-versatile",
    "llama3-8b": "llama-3.1-8b-instant",
    "llama-3.1-8b-instant": "llama-3.1-8b-instant",
    "mixtral": "llama-3.3-70b-versatile", # Fallback for decommissioned mixtral
    "gemma": "llama-3.1-8b-instant", # Fallback for decommissioned gemma
    # Vision Model
    "vision_model": settings.VISION_MODEL,
    # Multi-Agent Defaults
    "planner_agent": settings.PLANNER_MODEL,
    "coder_agent": settings.CODER_MODEL,
    "reviewer_agent": settings.REVIEWER_MODEL,
    "research_agent": settings.PLANNER_MODEL,
}

def is_groq_model(model_name: str) -> bool:
    """Check if the model is intended for Groq."""
    groq_models = [
        "llama-3.3-70b-versatile", 
        "llama-3.1-8b-instant",
        "llama-3.2-11b-vision-preview",
        "llama-3.2-3b-preview",
        "llama-3.2-1b-preview",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "whisper-large-v3",
        "whisper-large-v3-turbo"
    ]
    return model_name in groq_models or model_name.endswith("-groq") or "llama" in model_name.lower() or "whisper" in model_name.lower()

def convert_to_gemini_format(messages: list) -> dict:
    """Convert OpenAI-style messages (including multi-modal) to Gemini format."""
    contents = []
    system_instruction = None
    
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        
        if role == "system":
            system_instruction = {"parts": [{"text": content}]}
            continue
            
        gemini_parts = []
        if isinstance(content, list):
            for part in content:
                if part.get("type") == "text":
                    gemini_parts.append({"text": part.get("text")})
                elif part.get("type") == "image_url":
                    image_url = part.get("image_url", {}).get("url", "")
                    if image_url.startswith("data:image/"):
                        try:
                            # Format: data:image/png;base64,iVBOR...
                            header, data = image_url.split(",", 1)
                            mime_type = header.split(":", 1)[1].split(";", 1)[0]
                            gemini_parts.append({
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": data
                                }
                            })
                        except Exception as e:
                            logger.error(f"Failed to parse image data URL: {e}")
        else:
            gemini_parts.append({"text": content})
            
        contents.append({
            "role": "user" if role == "user" else "model",
            "parts": gemini_parts
        })
        
    payload = {"contents": contents}
    if system_instruction:
        payload["system_instruction"] = system_instruction
        
    return payload

async def call_gemini(payload: dict, model: str = None, api_key: str = None, stream: bool = False):
    """Call Google Gemini API."""
    model = model or settings.VISION_MODEL
    api_key = api_key or settings.GOOGLE_API_KEY
    
    # Use v1beta for stream support and newer models
    endpoint = "streamGenerateContent" if stream else "generateContent"
    url = f"{GEMINI_BASE_URL}/{model}:{endpoint}?key={api_key}"
    
    gemini_payload = convert_to_gemini_format(payload.get("messages", []))
    headers = {"Content-Type": "application/json"}
    
    if stream:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    async with client.stream("POST", url, headers=headers, json=gemini_payload) as response:
                        response.raise_for_status()
                        buffer = ""
                        async for chunk in response.aiter_text():
                            if not chunk: continue
                            buffer += chunk
                            
                            # Gemini sends JSON objects that might be split. 
                            # We look for "text": "..." patterns inside the accumulated buffer.
                            while True:
                                try:
                                    # Very basic extraction for speed, but robust to split chunks
                                    if '"text": "' in buffer:
                                        start_idx = buffer.find('"text": "') + 9
                                        end_idx = buffer.find('"', start_idx)
                                        if end_idx != -1:
                                            text_part = buffer[start_idx:end_idx]
                                            # Decode unicode escapes
                                            try:
                                                decoded_text = text_part.encode().decode('unicode-escape')
                                                yield decoded_text
                                            except:
                                                yield text_part
                                            
                                            # Remove processed part from buffer
                                            buffer = buffer[end_idx + 1:]
                                        else:
                                            # Found start but not end, wait for more data
                                            break
                                    else:
                                        # No more text parts found in current buffer
                                        if len(buffer) > 1000: # Safety flush if buffer grows too large without match
                                            buffer = buffer[-500:]
                                        break
                                except Exception as e:
                                    logger.error(f"Gemini internal parse error: {e}")
                                    break
                except Exception as e:
                    logger.error(f"Gemini Stream Failed: {e}")
                    yield f"\n❌ [Gemini Stream Error]: {str(e)}"
        return stream_generator()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, headers=headers, json=gemini_payload)
            response.raise_for_status()
            data = response.json()
            text = data['candidates'][0]['content']['parts'][0]['text']
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": text
                        }
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Gemini Call Failed ({model}): {e}")
            raise HTTPException(status_code=502, detail=f"Gemini API Error: {str(e)}")

async def call_openrouter(payload: dict, api_key: str, stream: bool = False):
    """Call OpenRouter API (OpenAI Compatible) with streaming support."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
        "X-Title": "Antigravity AI Chatbot"
    }
    
    payload["stream"] = stream
    
    if stream:
        async def stream_generator():
            async with httpx.AsyncClient(timeout=120.0) as client:
                try:
                    async with client.stream("POST", OPENROUTER_CHAT_URL, headers=headers, json=payload) as response:
                        if response.status_code != 200:
                            error_detail = await response.aread()
                            logger.error(f"OpenRouter Stream Error ({response.status_code}): {error_detail.decode()}")
                            yield f"\n❌ [OpenRouter Error]: {response.status_code}"
                            return

                        buffer = ""
                        async for chunk in response.aiter_text():
                            if not chunk: continue
                            buffer += chunk
                            
                            lines = buffer.split('\n')
                            # Keep the last potentially incomplete line in the buffer
                            buffer = lines.pop()
                            
                            for line in lines:
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]": continue
                                    try:
                                        data = json.loads(data_str)
                                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if content:
                                            yield content
                                    except:
                                        pass
                except Exception as e:
                    logger.error(f"OpenRouter Stream Failed: {e}")
                    yield f"\n❌ [OpenRouter Stream Error]: {str(e)}"
        return stream_generator()

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(OPENROUTER_CHAT_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"OpenRouter Call Failed: {e}")
            raise HTTPException(status_code=502, detail=f"OpenRouter API Error: {str(e)}")

async def call_llm(request_type: str, payload: dict, key_group: str = None, stream: bool = False):
    """
    Call LLM via appropriate provider (Groq, OpenRouter, Gemini).
    Supports streaming if stream=True.
    """
    requested_alias = payload.get("model", settings.GROQ_MODEL)
    model_name = MODEL_MAP.get(requested_alias, requested_alias)
    payload["model"] = model_name
    payload["stream"] = stream

    try:
        # 1. Route Multi-Agent Specific Requests (Explicit Aliases)
        if requested_alias == "planner_agent":
            logger.info(f"Routing Planner to Groq: {model_name}")
            api_key = settings.PLANNER_API_KEY or settings.GROQ_API_KEY
        elif requested_alias == "research_agent":
            logger.info(f"Routing Search Agent to Groq: {model_name}")
            api_key = settings.PLANNER_API_KEY or settings.GROQ_API_KEY
        elif requested_alias == "coder_agent":
            logger.info(f"Routing Coder to OpenRouter: {model_name}")
            return await call_openrouter(payload, settings.CODER_API_KEY, stream=stream)
        elif requested_alias == "reviewer_agent":
            if "gemini" in model_name.lower():
                logger.info(f"Routing Reviewer to Gemini: {model_name}")
                return await call_gemini(payload, model=model_name, api_key=settings.REVIEWER_API_KEY, stream=stream)
            else:
                logger.info(f"Routing Reviewer to OpenRouter: {model_name}")
                return await call_openrouter(payload, settings.CODER_API_KEY or os.getenv("OPENROUTER_API_KEY"), stream=stream)

        # 2. Intelligent Routing based on Model ID Pattern
        elif "gemini" in model_name.lower():
            logger.info(f"Auto-Routing Gemini model: {model_name}")
            return await call_gemini(payload, model=model_name, stream=stream)
        elif "/" in model_name or "deepseek" in model_name.lower() or "claude" in model_name.lower():
            logger.info(f"Auto-Routing OpenRouter model: {model_name}")
            or_key = settings.CODER_API_KEY or os.getenv("OPENROUTER_API_KEY")
            return await call_openrouter(payload, or_key, stream=stream)
        elif key_group == "vision" or model_name == settings.VISION_MODEL:
            logger.info(f"Routing Vision to Gemini: {model_name}")
            return await call_gemini(payload, stream=stream)
        
        # 3. Default Groq Routing (Llama, Mixtral, etc.)
        logger.info(f"Routing '{request_type}' (stream={stream}) to Groq Model: {model_name}")
        api_key = settings.GROQ_API_KEY
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        url = GROQ_CHAT_URL
        
        if stream:
            async def stream_generator():
                async with httpx.AsyncClient(timeout=120.0) as client:
                    try:
                        async with client.stream("POST", url, headers=headers, json=payload) as response:
                            if response.status_code != 200:
                                error_detail = await response.aread()
                                logger.error(f"Groq Stream Error ({response.status_code}): {error_detail.decode()}")
                                yield f"\n❌ [Groq Error]: {response.status_code}"
                                return

                            buffer = ""
                            async for chunk in response.aiter_text():
                                if not chunk: continue
                                buffer += chunk
                                
                                lines = buffer.split('\n')
                                buffer = lines.pop()
                                
                                for line in lines:
                                    if line.startswith("data: "):
                                        data_str = line[6:].strip()
                                        if data_str == "[DONE]": continue
                                        try:
                                            data = json.loads(data_str)
                                            content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                            if content:
                                                yield content
                                        except:
                                            pass
                    except Exception as e:
                        logger.error(f"Groq Stream Failed: {e}")
                        yield f"\n❌ [Streaming Error]: {str(e)}"
            return stream_generator()

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Groq Call Failed ({model_name}): {e}")
                raise HTTPException(status_code=502, detail=f"Groq API Error: {str(e)}")
    except Exception as e:
        logger.error(f"Routing Failure: {e}")
        if stream:
            async def error_gen():
                yield f"\n❌ [Routing Error]: {str(e)}"
            return error_gen()
        raise e