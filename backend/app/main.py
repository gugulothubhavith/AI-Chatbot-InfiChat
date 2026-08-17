from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.config import settings
from datetime import datetime, timezone
from slowapi.errors import RateLimitExceeded
import asyncio

# CRITICAL: Import all models immediately to register them with SQLAlchemy/Base
from app import models 

import logging
import os
import traceback as tb_module
from logging.handlers import RotatingFileHandler

# --- Bounded error log ---------------------------------------------------
# Unhandled exceptions are appended to a dedicated file for post-mortem
# debugging. This MUST be size-bounded: an unbounded open("...", "a") in the
# exception handler (the previous behaviour) lets a crash-looping request fill
# the disk, which is itself a denial-of-service. RotatingFileHandler caps the
# footprint at maxBytes * (backupCount + 1) and recycles old segments.
_ERROR_LOG_PATH = os.getenv("BACKEND_ERROR_LOG", "backend_errors.log")
_error_file_logger = logging.getLogger("app.backend_errors")
_error_file_logger.propagate = False  # keep these out of the console/root stream
if not _error_file_logger.handlers:
    try:
        _err_handler = RotatingFileHandler(
            _ERROR_LOG_PATH,
            maxBytes=int(os.getenv("BACKEND_ERROR_LOG_MAX_BYTES", str(5 * 1024 * 1024))),
            backupCount=int(os.getenv("BACKEND_ERROR_LOG_BACKUPS", "3")),
            encoding="utf-8",
            delay=True,  # don't open the file until the first error is written
        )
        _err_handler.setFormatter(logging.Formatter("%(message)s"))
        _error_file_logger.addHandler(_err_handler)
        _error_file_logger.setLevel(logging.ERROR)
    except Exception:
        # If the log file can't be opened (read-only FS, etc.) we simply skip
        # file logging — never let logging setup crash startup.
        _error_file_logger = None

# --- Sensitive Data Masking (Logging) ---
class RedactingFilter(logging.Filter):
    """Masks sensitive keys in logs (password, token, secret, key)"""
    def filter(self, record):
        msg = str(record.msg)
        sensitive_keys = ["password", "token", "secret", "key", "authorization", "cookie"]
        for key in sensitive_keys:
            # Simple case-insensitive redact for key-value looking strings
            import re
            msg = re.sub(rf'("{key}"\s*:\s*")([^"]+)"', rf'\1[REDACTED]"', msg, flags=re.IGNORECASE)
            msg = re.sub(rf'({key}=)([^&\s]+)', rf'\1[REDACTED]', msg, flags=re.IGNORECASE)
        record.msg = msg
        return True

logger = logging.getLogger(__name__)
# Apply the filter to all relevant loggers (including uvicorn)
for logger_name in [None, "uvicorn", "uvicorn.access", "uvicorn.error", "app.main", "app.services.rag_service"]:
    l = logging.getLogger(logger_name)
    l.addFilter(RedactingFilter())

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up AI Platform Backend...")
    logger.info(f"Project Name: {settings.PROJECT_NAME}")

    # Configure and report the NVIDIA API key pool.
    from app.services.key_pool import key_pool
    if key_pool.size == 0:
        key_pool.configure(settings.nvidia_api_keys)
    if key_pool.size == 0:
        logger.error(
            "No NVIDIA API keys configured — all AI features will fail. "
            "Set NVIDIA_API_KEY_1..4 in backend/.env"
        )
    else:
        logger.info(f"NVIDIA key pool: {key_pool.size} key(s) active, rotated per-agent")
    
    from app.database.db import init_db
    from app.services import voice_service
    try:
        await init_db()
        logger.info("Database initialized successfully.")
        
        # Pre-load STT and TTS models for zero-latency first use
        logger.info("Pre-loading neural models (Whisper & Kokoro)...")
        voice_service.preload_models()
        logger.info("Models pre-loaded.")

        # Seed default subscription plans
        logger.info("Seeding subscription plans...")
        from app.services.seed_plans import seed_plans
        seed_plans()
        logger.info("Subscription plans seeded.")

        # Seed the admin permission catalogue and starter roles.
        #
        # Must run BEFORE seed_admin: that function creates the SuperAdmin role,
        # and if it wins the race the role is created with an empty permission
        # set. More importantly, without this the admin_permissions table stays
        # empty, every RequiresPermission(...) check denies, and delegated
        # administration is impossible — only is_super_admin can do anything.
        logger.info("Seeding admin permissions and roles...")
        from app.core.permissions import seed_admin_rbac
        seed_admin_rbac()
        logger.info("Admin RBAC seeded.")

        # Seed default admin user (only if no admin exists)
        logger.info("Seeding default admin user...")
        from app.services.seed_admin import seed_admin
        seed_admin()
        logger.info("Admin seeding check complete.")
        logger.info("Admin panel: http://localhost:5174 — credentials are set via seed_admin/env, not logged.")

        # Automatically run schema fixes
        logger.info("Running automated schema fixes...")
        # from fix_db_schema import fix_schema
        # fix_schema()
    except Exception as e:
        logger.error(f"DATABASE ERROR ON STARTUP: {e}")

    # Auto-download spaCy model for Deep Research NER (if not already present)
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
            logger.info("spaCy model en_core_web_sm already available.")
        except OSError:
            logger.info("Downloading spaCy en_core_web_sm model...")
            from spacy.cli import download
            download("en_core_web_sm")
            logger.info("spaCy model downloaded successfully.")
    except ImportError:
        logger.warning("spaCy not installed — Deep Research NER will be limited.")
    except Exception as e:
        logger.warning(f"spaCy setup failed (non-critical): {e}")

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
    {
        "name": "Deep Research",
        "description": "🔬 11-Agent deep research pipeline with real-time progress streaming.",
    },
]

