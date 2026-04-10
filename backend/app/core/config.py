from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional, List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    PROJECT_NAME: str = "InfiChat"
    
    # --- Security & Environment ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # "development" or "production"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))  # 1 hour default
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))  # 7 days default
    
    # CORS & Hosts
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:3000,http://localhost:8080")
    ALLOWED_HOSTS: str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    
    # E2E Encryption (Must be 32 url-safe base64-encoded bytes for Fernet)
    E2E_ENCRYPTION_KEY: str = os.getenv("E2E_ENCRYPTION_KEY", "pmaibSwQbMbn_mABfYvYPGF-jTod7Wk1bXfMm-Q3muQ=")
    
    # RAG Encryption (Must be 32 url-safe base64-encoded bytes for Fernet)
    RAG_ENCRYPTION_KEY: str = os.getenv("RAG_ENCRYPTION_KEY", "FwD6i249jOhYhSDB8aXvA-c4e9A8H8bFzL1h9_N0lQo=")
    
    # MFA Settings
    TOTP_ISSUER_NAME: str = os.getenv("TOTP_ISSUER_NAME", "InfiChat")
    
    # Infrastructure Security: IP Whitelisting & Origin Shields
    ADMIN_WHITELIST_IPS: str = os.getenv("ADMIN_WHITELIST_IPS", "127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12")
    CLOUDFLARE_ORIGIN_SECRET: str = os.getenv("CLOUDFLARE_ORIGIN_SECRET", "") # If set, all traffic must contain this secret header
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    @property
    def trusted_hosts(self) -> List[str]:
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",") if host.strip()]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://ai:ai_pass@postgres:5432/autoagent")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Model servers
    LLAMA3_70B_URL: str = "http://ai-llama3-70b:8000/v1/chat/completions"
    LLAMA3_8B_URL: str = "http://ai-llama3-8b:8000/v1/chat/completions"
    CODE_LLAMA_34B_URL: str = "http://ai-code-llama-34b:8000/v1/completions"
    CODE_LLAMA_13B_URL: str = "http://ai-code-llama-13b:8000"
    MIXTRAL_URL: str = "http://ai-mixtral:8000/v1/chat/completions"
    SDXL_URL: str = "http://ai-sdxl:7860"
    
    # Embeddings
    EMBEDDINGS_MODEL: str = "BAAI/bge-small-en-v1.5"
    CHROMA_URL: str = "http://ai-chromadb:8000"
    
    # Sandbox
    SANDBOX_IMAGE: str = "infichat-sandbox:latest"
    SANDBOX_TIMEOUT: int = 30
    SANDBOX_MAX_MEMORY: str = "512M"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    
    # Groq
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Voyage AI
    VOYAGE_API_KEY: Optional[str] = os.getenv("VOYAGE_API_KEY")
    VOYAGE_EMBEDDING_MODEL: str = os.getenv("VOYAGE_EMBEDDING_MODEL", "voyage-3")
    VOYAGE_RERANK_MODEL: str = os.getenv("VOYAGE_RERANK_MODEL", "rerank-2.5")
    
    # Hugging Face Inference API (Image Generation)
    HUGGINGFACE_API_KEY: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    HUGGINGFACE_IMAGE_MODEL: str = os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    
    # Gemini / Google AI
    GOOGLE_API_KEY: Optional[str] = None
    VISION_MODEL: str = "gemini-1.5-flash"
    
    # Voice (STT & TTS)
    GROQ_STT_API_KEY: Optional[str] = os.getenv("GROQ_STT_API_KEY")
    GROQ_STT_MODEL: str = os.getenv("GROQ_STT_MODEL", "whisper-large-v3")
    UNREAL_SPEECH_API_KEY: Optional[str] = os.getenv("UNREAL_SPEECH_API_KEY")
    UNREAL_SPEECH_VOICE: str = os.getenv("UNREAL_SPEECH_VOICE", "Sierra")
    
    # Multi-Agent System
    PLANNER_API_KEY: Optional[str] = os.getenv("PLANNER_API_KEY")
    PLANNER_MODEL: str = os.getenv("PLANNER_MODEL", "llama-3.3-70b-versatile")
    CODER_API_KEY: Optional[str] = os.getenv("CODER_API_KEY")
    CODER_MODEL: str = os.getenv("CODER_MODEL", "bigcode/starcoder2-7b")
    REVIEWER_API_KEY: Optional[str] = os.getenv("REVIEWER_API_KEY")
    REVIEWER_MODEL: str = os.getenv("REVIEWER_MODEL", "bigcode/starcoder2-7b")
    
    # Email SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = os.getenv("SMTP_USER", "aichatbotclgproject@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "CHANGE_ME")

settings = Settings()