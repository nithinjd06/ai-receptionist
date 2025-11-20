"""
Configuration management using Pydantic Settings.
All secrets and toggles loaded from environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings with sensible defaults for production."""
    
    # App
    APP_NAME: str = "AI Receptionist"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Public URL (for Twilio webhooks)
    PUBLIC_URL: str = Field(..., description="Public URL for Twilio callbacks, e.g. https://yourdomain.com")
    
    # Twilio
    TWILIO_ACCOUNT_SID: str = Field(..., description="Twilio Account SID")
    TWILIO_AUTH_TOKEN: str = Field(..., description="Twilio Auth Token")
    TWILIO_PHONE_NUMBER: str = Field(..., description="Your Twilio phone number")
    TWILIO_VERIFY_SIGNATURE: bool = True
    
    # Feature flags & provider selection
    FEATURE_STT_PROVIDER: Literal["deepgram", "whisper"] = "deepgram"
    FEATURE_TTS_PROVIDER: Literal["elevenlabs"] = "elevenlabs"
    FEATURE_LLM_PROVIDER: Literal["openai", "anthropic", "gemini"] = "gemini"
    FEATURE_SCHEDULER: Literal["google", "calendly", "none"] = "google"
    FEATURE_EHR_ATHENA: bool = False
    
    # Deepgram
    DEEPGRAM_API_KEY: str = ""
    DEEPGRAM_MODEL: str = "nova-2"
    DEEPGRAM_LANGUAGE: str = "en-US"
    
    # Whisper (local or API)
    WHISPER_MODEL: str = "base"
    WHISPER_API_KEY: str = ""  # If using OpenAI Whisper API
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 500
    OPENAI_TIMEOUT_S: float = 10.0
    
    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    ANTHROPIC_TEMPERATURE: float = 0.7
    ANTHROPIC_MAX_TOKENS: int = 500
    ANTHROPIC_TIMEOUT_S: float = 10.0
    
    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 500
    GEMINI_TIMEOUT_S: float = 10.0
    
    # ElevenLabs
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
    ELEVENLABS_MODEL: str = "eleven_turbo_v2_5"
    ELEVENLABS_STABILITY: float = 0.5
    ELEVENLABS_SIMILARITY_BOOST: float = 0.75
    
    # Google Calendar
    GOOGLE_CALENDAR_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_CALENDAR_TOKEN_FILE: str = "token.json"
    GOOGLE_CALENDAR_ID: str = "primary"
    GOOGLE_CALENDAR_TIMEZONE: str = "America/Chicago"
    
    # Calendly
    CALENDLY_API_KEY: str = ""
    CALENDLY_USER_URI: str = ""
    
    # Athena Health (EHR)
    ATHENA_CLIENT_ID: str = ""
    ATHENA_CLIENT_SECRET: str = ""
    ATHENA_PRACTICE_ID: str = ""
    ATHENA_BASE_URL: str = "https://api.athenahealth.com/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/receptionist.db"
    DATABASE_ECHO: bool = False
    
    # Redis (optional)
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Audio processing
    AUDIO_SAMPLE_RATE: int = 8000  # Twilio uses 8kHz
    AUDIO_CHANNELS: int = 1
    AUDIO_CHUNK_DURATION_MS: int = 300  # Collect audio in 300ms chunks
    AUDIO_ENCODING: str = "mulaw"  # Twilio default
    
    # Latency & timeouts
    STT_TIMEOUT_S: float = 5.0
    TTS_TIMEOUT_S: float = 5.0
    LLM_TIMEOUT_S: float = 10.0
    CALENDAR_API_TIMEOUT_S: float = 5.0
    
    # Conversation settings
    MAX_CONVERSATION_TURNS: int = 50
    MAX_FAILED_ASR_ATTEMPTS: int = 2
    SILENCE_TIMEOUT_S: float = 3.0
    BARGE_IN_ENABLED: bool = True
    
    # Business hours (24h format, local timezone)
    BUSINESS_HOURS_START: str = "08:00"
    BUSINESS_HOURS_END: str = "17:00"
    BUSINESS_DAYS: str = "1,2,3,4,5"  # Monday=1, Sunday=7
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = Field(..., description="Admin password for protected endpoints")
    
    # Observability
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: Literal["json", "text"] = "json"
    METRICS_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

