# Architecture Overview

This document explains the design decisions, architecture patterns, and technical implementation of the AI Receptionist system.

## System Architecture

```
┌─────────────┐
│   Caller    │
└──────┬──────┘
       │ Phone Call
       ▼
┌─────────────────────────────────────────────────────────────┐
│                      Twilio Voice                           │
│  ┌──────────────┐         ┌──────────────────────────────┐ │
│  │   TwiML      │◄────────│   POST /voice/incoming       │ │
│  │   Response   │         │   (Webhook)                  │ │
│  └──────┬───────┘         └──────────────────────────────┘ │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         Twilio Media Streams (WebSocket)             │ │
│  │         WS /voice/stream                             │ │
│  │         • Bidirectional audio (8kHz μ-law)          │ │
│  │         • Real-time streaming                        │ │
│  └─────────────────────┬────────────────────────────────┘ │
└────────────────────────┼──────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │      AI Receptionist Server            │
        │         (FastAPI + Python)             │
        │                                        │
        │  ┌──────────────────────────────────┐ │
        │  │   TwilioCallHandler              │ │
        │  │   • Manages WebSocket            │ │
        │  │   • Audio buffering              │ │
        │  │   • Barge-in detection           │ │
        │  └────┬────────────────────────┬────┘ │
        │       │                        │      │
        │       ▼                        ▼      │
        │  ┌─────────┐            ┌─────────┐  │
        │  │   STT   │            │   TTS   │  │
        │  │Deepgram │            │ElevenLabs│ │
        │  └────┬────┘            └────▲────┘  │
        │       │                      │       │
        │       ▼                      │       │
        │  ┌──────────────────────────┼────┐  │
        │  │   ConversationRouter      │    │  │
        │  │   • Turn management       │    │  │
        │  │   • Context tracking      │    │  │
        │  │   • Action routing        │    │  │
        │  └────┬──────────────────────┘    │  │
        │       ▼                            │  │
        │  ┌─────────┐                      │  │
        │  │   LLM   │──────────────────────┘  │
        │  │ GPT-4o  │  (Response text)        │
        │  └────┬────┘                         │
        │       │                              │
        │       ▼                              │
        │  ┌──────────────────────────────┐   │
        │  │   Action Handlers            │   │
        │  │   • FAQ lookup               │   │
        │  │   • Scheduling               │   │
        │  │   • Message taking           │   │
        │  │   • Human routing            │   │
        │  └────┬─────────────────────────┘   │
        │       ▼                              │
        │  ┌──────────────────────────────┐   │
        │  │   Database (SQLite/Postgres) │   │
        │  │   • Calls                    │   │
        │  │   • Turns                    │   │
        │  │   • Appointments             │   │
        │  │   • Messages                 │   │
        │  │   • Audit logs               │   │
        │  └──────────────────────────────┘   │
        └────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────────┐
        │      External Services                 │
        │  • Google Calendar (scheduling)        │
        │  • Athena Health (EHR, optional)       │
        │  • Redis (caching, optional)           │
        └────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Async-First Architecture

**Decision**: Use Python `asyncio` throughout the stack.

**Rationale**:
- Handle multiple concurrent phone calls efficiently
- Non-blocking I/O for API calls (STT, LLM, TTS)
- Better resource utilization vs threading
- Natural fit for WebSocket streaming

**Implementation**:
- FastAPI with async route handlers
- AsyncIO database sessions (SQLAlchemy async)
- Async providers for STT/TTS/LLM
- Async context managers for resource cleanup

### 2. Provider Abstraction Pattern

**Decision**: Abstract interfaces for STT, TTS, LLM providers.

**Rationale**:
- Swap providers via environment variables
- A/B test different providers
- Avoid vendor lock-in
- Easy to add new providers

**Implementation**:
```python
class STTProvider(ABC):
    @abstractmethod
    async def send_audio(self, chunk: bytes) -> None: ...
    @abstractmethod
    async def receive_transcripts(self) -> AsyncIterator[TranscriptResult]: ...