app = FastAPI(
    title="InfiChat",
    description=(
        "## Backend API\n\n"
        "InfiChat — AI Chat Platform with:\n"
        "- **Streaming Chat** powered by Groq and NVIDIA\n"
        "- **Professional Indic TTS** — English, Hindi, Telugu voices\n"
        "- **Whisper STT** — speech-to-text transcription\n"
        "- **RAG** — personal Knowledge Base from uploaded documents\n"
        "- **Sandboxed Code Execution** — safe Python runner\n"
        "- **Google OAuth** + Password + OTP authentication\n\n"
    ),
    version=settings.APP_VERSION,
    contact={
        "name": "InfiChat",
    },
    openapi_tags=tags_metadata,
    docs_url=None,           # Overridden below with custom CSS injection
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Serve logo from /static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Custom /docs — hides /openapi.json link and shows logo instead of InfiChat title
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui() -> HTMLResponse:
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="API Docs",
        swagger_favicon_url="/static/logo.png",
    )
    body = html.body.decode()
    custom_css = """
    <style>
      /* Hide the InfiChat title text and /openapi.json link */
      .swagger-ui .info .title,
      .swagger-ui .info a { display: none !important; }
      /* Show logo above the description */
      .swagger-ui .info::before {
        content: '';
        display: block;
        background-image: url('/static/logo.png');
        background-repeat: no-repeat;
        background-size: contain;
        width: 180px;
        height: 70px;
        margin-bottom: 16px;
      }
    </style>
    """
    body = body.replace("</head>", custom_css + "</head>")
    return HTMLResponse(content=body, status_code=200)

# --- Security Middleware Stack (order matters: last added = first executed) ---

# 0. Admin Audit Middleware — Automated logging of all admin actions
from app.middleware.audit_logging import AdminAuditMiddleware
app.add_middleware(AdminAuditMiddleware)

# 1. CORS Middleware — restrict to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    expose_headers=["X-Request-ID"],
    max_age=600,  # Cache preflight for 10 minutes
)

# 2. Trusted Host Middleware
if settings.ENVIRONMENT != "test":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts
    )

# 3. Security Headers Middleware (X-Frame-Options, CSP, HSTS, etc.)
from app.core.security import SecurityHeadersMiddleware
# Enforces maintenance mode. Registered here so it runs ahead of the feature
# middleware and every router — the point is to short-circuit before any of
# them do work.
from app.middleware.maintenance import MaintenanceModeMiddleware
app.add_middleware(MaintenanceModeMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

# 4. Input Sanitization Middleware (XSS, SQL injection, payload size)
from app.middleware.input_sanitizer import InputSanitizationMiddleware
app.add_middleware(InputSanitizationMiddleware)

# 5. Tenant Isolation Middleware
from app.middleware.tenant import TenantIsolationMiddleware
app.add_middleware(TenantIsolationMiddleware)

# 6. Advanced Infrastructure IP Firewall & Cloudflare Origin Shield (DDoS Mitigation)
from app.middleware.firewall import InfrastructureFirewallMiddleware
app.add_middleware(InfrastructureFirewallMiddleware)

# 7. Usage Tracking Middleware — subscription/enforcement
from app.middleware.usage_tracker import UsageTrackingMiddleware
app.add_middleware(UsageTrackingMiddleware)

# 8. CSRF Protection Middleware
from app.middleware.csrf import CSRFProtectionMiddleware
app.add_middleware(CSRFProtectionMiddleware)

# 9. Rate Limiter
from app.core.security import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(status_code=429, content={"detail": "Too many requests. Please slow down."}))

