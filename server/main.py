"""
FastAPI main application.
Orchestrates all components: telephony, STT, TTS, LLM, database, etc.
"""
import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, WebSocket, HTTPException, Depends, Header
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from .config import settings
from .telephony_twilio import TwilioCallHandler, generate_twiml_response, verify_twilio_signature
from .stt import DeepgramSTT, WhisperSTT, STTProvider
from .tts import ElevenLabsTTS, TTSProvider
from .llm import OpenAIGPT4o, AnthropicClaude, GoogleGemini, LLMProvider
from .convo import ConversationRouter
from .scheduling import GoogleCalendarProvider, CalendlyProvider, CalendarProvider
from .db.repo import CallRepository, MessageRepository
from .utils import generate_id, set_request_id, get_request_id
from .utils.validation import sanitize_phone

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if settings.LOG_FORMAT == "text"
    else '{"timestamp":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
db_engine = None
async_session_maker = None
llm_provider: Optional[LLMProvider] = None
calendar_provider: Optional[CalendarProvider] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initialize and cleanup resources.
    """
    global db_engine, async_session_maker, llm_provider, calendar_provider
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    db_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        future=True,
    )
    
    async_session_maker = sessionmaker(
        db_engine,
        class_=SQLModelAsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with db_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    logger.info("Database initialized")
    
    # Initialize LLM provider
    if settings.FEATURE_LLM_PROVIDER == "openai":
        llm_provider = OpenAIGPT4o(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            timeout=settings.OPENAI_TIMEOUT_S,
        )
        logger.info("Initialized OpenAI GPT-4o LLM provider")
    
    elif settings.FEATURE_LLM_PROVIDER == "anthropic":
        llm_provider = AnthropicClaude(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            temperature=settings.ANTHROPIC_TEMPERATURE,
            max_tokens=settings.ANTHROPIC_MAX_TOKENS,
            timeout=settings.ANTHROPIC_TIMEOUT_S,
        )
        logger.info("Initialized Anthropic Claude LLM provider")
    
    elif settings.FEATURE_LLM_PROVIDER == "gemini":
        llm_provider = GoogleGemini(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            max_tokens=settings.GEMINI_MAX_TOKENS,
            timeout=settings.GEMINI_TIMEOUT_S,
        )
        logger.info("Initialized Google Gemini 2.5 Flash LLM provider")
    
    # Initialize calendar provider
    if settings.FEATURE_SCHEDULER == "google":
        calendar_provider = GoogleCalendarProvider(
            credentials_file=settings.GOOGLE_CALENDAR_CREDENTIALS_FILE,
            token_file=settings.GOOGLE_CALENDAR_TOKEN_FILE,
            calendar_id=settings.GOOGLE_CALENDAR_ID,
            timezone=settings.GOOGLE_CALENDAR_TIMEZONE,
        )
        logger.info("Initialized Google Calendar provider")
    
    elif settings.FEATURE_SCHEDULER == "calendly":
        calendar_provider = CalendlyProvider(
            api_key=settings.CALENDLY_API_KEY,
            user_uri=settings.CALENDLY_USER_URI,
        )
        logger.info("Initialized Calendly provider")
    
    logger.info("Application startup complete")
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")
    
    if db_engine:
        await db_engine.dispose()
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware for request ID and logging
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Add request ID and logging for all requests."""
    request_id = request.headers.get("X-Request-ID", generate_id())
    set_request_id(request_id)
    
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={"request_id": request_id},
    )
    
    response = await call_next(request)
    
    # Log response
    duration_ms = (time.time() - start_time) * 1000
    logger.info(
        f"Request completed: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - Duration: {duration_ms:.2f}ms",
        extra={"request_id": request_id, "duration_ms": duration_ms},
    )
    
    response.headers["X-Request-ID"] = request_id
    return response


# Dependency to get database session
async def get_session() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        yield session