# Concrete implementations
- DeepgramSTT
- WhisperSTT
```

### 3. Streaming Pipeline

**Decision**: Stream audio in real-time vs batch processing.

**Rationale**:
- Lower latency (P95 < 2s)
- Better user experience
- Enable barge-in (user interruption)
- Deepgram supports streaming natively

**Implementation**:
- 300ms audio chunks (balance latency vs accuracy)
- Partial transcripts for early response
- Generator pattern for TTS streaming
- WebSocket for bidirectional audio

### 4. Conversation State Management

**Decision**: Server-side conversation context stored in database.

**Rationale**:
- Support multi-turn conversations
- Persist across server restarts
- Enable conversation analysis
- Audit trail for compliance

**Implementation**:
```python
class ConversationContext:
    call_id: int
    turn_number: int
    conversation_state: Dict[str, Any]
    last_action: Optional[str]
```

### 5. Function Calling for Actions

**Decision**: Use LLM function calling (not prompt engineering alone).

**Rationale**:
- Structured JSON output (reliable parsing)
- Type-safe action parameters
- Clear intent classification
- Works with GPT-4o and Claude

**Implementation**:
```python
functions = [
    {
        "name": "answer_faq",
        "parameters": {...}
    },
    {
        "name": "schedule_appointment",
        "parameters": {...}
    },
    ...
]
```

### 6. Database Schema Design

**Decision**: Separate tables for calls, turns, appointments, messages, audit logs.

**Rationale**:
- Normalize data (avoid duplication)
- Efficient queries for analytics
- Clear separation of concerns
- Support compliance requirements

**Schema**:
- `calls`: Call metadata and summary
- `turns`: Individual conversation exchanges
- `appointments`: Scheduled appointments
- `messages`: Messages for callback
- `audit_logs`: Audit trail

### 7. Safety Guardrails in System Prompt

**Decision**: Enforce safety rules via system prompt, not post-processing.

**Rationale**:
- LLM naturally refuses medical advice
- Contextual safety (understands intent)
- Reduces false positives
- More maintainable than rule-based filtering

**Implementation**:
```python
prompt = """
Safety Rules:
- NEVER provide medical advice
- If emergency, advise calling 911
- After 2 failed ASR, offer message taking
"""
```

### 8. Audio Codec Design

**Decision**: Handle μ-law encoding/decoding in application layer.

**Rationale**:
- Twilio sends μ-law by default
- STT providers expect PCM
- TTS providers return various formats
- Need format conversion anyway

**Implementation**:
```python
class AudioCodec:
    def decode_mulaw(self, b64: str) -> bytes  # Twilio → PCM
    def encode_mulaw(self, pcm: bytes) -> str  # PCM → Twilio
    def pcm_to_wav(self, pcm: bytes) -> bytes  # PCM → WAV (for Whisper)
```

### 9. Barge-in Detection

**Decision**: Simple voice activity detection on incoming audio during playback.

**Rationale**:
- Natural conversation flow
- User can interrupt assistant
- Industry standard for voice AI
- Improves user experience

**Implementation**:
- Monitor audio input during TTS playback
- Detect non-zero audio energy
- Send "clear" message to Twilio
- Stop TTS streaming

### 10. Repository Pattern for Database

**Decision**: Separate repository layer from models.

**Rationale**:
- Decouple business logic from persistence
- Easy to mock for testing
- Reusable queries
- Clear data access patterns

**Implementation**:
```python
class CallRepository:
    @staticmethod
    async def create(session, call: Call) -> Call: ...
    @staticmethod
    async def get_by_call_sid(session, sid: str) -> Call: ...
