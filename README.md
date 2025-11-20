# AI Receptionist - Production-Ready Voice Assistant

A production-ready AI receptionist that answers real phone calls, holds natural conversations, and performs actions like scheduling appointments, taking messages, and routing calls.

## Features

- **Real-time Phone Conversations**: Twilio integration with bidirectional audio streaming
- **Natural Language Processing**: GPT-4o or Claude 3.5 Sonnet for intent understanding
- **Low-Latency STT**: Deepgram Nova streaming (or Whisper alternative)
- **Natural TTS**: ElevenLabs streaming for human-like speech
- **Smart Actions**: FAQ answers, appointment scheduling, message taking, call routing
- **Calendar Integration**: Google Calendar with slot discovery and booking
- **Safety Guardrails**: Medical advice refusal, emergency detection, escalation protocols
- **Full Observability**: Structured logging, request IDs, latency metrics, audit trails
- **Production Ready**: Docker deployment, health checks, async architecture

## Tech Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn (async)
- **Telephony**: Twilio Programmable Voice + Media Streams
- **STT**: Deepgram Nova streaming (Whisper alternative available)
- **LLM**: GPT-4o (Claude 3.5 Sonnet alternative available)
- **TTS**: ElevenLabs streaming
- **Database**: SQLite (Postgres-ready via config)
- **Deployment**: Docker, Render/Railway/AWS compatible

## Project Structure

```
ai_receptionist/
├── server/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Configuration management
│   ├── telephony_twilio.py      # Twilio integration
│   ├── audio_codec.py           # Audio processing utilities
│   ├── stt/                     # Speech-to-Text providers
│   │   ├── deepgram_streaming.py
│   │   └── whisper_batch.py
│   ├── tts/                     # Text-to-Speech providers
│   │   └── elevenlabs_stream.py
│   ├── llm/                     # LLM providers
│   │   ├── openai_gpt4o.py
│   │   └── anthropic_claude.py
│   ├── convo/                   # Conversation management
│   │   ├── router.py
│   │   ├── prompts.py
│   │   └── schema.py
│   ├── scheduling/              # Calendar integrations
│   │   ├── google_calendar.py
│   │   └── calendly.py
│   ├── ehr/                     # EHR integrations (optional)
│   │   └── athena_client.py
│   ├── db/                      # Database models
│   │   ├── models.py
│   │   └── repo.py
│   └── utils/                   # Utilities
├── data/
│   └── faq.json                 # FAQ knowledge base
├── tests/                       # Test suite
├── requirements.txt
├── Dockerfile
├── Makefile
└── README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Twilio account with phone number
- Deepgram API key
- OpenAI API key
- ElevenLabs API key
- Google Calendar credentials (for scheduling)

### 2. Installation

```bash
# Clone repository
cd ai_receptionist

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
PUBLIC_URL=https://your-domain.com
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=sk-your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ADMIN_PASSWORD=secure_password_here

# Optional: Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=token.json
```

### 4. Google Calendar Setup (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials as `credentials.json`
6. Place in project root

### 5. Run Locally

```bash
# Start server
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Or use Make
make run
```

### 6. Expose with ngrok

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Note the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update PUBLIC_URL in .env
```

### 7. Configure Twilio Webhook

