from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
import base64
import hashlib
import os
from typing import Optional, List


# ═══════════════════════════════════════════════════════════════════════
# COMPROMISED SECRETS — REJECTED IN PRODUCTION
# ═══════════════════════════════════════════════════════════════════════
# These values were committed to git history as source defaults and must be
# treated as public knowledge. Anyone with repository access can derive them,
# so they are refused whenever ENVIRONMENT=production. Rotate with
# `python -m scripts.rotate_keys --help` before deploying.
LEAKED_SECRETS: frozenset[str] = frozenset({
    "dev-secret-key-change-in-prod",
    "pmaibSwQbMbn_mABfYvYPGF-jTod7Wk1bXfMm-Q3muQ=",
    "FwD6i249jOhYhSDB8aXvA-c4e9A8H8bFzL1h9_N0lQo=",
    "change-me",
    "changeme",
    "secret",
})

# Minimum entropy we accept for a production signing/encryption secret.
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    PROJECT_NAME: str = "InfiChat"

    # --- Security & Environment ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # "development" or "production"
    # No default: production boots only when this is supplied via the
    # environment. Development falls back in the validator below.
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # 1 hour default
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))  # 7 days default

    # Refresh-token cookie. The refresh token is delivered as an httpOnly cookie
    # so JavaScript (and therefore XSS) cannot read it. Secure is forced on in
    # production; SameSite=lax works for same-site and top-level navigations.
    # Set REFRESH_COOKIE_DOMAIN when the API and app are on different subdomains
    # of the same site (e.g. api.example.com + app.example.com → ".example.com").
    REFRESH_COOKIE_NAME: str = os.getenv("REFRESH_COOKIE_NAME", "infichat_rt")
    REFRESH_COOKIE_SAMESITE: str = os.getenv("REFRESH_COOKIE_SAMESITE", "lax")
    REFRESH_COOKIE_DOMAIN: str = os.getenv("REFRESH_COOKIE_DOMAIN", "")

    # CORS & Hosts
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:3000,http://localhost:8080")
    ALLOWED_HOSTS: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")

    # Reverse-proxy awareness. Rate limiting and audit logging read the client
    # IP from X-Forwarded-For ONLY when the immediate peer is listed here —
    # otherwise any client could spoof the header to evade per-IP limits.
    TRUSTED_PROXY_IPS: str = os.getenv("TRUSTED_PROXY_IPS", "")

    # E2E Encryption (Fernet passphrase; PBKDF2-derived in app/core/encryption.py)
    # No default — see LEAKED_SECRETS above. Changing this makes previously
    # encrypted rows unreadable unless you migrate them with scripts/rotate_keys.py.
    E2E_ENCRYPTION_KEY: str = os.getenv("E2E_ENCRYPTION_KEY", "")

    # RAG Encryption (Must be 32 url-safe base64-encoded bytes for Fernet)
    RAG_ENCRYPTION_KEY: str = os.getenv("RAG_ENCRYPTION_KEY", "")


    # MFA Settings
    TOTP_ISSUER_NAME: str = os.getenv("TOTP_ISSUER_NAME", "InfiChat")

    # Infrastructure Security: IP Whitelisting & Origin Shields
    ADMIN_WHITELIST_IPS: str = os.getenv("ADMIN_WHITELIST_IPS", "127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12")
    CLOUDFLARE_ORIGIN_SECRET: str = os.getenv("CLOUDFLARE_ORIGIN_SECRET", "")  # If set, all traffic must contain this secret header

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT.lower() in ("test", "testing")

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]

    @property
    def trusted_proxy_ips(self) -> List[str]:
        return [ip.strip() for ip in self.TRUSTED_PROXY_IPS.split(",") if ip.strip()]

    @model_validator(mode="after")
    def _default_task_models_to_chat_model(self) -> "Settings":
        """Any blank task-specific model falls back to the chat model.

        There is one model choice in this product — the picker in the UI — and
        callers pass it down. These settings exist only for internal jobs with
        no user in the loop, so leaving them unset in the environment is the
        normal case, not a misconfiguration.

        This also removes a whole class of outage: each used to carry its own
        hardcoded id, and one of them (`llama-3_3-nemotron-super-49b-v1_5`) did
        not exist on the endpoint, so every call 404'd after ~14s of key-pool
        retries. Memory extraction runs on every chat turn, so that was ~14s
        added to every message for a background job that then failed anyway.
        """
        for field in (
            "FAST_MODEL",
            "REASONING_MODEL",
            "MEMORY_EXTRACTOR_MODEL",
            "WEB_SEARCH_MODEL",
            "PLANNER_MODEL",
            "CODER_MODEL",
            "DEEP_RESEARCH_DEFAULT_MODEL",
            "DEEP_RESEARCH_FAST_LOOP_MODEL",
        ):
            if not (getattr(self, field, "") or "").strip():
                object.__setattr__(self, field, self.DEFAULT_CHAT_MODEL)
        return self

    @model_validator(mode="after")
    def _enforce_production_secrets(self) -> "Settings":
        """Refuse to start a production deployment on weak or leaked secrets.

        Fails closed: a misconfigured production instance must not boot with
        forgeable JWTs or publicly-known encryption keys. In development the
        same fields fall back to clearly-marked ephemeral values.
        """
        secret_fields = ("SECRET_KEY", "E2E_ENCRYPTION_KEY", "RAG_ENCRYPTION_KEY")

        if not self.is_production:
            # Development convenience: synthesize deterministic placeholders so
            # a fresh clone runs without reusing the leaked literals. The
            # encryption keys must be *valid Fernet keys* (32 url-safe base64
            # bytes) because models/utils.py feeds them straight to Fernet().
            # Deterministic (not random) so dev data stays readable across
            # restarts.
            for field in secret_fields:
                if getattr(self, field):
                    continue
                if field.endswith("_ENCRYPTION_KEY"):
                    seed = hashlib.sha256(f"infichat-dev-only-{field}".encode()).digest()
                    placeholder = base64.urlsafe_b64encode(seed).decode()
                else:
                    placeholder = "dev-only-insecure-" + "x" * MIN_SECRET_LENGTH
                object.__setattr__(self, field, placeholder)
            return self

        problems: List[str] = []
        for field in secret_fields:
            value = (getattr(self, field) or "").strip()
            if not value:
                problems.append(f"{field} is not set")
            elif value in LEAKED_SECRETS:
                problems.append(
                    f"{field} matches a value published in git history and is permanently compromised"
                )
            elif len(value) < MIN_SECRET_LENGTH:
                problems.append(
                    f"{field} is only {len(value)} chars; needs >= {MIN_SECRET_LENGTH}"
                )

        # A wildcard origin combined with credentialed CORS lets any site read
        # authenticated responses.
        if "*" in self.cors_origins:
            problems.append("ALLOWED_ORIGINS must not contain '*' when credentials are allowed")

        if problems:
            raise ValueError(
                "Refusing to start in production due to insecure configuration:\n"
                + "\n".join(f"  - {p}" for p in problems)
                + "\n\nGenerate strong values with:\n"
                '  python -c "import secrets; print(secrets.token_urlsafe(48))"   # SECRET_KEY\n'
                '  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
                "   # *_ENCRYPTION_KEY\n"
                "Then migrate existing encrypted rows with backend/scripts/rotate_keys.py "
                "before switching keys."
            )
        return self

    # --- Application version ---
    # Single source for the backend; keep in step with the three package.json
    # files and Frontend-New/src/lib/version.ts. Distinct from the two legal
    # versions below, which version the *documents* — bumping one of those
    # forces every user through re-consent.
    APP_VERSION: str = "0.1.0"

    # --- Legal document versions (match frontmatter in Frontend-New/src/content/legal/*.md) ---
    #
    # Bumped to 1.1.0 for image-history and token-metering. Both introduced new
    # categories of processing that the previous version did not disclose:
    # generated images and their prompts are now *stored on our servers* rather
    # than existing only in the response, and per-request token counts are now
    # recorded. New categories of personal data are a material change, so this
    # deliberately forces every existing user through re-consent rather than
    # relying on continued use to imply agreement.
    CURRENT_TERMS_VERSION: str = "1.1.0"
    CURRENT_PRIVACY_VERSION: str = "1.1.0"

    # --- Database & Cache ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # --- Vector store (Chroma) ---
    EMBEDDINGS_MODEL: str = "BAAI/bge-small-en-v1.5"
    # Accepts a full URL, or is derived from CHROMA_HOST/CHROMA_PORT when those
    # are supplied instead (docker-compose sets the host/port pair).
    CHROMA_URL: str = os.getenv("CHROMA_URL", "")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

    @property
    def chroma_endpoint(self) -> str:
        """Resolve the Chroma endpoint from either CHROMA_URL or CHROMA_HOST/PORT."""
        if self.CHROMA_URL:
            return self.CHROMA_URL.rstrip("/")
        if self.CHROMA_HOST:
            return f"http://{self.CHROMA_HOST}:{self.CHROMA_PORT}"
        return "http://localhost:8001"

    # --- External services ---
    SEARXNG_URL: str = os.getenv("SEARXNG_URL", "http://localhost:8080")
    UNSTRUCTURED_URL: str = os.getenv("UNSTRUCTURED_URL", "")

    # --- Image generation & storage ---
    # Where generated images live on disk. Must be a mounted volume in Docker:
    # the default sits inside the container filesystem, so without a volume
    # every image in a user's gallery disappears on the next `docker compose up
    # --build` while the database rows survive — a gallery of broken tiles,
    # which is worse than no gallery. See the `backend_images` volume in
    # docker-compose.yml.
    IMAGE_STORAGE_DIR: str = os.getenv("IMAGE_STORAGE_DIR", "/data/images")
    IMAGE_PROVIDER_URL: str = os.getenv(
        "IMAGE_PROVIDER_URL", "https://image.pollinations.ai"
    )
    # Generous, because diffusion is slow: a 1024×1024 render regularly takes
    # 30-40s and a shorter timeout turns a working request into a placeholder.
    IMAGE_GENERATION_TIMEOUT: float = float(
        os.getenv("IMAGE_GENERATION_TIMEOUT", "90")
    )
    # How long a soft-deleted image is recoverable before the retention sweep
    # removes the row and unlinks the file.
    IMAGE_PURGE_AFTER_DAYS: int = int(os.getenv("IMAGE_PURGE_AFTER_DAYS", "30"))

    # --- Sandbox (code execution) ---
    SANDBOX_IMAGE: str = os.getenv("SANDBOX_IMAGE", "infichat-sandbox:latest")
    SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "30"))
    SANDBOX_MAX_MEMORY: str = os.getenv("SANDBOX_MAX_MEMORY", "512M")
    # Run submitted code as a plain subprocess when Docker is unreachable.
    #
    # Off by default, and refused outright in production. That fallback executes
    # user-supplied Python *inside the backend container* — same filesystem,
    # same network, and an environment holding SECRET_KEY, DATABASE_URL and
    # every provider API key. The AST denylist in core/security.py is not a
    # substitute for isolation: `importlib.import_module("os")`, `builtins.exec`
    # and `runpy` all pass it. Opt in only on a throwaway dev box.
    SANDBOX_ALLOW_UNISOLATED: bool = os.getenv("SANDBOX_ALLOW_UNISOLATED", "false").lower() in ("1", "true", "yes")

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- OAuth ---
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")

    # ═══════════════════════════════════════════════════════════════════
    # NVIDIA NIM API KEY POOL
    # ═══════════════════════════════════════════════════════════════════
    # Every agent shares this pool via app/services/key_pool.py, which pins
    # each logical agent to its own key so concurrent pipeline stages never
    # contend for the same quota. Add or remove keys freely.
    NVIDIA_API_KEY_1: str = os.getenv("NVIDIA_API_KEY_1", "")
    NVIDIA_API_KEY_2: str = os.getenv("NVIDIA_API_KEY_2", "")
    NVIDIA_API_KEY_3: str = os.getenv("NVIDIA_API_KEY_3", "")
    NVIDIA_API_KEY_4: str = os.getenv("NVIDIA_API_KEY_4", "")

    # Legacy single-key names — still honoured so an older .env keeps working.
    DEFAULT_CHAT_API_KEY: str = os.getenv("DEFAULT_CHAT_API_KEY", "")
    PLANNER_API_KEY: Optional[str] = os.getenv("PLANNER_API_KEY")
    CODER_API_KEY: Optional[str] = os.getenv("CODER_API_KEY")

    @property
    def nvidia_api_keys(self) -> List[str]:
        """Ordered, de-duplicated list of every configured NVIDIA key.

        Numbered keys come first (NVIDIA_API_KEY_1..4), then any legacy
        single-purpose keys, so an existing deployment keeps working without
        edits while new deployments get the full pool.
        """
        candidates = [
            self.NVIDIA_API_KEY_1,
            self.NVIDIA_API_KEY_2,
            self.NVIDIA_API_KEY_3,
            self.NVIDIA_API_KEY_4,
            self.DEFAULT_CHAT_API_KEY,
            self.PLANNER_API_KEY or "",
            self.CODER_API_KEY or "",
        ]
        seen: set = set()
        keys: List[str] = []
        for candidate in candidates:
            candidate = (candidate or "").strip()
            if candidate and candidate not in seen:
                seen.add(candidate)
                keys.append(candidate)
        return keys

    @property
    def primary_api_key(self) -> str:
        """First key in the pool — used for non-pooled one-off calls."""
        keys = self.nvidia_api_keys
        return keys[0] if keys else ""

    # ═══════════════════════════════════════════════════════════════════
    # MODELS (all NVIDIA NIM)
    # ═══════════════════════════════════════════════════════════════════
    # Verified against GET /v1/models on this endpoint, not assumed.
    #
    # The previous default, "nvidia/nemotron-3-ultra-550b-a55b", does not exist:
    # every completion 404'd, the key pool read four consecutive 404s as four
    # bad keys and put them all on a cooling backoff, and the user saw
    # "The server ran into a problem" from chat, deep thinking, deep research,
    # the code agent and web search alike — every feature routes through here.
    #
    # A 404 is not a key failure. Until the pool distinguishes the two, a wrong
    # model name disables the whole platform, so this value has to be checked
    # against the live model list rather than typed from memory.
    DEFAULT_CHAT_MODEL: str = os.getenv(
        "DEFAULT_CHAT_MODEL", "meta/llama-3.1-70b-instruct"
    )
    # Deep reasoning / synthesis — highest quality, slowest.
    REASONING_MODEL: str = os.getenv("REASONING_MODEL", "")
    # Utility models for classification, query generation and extraction.
    #
    # These used to default to "nvidia/llama-3_3-nemotron-super-49b-v1_5", which
    # **does not exist on this endpoint** — every call 404'd after 14.3s of the
    # key pool retrying all four keys. Memory extraction runs on *every* chat
    # turn, so that was ~14s of pure waste added to each message, and web search
    # and the deep-research fast loop failed outright.
    #
    # They now fall back to the main chat model. Callers should pass the model
    # the user selected in the UI instead of relying on these at all; the
    # fallback exists only for internal jobs with no user in the loop.
    FAST_MODEL: str = os.getenv("FAST_MODEL", "")
    MEMORY_EXTRACTOR_MODEL: str = os.getenv("MEMORY_EXTRACTOR_MODEL", "")
    WEB_SEARCH_MODEL: str = os.getenv("WEB_SEARCH_MODEL", "")

    # ═══════════════════════════════════════════════════════════════════
    # AUTO WEB SEARCH (intent-driven, unmetered)
    # ═══════════════════════════════════════════════════════════════════
    # Auto-search escalates a normal chat turn to grounded web search when the
    # prompt clearly needs fresh facts. It is intentionally NOT metered against
    # the user's plan (manual `/web_search/` still is). To stop it being abused
    # as a free bypass, auto-search is capped per user per day server-side.
    AUTO_WEB_SEARCH_ENABLED: bool = os.getenv("AUTO_WEB_SEARCH_ENABLED", "true").lower() == "true"
    # Cheap classifier model used only when heuristics are ambiguous.
    AUTO_WEB_SEARCH_CLASSIFIER_MODEL: str = os.getenv(
        "AUTO_WEB_SEARCH_CLASSIFIER_MODEL", FAST_MODEL
    )
    # Abuse ceiling: max auto-triggered searches per user per rolling day.
    AUTO_WEB_SEARCH_DAILY_CAP: int = int(os.getenv("AUTO_WEB_SEARCH_DAILY_CAP", "50"))
    # Redis TTL (seconds) for cached intent classifications keyed by prompt hash.
    AUTO_WEB_SEARCH_INTENT_CACHE_TTL: int = int(
        os.getenv("AUTO_WEB_SEARCH_INTENT_CACHE_TTL", "86400")
    )

    DEEP_RESEARCH_DEFAULT_MODEL: str = os.getenv("DEEP_RESEARCH_DEFAULT_MODEL", "")
    DEEP_RESEARCH_FAST_LOOP_MODEL: str = os.getenv("DEEP_RESEARCH_FAST_LOOP_MODEL", "")

    # Multi-Agent Coding System
    PLANNER_MODEL: str = os.getenv("PLANNER_MODEL", "")
    CODER_MODEL: str = os.getenv("CODER_MODEL", "")

    # Image Generation (NVIDIA NIM)
    IMAGE_GENERATION_MODEL: str = os.getenv("IMAGE_GENERATION_MODEL", "black-forest-labs/flux-1-schnell")

    # Vision — reading an image rather than making one.
    #
    # Used to turn a screenshot or diagram into text that can live permanently
    # in a project's knowledge base. Optional: when this is unset or the model
    # is unreachable, image ingestion falls back to OCR alone and says so on the
    # file rather than pretending it understood the picture.
    # The 90b variant is listed but consistently timed out on this account; the
    # 11b answered in 0.3s. Vision here turns a screenshot into text for a
    # knowledge base, which is a background job — a model that returns beats a
    # larger one that does not.
    VISION_MODEL: str = os.getenv("VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")

    # --- Voyage AI (RAG embeddings + reranking) ---
    VOYAGE_API_KEY: Optional[str] = os.getenv("VOYAGE_API_KEY")
    VOYAGE_EMBEDDING_MODEL: str = os.getenv("VOYAGE_EMBEDDING_MODEL", "voyage-3")
    VOYAGE_RERANK_MODEL: str = os.getenv("VOYAGE_RERANK_MODEL", "rerank-2.5")

    # --- Voice: STT is fully local (faster-whisper), TTS via Edge-TTS ---
    WHISPER_MODEL_SIZE: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    UNREAL_SPEECH_API_KEY: Optional[str] = os.getenv("UNREAL_SPEECH_API_KEY")
    UNREAL_SPEECH_VOICE: str = os.getenv("UNREAL_SPEECH_VOICE", "Sierra")

    # --- Billing & Stripe ---
    STRIPE_SECRET_KEY: Optional[str] = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = os.getenv("STRIPE_WEBHOOK_SECRET")

    # --- Email SMTP ---
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    # --- Web Push (VAPID) ---
    # Generate with `python -m app.scripts.generate_vapid`. The public key is
    # handed to browsers and is not a secret; the private key signs the push
    # request and is. Both empty means push is *disabled*, not broken — the API
    # says so rather than letting the UI offer a switch that cannot work.
    VAPID_PUBLIC_KEY: str = os.getenv("VAPID_PUBLIC_KEY", "")
    VAPID_PRIVATE_KEY: str = os.getenv("VAPID_PRIVATE_KEY", "")
    # Contact address push services use to reach an operator about a
    # misbehaving sender. Must be a mailto: or https: URL per RFC 8292.
    VAPID_SUBJECT: str = os.getenv("VAPID_SUBJECT", "mailto:support@infichat.app")

    # --- Connectors (Phase 6) ---
    # Encrypts third-party OAuth tokens at rest. Empty disables connectors
    # entirely rather than storing bearer credentials for someone else's Gmail
    # in the clear. Rotating it makes existing connections unreadable — they
    # move to NEEDS_REAUTH and the user reconnects.
    CONNECTOR_ENCRYPTION_KEY: str = os.getenv("CONNECTOR_ENCRYPTION_KEY", "")
    # Absolute origin the OAuth callback returns to. Must match what is
    # registered with each provider exactly, including scheme and port.
    PUBLIC_BASE_URL: str = os.getenv("PUBLIC_BASE_URL", "http://localhost:5173")
    # Where the user lands after the callback finishes.
    # Settings is a dialog, not a route — there is no /settings URL. The app
    # shell turns `?settings=connectors` on a real route into an open dialog.
    CONNECTOR_SUCCESS_PATH: str = os.getenv("CONNECTOR_SUCCESS_PATH", "/chat?settings=connectors")

    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    # GOOGLE_CLIENT_ID is declared above for Google *sign-in*, which verifies an
    # ID token's signature and audience — that needs the public client id only,
    # which is why no secret was ever configured for it.
    #
    # The Drive/Gmail/Calendar connector reuses the same client but runs the
    # authorization-code flow, whose token exchange *is* authenticated with the
    # secret. So this is a genuinely new requirement, not a duplicate: the same
    # OAuth client in the Google Cloud Console already has a secret, it simply
    # was never needed until now.
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    SLACK_CLIENT_ID: str = os.getenv("SLACK_CLIENT_ID", "")
    SLACK_CLIENT_SECRET: str = os.getenv("SLACK_CLIENT_SECRET", "")
    NOTION_CLIENT_ID: str = os.getenv("NOTION_CLIENT_ID", "")
    NOTION_CLIENT_SECRET: str = os.getenv("NOTION_CLIENT_SECRET", "")


settings = Settings()
