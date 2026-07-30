"""
Security middleware, rate limiting, and code validation for InfiChat.
Production-ready security headers and request validation.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter
import hashlib
import logging
import secrets

from app.core.config import settings

logger = logging.getLogger(__name__)


# --- Rate limit key ---------------------------------------------------------
# The default slowapi key_func (get_remote_address) reads request.client.host,
# which behind a reverse proxy (nginx, Cloudflare) is the PROXY's IP — so every
# user collapses into a single bucket and the limits are meaningless. Worse,
# naively trusting X-Forwarded-For lets any client spoof the header to evade or
# frame others' limits.
#
# This key func fixes both:
#   * Authenticated callers are keyed on their identity (JWT subject or the
#     personal-access-token hash), so limits are genuinely per-user regardless
#     of source IP or NAT.
#   * Anonymous callers are keyed on their real IP, and X-Forwarded-For is
#     honoured ONLY when the immediate peer is a configured trusted proxy.
def _client_ip(request: Request) -> str:
    """Best-effort real client IP, trusting XFF only from known proxies."""
    peer = request.client.host if request.client else "127.0.0.1"
    trusted = settings.trusted_proxy_ips
    if trusted and peer in trusted:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Left-most entry is the originating client as recorded by our proxy.
            return forwarded.split(",")[0].strip() or peer
    return peer


def rate_limit_key(request: Request) -> str:
    """Per-caller rate-limit bucket key.

    Keys on authenticated identity when present, else on the proxy-aware
    client IP. Token decoding here is local and cheap (no DB); an unparseable
    token simply falls through to IP-based keying.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token.startswith("sk_infi_"):
            # Don't put the raw key in a bucket name; a stable hash prefix is
            # enough to isolate one API key from another.
            return "pat:" + hashlib.sha256(token.encode()).hexdigest()[:32]
        try:
            from app.core.auth import decode_token
            payload = decode_token(token)
            if payload and payload.get("sub"):
                return "user:" + str(payload["sub"])
        except Exception:
            pass
    return "ip:" + _client_ip(request)


# --- Rate Limiter ---
limiter = Limiter(key_func=rate_limit_key)

RATE_LIMITS = {
    "auth": "5/minute",
    "chat": "30/minute",
    "code_generate": "10/minute",
    "code_execute": "5/minute",
    "rag_upload": "10/hour",
    "image_generate": "10/minute",
}


# --- Security Headers Middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds production-grade security headers to every HTTP response.
    Follows OWASP Secure Headers Project recommendations.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate a unique nonce for this request
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Force HTTPS (HSTS) — 1 year with subdomains
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            # Allow Swagger UI resources for documentation
            response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: https:;"
        else:
            # Strict CSP for all other endpoints
            response.headers["Content-Security-Policy"] = (
                f"default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval'; "
                f"style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "img-src 'self' data: blob: https:; "
                "font-src 'self' https://fonts.gstatic.com; "
                "connect-src 'self' ws: wss: https:; "
                "media-src 'self' blob:; "
                "frame-ancestors 'none'"
            )


        # Referrer Policy — only send origin for cross-origin requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy — disable unnecessary browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # Prevent caching of sensitive responses
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response


import ast

# --- Code Safety Validation ---
def validate_code_safety(code: str, language: str) -> bool:
    """
    Advanced code validation using AST parsing for Python to prevent sandbox escapes,
    especially on bare-metal fallback execution environments.
    """
    if language != "python":
        # For non-python languages, rely on Docker container networking/restrictions
        dangerous_bash = ["rm -rf", "mkfs", "dd if=", ": (){:|: &};:"]
        dangerous_js = ["require('child_process')", "require('fs')"]
        
        patterns = dangerous_bash if language == "bash" else dangerous_js if language == "javascript" else []
        for pattern in patterns:
            if pattern.lower() in code.lower():
                logger.warning(f"Dangerous code pattern detected in {language}: {pattern}")
                return False
        return True

    class SecurityVisitor(ast.NodeVisitor):
        def __init__(self):
            # Extremely locked down by default as we have sensitive filesystem access
            self.safe = True
            self.blocked_modules = {'os', 'sys', 'subprocess', 'shutil', 'socket', 'pathlib', 'typing'}
            # eval, exec, and __import__ are universally blocked
            self.blocked_functions = {'eval', 'exec', 'open', 'compile', '__import__'}

        def visit_Import(self, node):
            for alias in node.names:
                if alias.name.split('.')[0] in self.blocked_modules:
                    logger.warning(f"AST Validator: Blocked direct import of {alias.name}")
                    self.safe = False
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            if node.module and node.module.split('.')[0] in self.blocked_modules:
                logger.warning(f"AST Validator: Blocked import-from of {node.module}")
                self.safe = False
            self.generic_visit(node)

        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id in self.blocked_functions:
                logger.warning(f"AST Validator: Blocked direct function call {node.func.id}")
                self.safe = False
            self.generic_visit(node)
            
        def visit_Attribute(self, node):
            # Block dunder methods (prevents sandbox escapes via '__subclasses__')
            if node.attr.startswith('__') and node.attr.endswith('__'):
                logger.warning(f"AST Validator: Blocked dunder attribute {node.attr}")
                self.safe = False
            self.generic_visit(node)

    try:
        tree = ast.parse(code)
        visitor = SecurityVisitor()
        visitor.visit(tree)
        return visitor.safe
    except SyntaxError:
        # If it doesn't parse, it's not a security threat, it's just invalid syntax.
        # Let the standard execution framework handle throwing the specific SyntaxError output.
        return True


# --- Sandbox Configuration ---
class SandboxConfig:
    """Sandbox execution configuration for code agent"""
    MAX_EXECUTION_TIME = 30  # seconds
    MAX_MEMORY = "512M"
    MAX_CPU_PERCENT = 80
    ENABLE_NETWORK = False
    ENABLE_GPU = False

    ALLOWED_MOUNTS = {
        "/tmp": "rw",
        "/app": "ro",
    }

    BLOCKED_SYSCALLS = [
        "socket", "setsockopt", "connect",
        "execve", "fork", "clone",
    ]