# 10. Pydantic Validation Error Handler — Hide internal field names in production
from fastapi.exceptions import RequestValidationError
import uuid as uuid_module

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    if settings.is_production:
        error_id = str(uuid_module.uuid4())[:8]
        logger.warning(f"Validation error [{error_id}]: {exc}")
        return JSONResponse(
            status_code=422,
            content={"detail": f"Invalid request data. Reference: {error_id}"}
        )
    else:
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    error_id = str(uuid_module.uuid4())[:8]
    error_trace = tb_module.format_exc()
    error_msg = f"GLOBAL ERROR [{error_id}]: {exc}\n{error_trace}"
    logger.error(error_msg)
    
    # Log to a size-bounded rotating file for debugging (never unbounded).
    if _error_file_logger is not None:
        try:
            _error_file_logger.error(
                "%s\nTIMESTAMP: %s\nURL: %s\n%s\n%s",
                "=" * 40,
                datetime.now(timezone.utc),
                request.url,
                error_msg,
                "=" * 40,
            )
        except Exception:
            pass

    # SECURITY: Never expose tracebacks or internal details to clients in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later.", "reference": error_id}
        )
    else:
        # Development mode — show details for debugging
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": error_trace}
        )


@app.get("/health", tags=["Health"])
# 120/minute, not 20. This endpoint is what keeps the container alive: the
# compose healthcheck polls it every 15s, and any orchestrator (k8s liveness +
# readiness at 10s each), load balancer, or uptime monitor adds more. At 20/min
# those probes collectively trip the limit, /health starts returning 429, and
# the orchestrator kills a container that is in fact perfectly healthy — a
# self-inflicted outage that gets worse under load. The limit is kept (rather
# than removed) because this handler does touch Postgres and Redis, so it
# should not be an unbounded anonymous amplifier.
@limiter.limit("120/minute")
async def health(request: Request):
    from app.database.db import check_db_connection
    from app.core.redis_client import redis_client

    db_ok = await check_db_connection()

    # redis-py's client is synchronous, so ping() blocks the calling thread on a
    # socket round-trip. Called inline it blocked the event loop — and the case
    # that matters is precisely the one where Redis is unhealthy: a hung server
    # stalls every concurrent request (including live SSE streams) until the
    # socket times out, turning a degraded dependency into a full outage of the
    # very endpoint meant to report it. Offloaded, a slow ping costs one worker
    # thread and still reports "degraded".
    def _ping() -> bool:
        try:
            return bool(redis_client.ping())
        except Exception:
            return False

    redis_ok = await asyncio.to_thread(_ping)

    status = "ok" if (db_ok and redis_ok) else "degraded"

    return {
        "status": status,
        # Lets a deploy be identified without shelling into the container, and
        # gives the frontend's About row something authoritative to compare its
        # own bundled version against.
        "version": settings.APP_VERSION,
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
        "timestamp": datetime.now(timezone.utc)
    }


from app.api import auth, chat, code_agent, rag, image, admin, ws_code, ws_agent, voice, snippets, settings as settings_api, api_keys, admin_governance, admin_security, admin_zero_trust, metrics, organizations, proxy, ws_broadcast, system, research, thinking, subscriptions, web_search, legal, projects, reports, mfa, notifications, connectors, oauth_github, group_chat, group_messages, ws_groups, family, project_sharing, platform_profile, code_sessions
# Admin console surface: staff management, real analytics, the unified audit
# trail and the read-only data explorer.
from app.api import admin_staff, admin_analytics, admin_audit_api, admin_explorer, admin_database, admin_coupons, admin_safety