1. Go to [Twilio Console](https://console.twilio.com/)
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Select your phone number
4. Under "Voice Configuration":
   - A Call Comes In: Webhook
   - URL: `https://your-ngrok-url.ngrok.io/voice/incoming`
   - HTTP Method: POST
5. Save

### 8. Make a Test Call

Call your Twilio number and test the conversation!

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t ai-receptionist:latest .

# Run container
docker run -p 8000:8000 --env-file .env ai-receptionist:latest
```

### Deploy to Render

1. Create account at [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repository
4. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn server.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env`
6. Deploy!

### Deploy to Railway

1. Create account at [railway.app](https://railway.app)
2. Create new project from GitHub
3. Add environment variables
4. Railway auto-deploys

### Production Database (Postgres)

Update `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

## Configuration

### Provider Selection

Switch providers via environment variables:

```env
# STT Provider
FEATURE_STT_PROVIDER=deepgram  # or whisper

# LLM Provider
FEATURE_LLM_PROVIDER=openai    # or anthropic

# TTS Provider
FEATURE_TTS_PROVIDER=elevenlabs

# Scheduler
FEATURE_SCHEDULER=google       # google | calendly | none
```

### Business Hours

```env
BUSINESS_HOURS_START=08:00
BUSINESS_HOURS_END=17:00
BUSINESS_DAYS=1,2,3,4,5  # Monday=1, Sunday=7
```

### Audio & Latency Tuning

```env
# Audio processing
AUDIO_CHUNK_DURATION_MS=300  # Larger = more latency but better accuracy

# Timeouts
STT_TIMEOUT_S=5.0
TTS_TIMEOUT_S=5.0
LLM_TIMEOUT_S=10.0

# Barge-in (user interruption)
BARGE_IN_ENABLED=true
```

## API Endpoints

### Public Endpoints

- `GET /` - Service information
- `GET /healthz` - Health check
- `GET /ready` - Readiness check
- `POST /voice/incoming` - Twilio webhook (TwiML)
- `WS /voice/stream` - Twilio Media Stream WebSocket

### Admin Endpoints (Basic Auth)

- `GET /admin/calls` - Recent call history
- `GET /admin/messages` - Messages for callback

**Authentication**: Basic Auth with `ADMIN_USERNAME` and `ADMIN_PASSWORD`

```bash
# Example
curl -u admin:your_password https://your-domain.com/admin/calls
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=server --cov-report=html

# Or use Make
make test
```

## Safety & Guardrails

The system includes multiple safety mechanisms:

1. **Medical Advice Refusal**: Never provides medical advice or diagnoses
2. **Emergency Detection**: Recognizes emergencies and advises calling 911
3. **Failed ASR Handling**: After 2 failed attempts, offers message taking
4. **Off-Hours Protocol**: Takes messages when office is closed
5. **PII Protection**: Masks sensitive information in logs
6. **Audit Trail**: All actions logged for compliance

## Performance Targets

- **P95 Turn Latency**: < 2.0 seconds (STT + LLM + TTS)
- **Barge-in Latency**: < 300ms to detect and stop
- **Audio Chunk Size**: 300-600ms for smooth streaming
- **Concurrent Calls**: 10+ (single instance)

### Latency Optimization Tips

1. **Reduce chunk duration** for faster STT (but less accurate)
2. **Use Deepgram partials** for interim results
3. **Enable ElevenLabs low-latency mode** (`optimize_streaming_latency=3`)
4. **Deploy closer to users** (regional deployment)
5. **Use Postgres** instead of SQLite for high load

## EHR Integration (Athena Health)

⚠️ **IMPORTANT**: EHR integration is disabled by default and is a **stub implementation**.

Production use requires:
- Business Associate Agreement (BAA) with Athena Health
- HIPAA compliance implementation
- PHI data handling and encryption
- Audit logging for PHI access
- Security assessment and penetration testing

Enable in `.env`:

```env
FEATURE_EHR_ATHENA=true
ATHENA_CLIENT_ID=your_client_id
ATHENA_CLIENT_SECRET=your_client_secret
ATHENA_PRACTICE_ID=your_practice_id
```

## Observability

### Structured Logging

Logs are JSON-formatted for easy parsing:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "level": "INFO",
  "name": "server.telephony",
  "message": "Call started: CA123456",
  "request_id": "uuid-here"
}
```

### Metrics

Key metrics tracked:
- Turn latency (P50, P95, P99)
- STT/TTS/LLM latency breakdown
- Call duration
- Action success/failure rates
- Error rates by type

### Call Summaries

End-of-call summaries include:
- Total turns
- Actions taken
- Appointments scheduled
- Messages taken
- Errors encountered

## Troubleshooting

### Audio Quality Issues

- Check `AUDIO_CHUNK_DURATION_MS` (300-600ms recommended)
- Verify Twilio Media Streams are enabled
- Ensure proper μ-law encoding/decoding

### High Latency

- Profile LLM response time (check `OPENAI_TIMEOUT_S`)
- Use Deepgram partials for faster STT
- Reduce context window in conversation history
- Check network latency to providers

### Database Errors

- Ensure database file/directory is writable
- For Postgres: verify connection string and credentials
- Check async session configuration

### Twilio WebSocket Disconnects

- Verify `PUBLIC_URL` is correct and HTTPS
- Check WebSocket timeout settings
- Ensure server can handle persistent connections

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new features
4. Run linters: `make lint`
5. Format code: `make format`
6. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues or questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [repository-url]/wiki

## Roadmap

- [ ] Multi-language support (Spanish, French, etc.)
- [ ] Voice biometrics for caller identification
- [ ] Advanced sentiment analysis
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] SMS/email follow-ups
- [ ] Analytics dashboard
- [ ] Multi-tenant support
- [ ] Call recording and quality monitoring

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Twilio](https://www.twilio.com/)
- [Deepgram](https://deepgram.com/)
- [OpenAI](https://openai.com/)
- [ElevenLabs](https://elevenlabs.io/)
- [Google Calendar API](https://developers.google.com/calendar)







