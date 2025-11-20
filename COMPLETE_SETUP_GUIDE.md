# Complete Setup Guide - From Zero to First Call

This guide will walk you through **everything** you need to get your AI receptionist working, step by step.

## 📋 What You'll Need

Before starting, make sure you have:
- ✅ A computer (Windows, Mac, or Linux)
- ✅ Internet connection
- ✅ Python 3.11 or higher installed
- ✅ A Google account (for Gemini API)
- ✅ About 30 minutes of time

---

## 🎯 Step-by-Step Setup

### **STEP 1: Get All Your API Keys** (15 minutes)

You need 4 API keys. Let's get them one by one:

#### 1.1 Twilio (Phone System) - FREE TRIAL

1. **Sign up**: Go to https://www.twilio.com/try-twilio
2. **Verify your phone**: They'll send you a code
3. **Get a phone number**:
   - In dashboard, click "Get a Twilio phone number"
   - Choose any number (they're all free on trial)
   - **Copy this number!** (e.g., +15551234567)
4. **Get credentials**:
   - On dashboard, you'll see:
     - **Account SID**: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
     - **Auth Token**: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Copy both!**

✅ **You now have:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

---

#### 1.2 Deepgram (Speech Recognition) - $200 FREE

1. **Sign up**: Go to https://console.deepgram.com/signup
2. **Get $200 free credit** (no credit card needed!)
3. **Create API key**:
   - Click "API Keys" in left sidebar
   - Click "Create New Key"
   - **Copy immediately!** (only shown once)
   - Name it "AI Receptionist"

✅ **You now have:**
- `DEEPGRAM_API_KEY`

---

#### 1.3 Google Gemini (AI Brain) - FREE TIER

1. **Sign up**: Go to https://aistudio.google.com/app/apikey
2. **Sign in** with Google account
3. **Create API key**:
   - Click "Create API Key"
   - Choose "Create API key in new project" (or existing)
   - **Copy the key!**

✅ **You now have:**
- `GEMINI_API_KEY`

---

#### 1.4 ElevenLabs (Voice) - FREE TIER

1. **Sign up**: Go to https://elevenlabs.io
2. **Free tier**: 10,000 characters/month free
3. **Get API key**:
   - Click profile icon → "Profile"
   - Scroll to "API Keys"
   - Click "Copy" on your key (or create new one)

✅ **You now have:**
- `ELEVENLABS_API_KEY`

---

### **STEP 2: Install Python & Setup Project** (5 minutes)

#### 2.1 Check Python Version

Open terminal/command prompt and run:

```bash
python --version
```

**Should show**: `Python 3.11.x` or higher

**If not installed:**
- **Windows**: Download from https://www.python.org/downloads/
- **Mac**: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11`

#### 2.2 Navigate to Project

```bash
cd c:\Users\nithi\automations\ai_receptionist
```

#### 2.3 Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Mac/Linux:
source venv/bin/activate
```

**You should see** `(venv)` in your terminal prompt.

#### 2.4 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will take 2-3 minutes. You'll see packages installing.

---

### **STEP 3: Configure Environment** (3 minutes)

#### 3.1 Create .env File

```bash
# Copy the example file
# Windows:
Copy-Item env.example .env

# Mac/Linux:
cp env.example .env
```

#### 3.2 Edit .env File

Open `.env` in any text editor (Notepad, VS Code, etc.)

**Replace these values with YOUR actual keys:**

```env
# Twilio (from Step 1.1)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+15551234567

# Deepgram (from Step 1.2)
DEEPGRAM_API_KEY=your_deepgram_key_here

# Gemini (from Step 1.3)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# ElevenLabs (from Step 1.4)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Admin password (choose your own)
ADMIN_PASSWORD=mySecurePassword123

# Public URL (we'll update this in Step 5)
PUBLIC_URL=https://your-domain.com
```

**Save the file!**

---

### **STEP 4: Create Data Directory** (30 seconds)

```bash
# Create directory for database
mkdir data
```

---

### **STEP 5: Start Your Server** (1 minute)

```bash
# Make sure virtual environment is activated (you should see (venv))
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete
INFO:     Initialized Google Gemini 2.5 Flash LLM provider
```

✅ **Server is running!**

**Test it:**
- Open browser: http://localhost:8000
- You should see JSON with service info
- Try: http://localhost:8000/healthz → Should say "healthy"

---

### **STEP 6: Expose Server to Internet** (3 minutes)

Your server is only on your computer. We need to make it accessible to Twilio.

#### 6.1 Install ngrok

1. **Download**: https://ngrok.com/download
2. **Sign up**: Create free account at https://dashboard.ngrok.com/signup
3. **Get auth token**: Copy it from dashboard
4. **Install**: Follow instructions for your OS
5. **Authenticate**: Run:
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

#### 6.2 Start ngrok

**Open a NEW terminal** (keep server running in first terminal):

```bash
ngrok http 8000
```

**You'll see:**
```
Forwarding  https://abc123def456.ngrok.app -> http://localhost:8000
```

**Copy that HTTPS URL!** (the `abc123def456.ngrok.app` part)

#### 6.3 Update .env File

1. **Stop your server** (Ctrl+C in first terminal)
2. **Edit `.env`**:
   ```env
   PUBLIC_URL=https://abc123def456.ngrok.app
   ```
   (Replace with YOUR actual ngrok URL)
3. **Save**
4. **Restart server**:
   ```bash
   python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
   ```

---

### **STEP 7: Connect Twilio** (2 minutes)

Tell Twilio where to send calls:

1. **Go to**: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. **Click** your phone number
3. **Scroll** to "Voice Configuration"
4. **Configure**:
   - **A call comes in**: Select "Webhook"
   - **URL**: `https://your-ngrok-url.ngrok.app/voice/incoming`
     - Replace `your-ngrok-url.ngrok.app` with YOUR actual ngrok URL
   - **HTTP Method**: POST
5. **Click "Save"**

✅ **Twilio is connected!**

---

### **STEP 8: Make Your First Call!** 🎉

**Call your Twilio phone number!**

You should hear:
> "Hello! Thank you for calling. How may I help you today?"

**Try saying:**
- "What are your hours?"
- "Where are you located?"
- "I'd like to schedule an appointment"
- "Can someone call me back?"

**Watch your terminal** - you'll see real-time logs!

---

## ✅ Verification Checklist

After setup, verify everything:

- [ ] Server starts without errors
- [ ] http://localhost:8000 shows service info
- [ ] http://localhost:8000/healthz returns "healthy"
- [ ] ngrok is running and forwarding
- [ ] Twilio webhook configured correctly
- [ ] Can make a call and hear greeting
- [ ] AI responds to questions

---

## 🎯 Quick Test Commands

### Test Server Locally

```bash
# Health check
curl http://localhost:8000/healthz

# Should return: {"status":"healthy","service":"AI Receptionist"}
```

### Test Admin Endpoint

```bash
# After making a call
curl -u admin:your_password http://localhost:8000/admin/calls

# Should return JSON with call history
```

---

## 🔧 Common Issues & Fixes

### Issue: "Module not found"

**Fix:**
```bash
# Make sure virtual environment is activated
# You should see (venv) in prompt

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Invalid Twilio signature"

**Fix:**
- Check `PUBLIC_URL` in `.env` matches ngrok URL EXACTLY
- Must be HTTPS (not HTTP)
- No trailing slash
- Restart server after changing `.env`

### Issue: "No audio" or "Silent call"

**Fix:**
- Check ngrok is still running (free tier stops after 2 hours)
- Verify WebSocket connection in terminal logs
- Check Twilio webhook URL is correct
- Make sure server is running

### Issue: "API key not valid"

**Fix:**
- Double-check you copied the full key (no spaces)
- No quotes around the key in `.env`
- Verify key is active in provider dashboard
- For Gemini: Check at https://aistudio.google.com/app/apikey

### Issue: ngrok URL keeps changing

**Fix:**
- Free ngrok URLs change each restart
- Paid ngrok ($8/month) gives permanent URL
- Or deploy to real server (see DEPLOYMENT.md)

### Issue: "High latency" or "Slow responses"

**Fix:**
- Normal for first call (cold start)
- Subsequent calls should be faster
- Check your internet connection
- Free API tiers might be slower

---

## 📊 What's Happening Behind the Scenes

When someone calls:

1. **Twilio** receives call → sends webhook to your server
2. **Your server** returns TwiML → starts WebSocket connection
3. **Audio streams** in real-time (bidirectional)
4. **Deepgram** transcribes speech → text
5. **Gemini** understands intent → generates response + action
6. **ElevenLabs** converts text → speech
7. **Audio streams back** → caller hears response
8. **Database** logs everything for review

**All in under 2 seconds!**

---

## 🎨 Customize Your Receptionist

### Update Business Info

Edit `data/faq.json`:

```json
{
  "hours": {
    "question": "What are your hours?",
    "answer": "We're open Monday-Friday, 9 AM to 6 PM"
  },
  "location": {
    "question": "Where are you located?",
    "answer": "456 Main Street, Austin, TX"
  }
}
```

### Change Voice

Edit `.env`:

```env
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # Rachel (default)
# Other options at: https://elevenlabs.io/voice-library
```

### Adjust Business Hours

Edit `.env`:

```env
BUSINESS_HOURS_START=09:00
BUSINESS_HOURS_END=17:00
BUSINESS_DAYS=1,2,3,4,5  # Mon-Fri
```

---

## 📈 Next Steps

### For Development
- ✅ Test different conversation scenarios
- ✅ Customize FAQ responses
- ✅ Adjust system prompts
- ✅ Monitor call logs

### For Production
- 📖 Read `DEPLOYMENT.md` for production deployment
- 🚀 Deploy to Render/Railway/AWS
- 🔒 Set up proper domain and SSL
- 📊 Add monitoring and alerts

---

## 💰 Cost Breakdown

**Free Tier Limits:**
- **Twilio**: $15 trial credit (~1,750 minutes)
- **Deepgram**: $200 free credit (~45,000 minutes)
- **Gemini**: 1,500 requests/day free
- **ElevenLabs**: 10,000 characters/month free

**Per Call Cost (after free tier):**
- Deepgram: $0.01
- Gemini: $0.001
- ElevenLabs: $0.02
- Twilio: $0.02
- **Total: ~$0.05 per call**

---

## 📚 Additional Resources

- **Main README**: `README.md` - Complete documentation
- **Quick Start**: `QUICKSTART.md` - 5-minute version
- **Deployment**: `DEPLOYMENT.md` - Production deployment
- **Architecture**: `ARCHITECTURE.md` - Technical details
- **Knowledge Base**: `KNOWLEDGE_BASE_GUIDE.md` - FAQ customization
- **EHR Integration**: `EHR_INTEGRATION_GUIDE.md` - Athena Health setup

---

## 🆘 Getting Help

**If something doesn't work:**

1. **Check logs** in terminal for error messages
2. **Verify all API keys** are correct in `.env`
3. **Test each component** individually:
   - Server: http://localhost:8000/healthz
   - ngrok: Check forwarding status
   - Twilio: Verify webhook URL
4. **Check documentation** in README.md
5. **Review troubleshooting** section above

---

## ✅ Success Checklist

You're all set when:

- ✅ Server starts without errors
- ✅ All API keys configured
- ✅ ngrok forwarding to localhost:8000
- ✅ Twilio webhook points to ngrok URL
- ✅ Can make a call and hear AI
- ✅ AI responds to questions
- ✅ Call logs appear in admin dashboard

---

## 🎉 Congratulations!

**You now have a working AI receptionist!** 📞🤖

**What you can do:**
- Answer phone calls automatically
- Handle FAQs about your business
- Schedule appointments
- Take messages
- Route complex calls

**Next:**
- Customize for your business
- Test different scenarios
- Deploy to production when ready

**Happy calling!** 🚀





