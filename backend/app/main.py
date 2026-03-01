from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from datetime import datetime

# CRITICAL: Import all models immediately to register them with SQLAlchemy/Base
from app import models 

import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Platform Backend...")
    logger.info(f"Project Name: {settings.PROJECT_NAME}")
    logger.info(f"Groq API Key set: {'Yes' if settings.GROQ_API_KEY else 'No'}")
    
    from app.database.db import init_db
    from app.services import voice_service
    try:
        await init_db()
        logger.info("Database initialized successfully.")
        
        # Pre-load STT and TTS models for zero-latency first use
        logger.info("Pre-loading neural models (Whisper & Kokoro)...")
        voice_service.preload_models()
        logger.info("Models pre-loaded.")
        
        # Automatically run schema fixes
        logger.info("Running automated schema fixes...")
        from fix_db_schema import fix_schema
        fix_schema()
    except Exception as e:
        logger.error(f"DATABASE ERROR ON STARTUP: {e}")
    yield

    # Shutdown
    print("Shutting down...")


tags_metadata = [
    {
        "name": "Auth",
        "description": "🔐 User registration, login (Password + OTP), JWT token management.",
    },
    {
        "name": "OAuth",
        "description": "🌐 Google OAuth 2.0 single sign-on integration.",
    },
    {
        "name": "Chat",
        "description": "💬 AI Chat sessions, streaming responses, conversation history, session management, sharing, and archiving.",
    },
    {
        "name": "Voice",
        "description": "🎙️ Professional Indic TTS engine (Edge-TTS): English, Hindi, Telugu voices. Speech-to-Text transcription via Whisper.",
    },
    {
        "name": "RAG",
        "description": "📚 Retrieval-Augmented Generation — upload documents (PDF, DOCX, TXT) to your personal Knowledge Base for context-aware responses.",
    },
    {
        "name": "Code Agent",
        "description": "🤖 Sandboxed Python code execution agent with real-time output streaming.",
    },
    {
        "name": "Image",
        "description": "🖼️ AI Image generation using Stable Diffusion XL.",
    },
    {
        "name": "Snippets",
        "description": "📝 Save, list, and delete reusable code or text snippets.",
    },
    {
        "name": "Settings",
        "description": "⚙️ User preferences: theme, voice, personalization, model config, notification channels.",
    },
    {
        "name": "Admin",
        "description": "🛡️ Admin-only controls: PII scrubbing toggle, privacy settings.",
    },
    {
        "name": "WebSocket",
        "description": "🔌 Real-time WebSocket endpoints for the Code Agent and AI Agent.",
    },
]

app = FastAPI(
    title="InfiChat",
    description=(
        "## InfiChat Backend API\n\n"
        "A fully self-hosted, multi-modal AI platform with:\n"
        "- **Streaming Chat** powered by Groq, Gemini, and OpenRouter\n"
        "- **Professional Indic TTS** — English, Hindi, Telugu voices\n"
        "- **Whisper STT** — speech-to-text transcription\n"
        "- **RAG** — personal Knowledge Base from uploaded documents\n"
        "- **Sandboxed Code Execution** — safe Python runner\n"
        "- **Google OAuth** + Password + OTP authentication\n\n"
        "All data is stored locally. No cloud required."
    ),
    version="2.0.0",
    contact={
        "name": "InfiChat",
    },
    openapi_tags=tags_metadata,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    error_msg = f"GLOBAL ERROR: {exc}\n{traceback.format_exc()}"
    logger.error(error_msg)
    
    # Also log to a file and console for visibility
    logger.error(error_msg)
    print(f"CRITICAL BACKEND ERROR: {error_msg}")
    
    try:
        with open("backend_errors.log", "a") as f:
            f.write(f"\n{'='*40}\n")
            f.write(f"TIMESTAMP: {datetime.utcnow()}\n")
            f.write(f"URL: {request.url}\n")
            f.write(error_msg)
            f.write(f"\n{'='*40}\n")
    except:
        pass

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": traceback.format_exc()}
    )


@app.get("/health", tags=["Health"])
async def health():
    from app.database.db import check_db_connection
    from app.core.redis_client import redis_client
    
    db_ok = await check_db_connection()
    
    redis_ok = False
    try:
        redis_ok = redis_client.ping()
    except:
        pass
        
    status = "ok" if (db_ok and redis_ok) else "degraded"
    
    return {
        "status": status,
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.utcnow()
    }


from app.api import auth, chat, code_agent, rag, image, oauth, admin, ws_code, ws_agent, voice, snippets, settings as settings_api

# Include Routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(code_agent.router)
app.include_router(image.router)
app.include_router(oauth.router)
app.include_router(admin.router)
app.include_router(ws_code.router)
app.include_router(ws_agent.router)
app.include_router(voice.router)
app.include_router(snippets.router)
app.include_router(settings_api.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "InfiChat Backend API is running",
        "docs_url": "/docs",
        "health_url": "/health",
        "version": "2.0.0"
    }

if __name__ == "__main__": 
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)