```

## Performance Considerations

### Latency Budget (P95 target: < 2.0s)

```
Audio Buffering:      300ms  (chunk collection)
STT Processing:       200ms  (Deepgram Nova)
LLM Processing:       800ms  (GPT-4o function calling)
TTS Generation:       400ms  (ElevenLabs streaming)
Network Overhead:     300ms  (API calls, round trips)
─────────────────────────────
Total:               2000ms
```

### Optimization Strategies

1. **Reduce Audio Chunk Duration** (300ms → 200ms)
   - Faster STT but lower accuracy
   - Trade-off between latency and quality

2. **Use Deepgram Partials**
   - Start LLM processing before final transcript
   - Can save 200-300ms

3. **Streaming TTS**
   - Start playing audio before complete
   - Reduces perceived latency

4. **Parallel Operations**
   - Database writes don't block response
   - Background tasks for non-critical operations

5. **Connection Pooling**
   - Reuse HTTP connections to providers
   - Reduce connection overhead

### Scalability

**Single Instance Limits**:
- **Concurrent Calls**: ~10-20 (CPU bound)
- **WebSocket Connections**: ~1000 (memory bound)
- **Database**: SQLite good for < 100 calls/day

**Scaling Strategy**:
1. **Horizontal Scaling**: Deploy multiple instances behind load balancer
2. **Database**: Migrate to Postgres for concurrent writes
3. **Caching**: Add Redis for FAQ and calendar slots
4. **CDN**: Serve static assets via CDN
5. **Regional Deployment**: Deploy close to users

## Security Architecture

### Authentication & Authorization

- **Twilio Webhooks**: Signature verification
- **Admin Endpoints**: HTTP Basic Auth
- **API Keys**: Environment variables only (never in code)
- **Database**: No hardcoded credentials

### Data Protection

- **PII Masking**: Phone numbers masked in logs
- **PHI Boundaries**: EHR integration disabled by default
- **Audit Logging**: All actions logged for compliance
- **HTTPS Only**: TLS for all external communication

### Secrets Management

```
Development:  .env file (gitignored)
Production:   Environment variables (platform secrets)
```

## Error Handling Strategy

### Graceful Degradation

```python
if STT fails:
    → Ask caller to repeat
    → Log error
    → Continue conversation

if LLM times out:
    → Fallback: "Let me take a message"
    → Save context
    → Log for manual follow-up

if TTS fails:
    → Use TwiML <Say> as fallback
    → Log error
    → Continue conversation
```

### Circuit Breaker Pattern

Not currently implemented but recommended for production:

```python
if provider_error_rate > 50% in last_5_min:
    → Switch to backup provider
    → Alert operations team
    → Log incident
```

## Testing Strategy

### Unit Tests
- Mock external providers (STT, TTS, LLM)
- Test business logic in isolation
- Fast feedback loop

### Integration Tests
- Mock database (in-memory SQLite)
- Test provider integrations
- End-to-end conversation flows

### Load Tests (Recommended)
- Simulate concurrent calls
- Measure latency under load
- Identify bottlenecks

## Monitoring & Observability

### Structured Logging
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "request_id": "uuid",
  "call_sid": "CA123",
  "event": "turn_completed",
  "latency_ms": 1250,
  "action": "schedule_appointment"
}
```

### Key Metrics
- **Latency**: P50, P95, P99 turn latency
- **Success Rate**: % successful calls
- **Error Rate**: % errors by type
- **Action Distribution**: FAQ vs scheduling vs messages
- **Call Volume**: Calls/hour, calls/day

### Health Checks
- `/healthz`: Basic liveness
- `/ready`: Readiness (DB connectivity)
- Periodic provider health checks

## Future Enhancements

### Near-term
- [ ] Redis caching for FAQ and calendar
- [ ] Prometheus metrics export
- [ ] Sentry error tracking integration
- [ ] Call recording and playback

### Long-term
- [ ] Multi-language support
- [ ] Voice biometrics
- [ ] Sentiment analysis
- [ ] Advanced analytics dashboard
- [ ] CRM integrations

## Conclusion

This architecture prioritizes:
1. **Low Latency**: Real-time streaming, async operations
2. **Reliability**: Error handling, graceful degradation
3. **Maintainability**: Clean abstractions, separation of concerns
4. **Scalability**: Horizontal scaling, async design
5. **Security**: Authentication, PII protection, audit trails

The system is production-ready for small to medium deployments (< 1000 calls/day) and can scale horizontally for larger loads.