# Health check endpoints
@app.get("/healthz")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/ready")
async def readiness_check(session: AsyncSession = Depends(get_session)):
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        await session.execute("SELECT 1")
        
        return {
            "status": "ready",
            "database": "connected",
            "llm_provider": settings.FEATURE_LLM_PROVIDER,
            "stt_provider": settings.FEATURE_STT_PROVIDER,
            "tts_provider": settings.FEATURE_TTS_PROVIDER,
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


# Twilio voice webhook endpoint
@app.post("/voice/incoming")
async def voice_incoming(request: Request):
    """
    Handle incoming Twilio voice call.
    Returns TwiML to establish Media Stream.
    """
    try:
        # Get request data
        form_data = await request.form()
        post_data = dict(form_data)
        
        # Verify Twilio signature
        if settings.TWILIO_VERIFY_SIGNATURE:
            signature = request.headers.get("X-Twilio-Signature", "")
            url = str(request.url)
            
            if not verify_twilio_signature(
                url, post_data, signature, settings.TWILIO_AUTH_TOKEN
            ):
                logger.warning("Invalid Twilio signature")
                raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Extract call info
        call_sid = post_data.get("CallSid")
        from_number = post_data.get("From")
        
        logger.info(f"Incoming call: {call_sid} from {from_number}")
        
        # Generate TwiML response
        public_url = settings.PUBLIC_URL.replace("https://", "").replace("http://", "")
        twiml = generate_twiml_response(public_url, call_sid, from_number)
        
        return Response(content=twiml, media_type="application/xml")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Twilio Media Stream WebSocket endpoint
@app.websocket("/voice/stream")
async def voice_stream(websocket: WebSocket):
    """
    Handle Twilio Media Stream WebSocket connection.
    Manages bidirectional audio streaming for a call.
    """
    async with async_session_maker() as session:
        try:
            # Initialize STT provider
            if settings.FEATURE_STT_PROVIDER == "deepgram":
                stt_provider = DeepgramSTT(
                    api_key=settings.DEEPGRAM_API_KEY,
                    model=settings.DEEPGRAM_MODEL,
                    language=settings.DEEPGRAM_LANGUAGE,
                    sample_rate=settings.AUDIO_SAMPLE_RATE,
                )
            else:  # whisper
                stt_provider = WhisperSTT(
                    api_key=settings.WHISPER_API_KEY,
                    model=settings.WHISPER_MODEL,
                )
            
            # Initialize TTS provider
            tts_provider = ElevenLabsTTS(
                api_key=settings.ELEVENLABS_API_KEY,
                voice_id=settings.ELEVENLABS_VOICE_ID,
                model=settings.ELEVENLABS_MODEL,
                stability=settings.ELEVENLABS_STABILITY,
                similarity_boost=settings.ELEVENLABS_SIMILARITY_BOOST,
            )
            
            # Initialize conversation router
            conversation_router = ConversationRouter(
                llm_provider=llm_provider,
                session=session,
                business_name=settings.APP_NAME,
                business_hours=f"{settings.BUSINESS_HOURS_START} to {settings.BUSINESS_HOURS_END}",
            )
            
            # Create call handler
            handler = TwilioCallHandler(
                websocket=websocket,
                session=session,
                stt_provider=stt_provider,
                tts_provider=tts_provider,
                conversation_router=conversation_router,
            )
            
            # Handle the call
            await handler.handle_call()
        
        except Exception as e:
            logger.error(f"Error in voice stream: {e}", exc_info=True)


# Admin endpoints (basic auth required)
def verify_admin_auth(authorization: Optional[str] = Header(None)):
    """Verify admin authentication."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Basic auth: "Basic base64(username:password)"
    try:
        import base64
        auth_decoded = base64.b64decode(authorization.split(" ")[1]).decode()
        username, password = auth_decoded.split(":", 1)
        
        if username != settings.ADMIN_USERNAME or password != settings.ADMIN_PASSWORD:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")


@app.get("/admin/calls")
async def get_recent_calls(
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    _auth: None = Depends(verify_admin_auth),
):
    """Get recent calls (admin only)."""
    try:
        calls = await CallRepository.get_recent(session, limit=limit)
        
        return {
            "calls": [
                {
                    "id": call.id,
                    "call_sid": call.call_sid,
                    "caller_phone": sanitize_phone(call.caller_phone),
                    "started_at": call.started_at.isoformat(),
                    "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                    "duration_s": call.duration_s,
                    "outcome": call.outcome,
                    "summary": call.summary,
                }
                for call in calls
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching calls: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch calls")


@app.get("/admin/messages")
async def get_messages(
    status: str = "new",
    session: AsyncSession = Depends(get_session),
    _auth: None = Depends(verify_admin_auth),
):
    """Get messages (admin only)."""
    try:
        messages = await MessageRepository.get_unread(session, limit=100)
        
        return {
            "messages": [
                {
                    "id": msg.id,
                    "call_id": msg.call_id,
                    "caller_name": msg.caller_name,
                    "caller_phone": sanitize_phone(msg.caller_phone),
                    "summary": msg.summary,
                    "urgency": msg.urgency,
                    "status": msg.status,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "health": "/healthz",
            "readiness": "/ready",
            "voice_incoming": "/voice/incoming",
            "voice_stream": "/voice/stream (WebSocket)",
            "admin_calls": "/admin/calls",
            "admin_messages": "/admin/messages",
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