# --- API v1 Router Registration (versioned endpoints) ---
# All REST API routes are prefixed with /api/v1 for professional versioning
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(legal.router, prefix=API_V1_PREFIX)
app.include_router(chat.router, prefix=API_V1_PREFIX)
app.include_router(projects.router, prefix=API_V1_PREFIX)
app.include_router(project_sharing.router, prefix=API_V1_PREFIX)
app.include_router(reports.router, prefix=API_V1_PREFIX)
app.include_router(notifications.router, prefix=API_V1_PREFIX)
app.include_router(connectors.router, prefix=API_V1_PREFIX)
app.include_router(oauth_github.router, prefix=API_V1_PREFIX)
app.include_router(group_chat.router, prefix=API_V1_PREFIX)
app.include_router(group_messages.router, prefix=API_V1_PREFIX)
app.include_router(family.router, prefix=API_V1_PREFIX)
app.include_router(mfa.router, prefix=API_V1_PREFIX)
app.include_router(mfa.security_router, prefix=API_V1_PREFIX)
app.include_router(rag.router, prefix=API_V1_PREFIX)
app.include_router(code_agent.router, prefix=API_V1_PREFIX)
app.include_router(image.router, prefix=API_V1_PREFIX)
app.include_router(voice.router, prefix=API_V1_PREFIX)
app.include_router(snippets.router, prefix=API_V1_PREFIX)
app.include_router(settings_api.router, prefix=API_V1_PREFIX)
app.include_router(api_keys.router, prefix=API_V1_PREFIX)
app.include_router(proxy.router, prefix=API_V1_PREFIX)
app.include_router(research.router, prefix=API_V1_PREFIX)
app.include_router(thinking.router, prefix=API_V1_PREFIX)
app.include_router(subscriptions.router, prefix=API_V1_PREFIX)
app.include_router(web_search.router, prefix=API_V1_PREFIX)

# Admin & Security routes (versioned)
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(admin_governance.router, prefix=API_V1_PREFIX)
app.include_router(platform_profile.router, prefix=API_V1_PREFIX)
app.include_router(code_sessions.router, prefix=API_V1_PREFIX)
app.include_router(admin_security.router, prefix=API_V1_PREFIX)
app.include_router(admin_zero_trust.router, prefix=API_V1_PREFIX)
app.include_router(admin_staff.router, prefix=API_V1_PREFIX)
app.include_router(admin_analytics.router, prefix=API_V1_PREFIX)
app.include_router(admin_audit_api.router, prefix=API_V1_PREFIX)
app.include_router(admin_explorer.router, prefix=API_V1_PREFIX)
app.include_router(admin_database.router, prefix=API_V1_PREFIX)
app.include_router(admin_coupons.router, prefix=API_V1_PREFIX)
app.include_router(admin_safety.router, prefix=API_V1_PREFIX)
app.include_router(metrics.router, prefix=API_V1_PREFIX)
app.include_router(organizations.router, prefix=API_V1_PREFIX)
app.include_router(system.router, prefix=API_V1_PREFIX)
# ws_broadcast carries the HTTP announcement/maintenance endpoints alongside its
# socket. It was mounted at root only, so `/api/v1/platform/status` — the read
# the product uses to find out why it is being 503'd — did not exist. The socket
# route inside is unaffected by the prefix; clients connect to the root one.
app.include_router(ws_broadcast.router, prefix=API_V1_PREFIX)

# --- Backward-Compatible Legacy Routes (no prefix) ---
# INTENTIONAL dual registration: Frontend-New calls the versioned /api/v1
# routes, while admin-frontend and the legacy frontend call these unprefixed
# routes. Both mount the same router objects, so there is no duplicated logic —
# only two URL surfaces. Do not remove until both older frontends migrate to
# /api/v1, or their requests will 404.
app.include_router(auth.router)
app.include_router(legal.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(project_sharing.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(connectors.router)
app.include_router(oauth_github.router)
app.include_router(group_chat.router)
app.include_router(group_messages.router)
app.include_router(family.router)
app.include_router(mfa.router)
app.include_router(mfa.security_router)
app.include_router(admin.router)
app.include_router(admin_governance.router)
app.include_router(platform_profile.router)
app.include_router(code_sessions.router)
app.include_router(admin_security.router)
app.include_router(admin_zero_trust.router)
app.include_router(admin_staff.router)
app.include_router(admin_analytics.router)
app.include_router(admin_audit_api.router)
app.include_router(admin_explorer.router)
app.include_router(admin_database.router)
app.include_router(admin_coupons.router)
app.include_router(admin_safety.router)
app.include_router(metrics.router)
app.include_router(organizations.router)
app.include_router(rag.router)
app.include_router(code_agent.router)
app.include_router(image.router)
app.include_router(voice.router)
app.include_router(snippets.router)
app.include_router(settings_api.router)
app.include_router(api_keys.router)
app.include_router(proxy.router)
app.include_router(research.router)
app.include_router(thinking.router)
app.include_router(subscriptions.router)
app.include_router(system.router)
app.include_router(web_search.router)

# WebSocket routes stay at root (WS connections don't use versioned paths)
app.include_router(ws_code.router)
app.include_router(ws_agent.router)
app.include_router(ws_broadcast.router)
app.include_router(ws_groups.router)


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
# reload

# reload
