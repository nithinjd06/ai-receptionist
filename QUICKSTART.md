# Quick Start Guide - 5 Minutes to First Call

This guide will get you from zero to taking your first AI phone call in about 5 minutes.

## Prerequisites

- Python 3.11+
- A Twilio account (free trial works!)
- API keys for: Deepgram, OpenAI, ElevenLabs

## Step 1: Get API Keys (2 minutes)

### Twilio (Required)
1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Get a phone number (free with trial)
3. Note your Account SID and Auth Token from [console](https://console.twilio.com)

### Deepgram (Required)
1. Sign up at [deepgram.com](https://console.deepgram.com/signup)
2. Get $200 free credit
3. Create an API key from [console](https://console.deepgram.com/project/default/keys)

### OpenAI (Required)
1. Sign up at [platform.openai.com](https://platform.openai.com/signup)
2. Add payment method
3. Create API key from [API keys page](https://platform.openai.com/api-keys)

### ElevenLabs (Required)
1. Sign up at [elevenlabs.io](https://elevenlabs.io/)
2. Get free tier (10,000 characters/month)
3. Get API key from [profile](https://elevenlabs.io/speech-synthesis)

## Step 2: Setup Project (1 minute)

```bash
# Clone/navigate to project
cd ai_receptionist

# Copy environment template
cp env.example .env

# Make run script executable
chmod +x run.sh
```

## Step 3: Configure Environment (1 minute)

Edit `.env` file with your API keys:

```bash
# Required - Update these
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+15551234567
DEEPGRAM_API_KEY=your_deepgram_key
OPENAI_API_KEY=sk-your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ADMIN_PASSWORD=choose_secure_password

# Will update after ngrok (Step 5)
PUBLIC_URL=https://your-domain.com
```

## Step 4: Start Server (30 seconds)

```bash
# Run quick start script
./run.sh

# Server will start at http://localhost:8000
```

You should see:
```
✅ Setup complete!
🚀 Starting AI Receptionist server...
```

## Step 5: Expose with ngrok (30 seconds)

In a new terminal:

```bash
# Install ngrok if needed: https://ngrok.com/download
ngrok http 8000
```

You'll see:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

**Copy that HTTPS URL!**

Update `.env`:
```bash
PUBLIC_URL=https://abc123.ngrok.io
```

Restart the server (Ctrl+C and run `./run.sh` again).

## Step 6: Configure Twilio (30 seconds)

1. Go to [Twilio Console](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Click your phone number
3. Scroll to "Voice Configuration"
4. Set "A Call Comes In" to:
   - **Webhook**
   - URL: `https://your-ngrok-url.ngrok.io/voice/incoming`
   - **HTTP POST**
5. Click **Save**

## Step 7: Make Your First Call! 🎉

Call your Twilio phone number and say:

- "What are your hours?"
- "I'd like to schedule an appointment"
- "Can someone call me back?"

## What Just Happened?

When you called:

1. **Twilio** received the call and sent webhook to your server
2. Your server returned **TwiML** to start Media Stream
3. **WebSocket** connection established for bidirectional audio
4. Audio encoded in **μ-law** streamed in real-time
5. **Deepgram** transcribed your speech to text
6. **GPT-4o** understood intent and generated response
7. **ElevenLabs** synthesized natural speech
8. Audio streamed back through Twilio to caller
9. All logged to **SQLite** database

## Next Steps

### Test Different Scenarios

1. **FAQ Questions**
   ```
   "What are your hours?"
   "Where are you located?"
   "What insurance do you accept?"
   ```

2. **Appointment Scheduling**
   ```
   "I need to schedule an appointment"
   "What times are available next week?"
   ```

3. **Message Taking**
   ```
   "Can someone call me back?"
   "I have a billing question"
   ```

4. **Off-Hours**
   - Edit business hours in `.env` to test off-hours message

### View Call Logs

```bash
# Visit admin panel (use ADMIN_PASSWORD from .env)
curl -u admin:your_password http://localhost:8000/admin/calls
```

Or visit in browser: http://localhost:8000/admin/calls

### Add Google Calendar (Optional)

See main README.md section on Google Calendar setup.

### Deploy to Production

When ready for real use:

1. **Choose hosting**: Render, Railway, AWS, etc.
2. **Follow**: `DEPLOYMENT.md` for platform-specific instructions
3. **Update**: Twilio webhook to production URL
4. **Monitor**: Check `/admin/calls` for call quality

## Troubleshooting

### "No module named 'server'"
```bash
# Make sure you're in ai_receptionist directory
cd ai_receptionist
python -m uvicorn server.main:app --reload
```

### "Invalid Twilio signature"
- Verify `PUBLIC_URL` in `.env` matches ngrok URL exactly
- Make sure it's HTTPS (not HTTP)
- Restart server after changing .env

### "No audio in call"
- Check Twilio Media Streams are enabled
- Verify ngrok is running and forwarding to port 8000
- Check server logs for WebSocket connection

### "High latency / slow responses"
- Normal for first call (cold start)
- Check your internet connection
- Consider deploying closer to Twilio servers (US)

### "API errors"
- Verify all API keys are valid
- Check you have credits/billing enabled
- Look at server logs for specific errors

## Cost for Testing

With free tiers:
- **Deepgram**: $200 free credit (≈45,000 minutes)
- **Twilio**: $15 trial credit (≈1,750 minutes)
- **ElevenLabs**: 10,000 chars/month free (≈50 calls)
- **OpenAI**: Pay as you go (≈$0.02/call)

**Total cost for 10 test calls**: < $1

## Support

- 📖 Full documentation: `README.md`
- 🚀 Deployment guide: `DEPLOYMENT.md`
- 🐛 Issues: GitHub Issues
- 💬 Questions: GitHub Discussions

## What's Next?

- [x] Made your first call
- [ ] Customize FAQ responses (`data/faq.json`)
- [ ] Set up Google Calendar integration
- [ ] Deploy to production
- [ ] Configure business hours
- [ ] Customize system prompt
- [ ] Add your own actions/integrations

**Congratulations! You now have a working AI receptionist! 🎉**

