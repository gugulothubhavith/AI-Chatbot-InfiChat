from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    PROJECT_NAME: str = "InfiChat"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 10080)) # Default to 7 days
    
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
    CODER_MODEL: str = os.getenv("CODER_MODEL", "deepseek/deepseek-chat")
    REVIEWER_API_KEY: Optional[str] = os.getenv("REVIEWER_API_KEY")
    REVIEWER_MODEL: str = "gemini-1.5-flash"
    
    # Email SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = os.getenv("SMTP_USER", "aichatbotclgproject@gmail.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "CHANGE_ME")

settings = Settings()