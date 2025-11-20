# Switch to Google Gemini 2.5 Flash

Gemini 2.5 Flash is Google's fastest and most cost-effective LLM - perfect for real-time voice applications!

## Why Gemini 2.5 Flash?

✅ **Fast**: Lower latency than GPT-4o  
✅ **Cheap**: ~80% cheaper than GPT-4o  
✅ **Smart**: Excellent function calling support  
✅ **Free Tier**: Generous free quota to start  

**Cost Comparison (per 1M tokens):**
- GPT-4o: $2.50 input / $10.00 output
- Gemini 2.5 Flash: $0.075 input / $0.30 output
- **Savings: ~97% cheaper!**

---

## Quick Setup (2 minutes)

### Step 1: Get Gemini API Key

1. **Go to**: https://aistudio.google.com/app/apikey
2. **Sign in** with your Google account
3. **Click** "Create API Key"
4. **Copy** your API key

### Step 2: Update Your .env File

Open your `.env` file and add:

```env
# Google Gemini (DEFAULT - already set!)
FEATURE_LLM_PROVIDER=gemini

# Your Gemini API Key
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Model settings (these are already good defaults)
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=500
```

### Step 3: Install Gemini Package

```bash
# Activate your virtual environment
source venv/bin/activate  # Mac/Linux
# or
.\venv\Scripts\Activate.ps1  # Windows

# Install the Gemini package
pip install google-generativeai==0.8.3
```

### Step 4: Restart Your Server

```bash
# Stop server (Ctrl+C)

# Start again
python -m uvicorn server.main:app --reload
```

You should see:
```
INFO: Initialized Google Gemini 2.5 Flash LLM provider
```

### Step 5: Test!

Call your number and have a conversation. It works exactly the same but faster and cheaper!

---

## Performance Comparison

| Feature | GPT-4o | Gemini 2.5 Flash |
|---------|--------|------------------|
| Latency | ~800ms | ~400ms ⚡ |
| Cost per call | $0.02 | $0.001 💰 |
| Function calling | ✅ | ✅ |
| Context window | 128K | 1M tokens |
| Free tier | $5 credit | 1500 requests/day |

---

## Gemini Models Available

```env
# Default: Gemini 2.5 Flash (fastest, cheapest, latest)
GEMINI_MODEL=gemini-2.5-flash

# Gemini 2.0 Flash (previous version)
GEMINI_MODEL=gemini-2.0-flash-exp

# Gemini 1.5 Flash (stable version)
GEMINI_MODEL=gemini-1.5-flash

# Gemini 1.5 Pro (more capable, slower)
GEMINI_MODEL=gemini-1.5-pro
```

**Recommendation**: Use `gemini-2.5-flash` for voice applications - it's the latest and best!

---

## Switching Back to GPT-4o or Claude

Just change one line in `.env`:

```env
# Use GPT-4o
FEATURE_LLM_PROVIDER=openai

# Use Claude
FEATURE_LLM_PROVIDER=anthropic

# Use Gemini
FEATURE_LLM_PROVIDER=gemini
```

No code changes needed!

---

## Troubleshooting

### "API key not valid"

- Make sure you copied the full API key
- No spaces or quotes around the key
- Get a new one at https://aistudio.google.com/app/apikey

### "Rate limit exceeded"

Free tier limits:
- 15 requests per minute
- 1500 requests per day
- 1M tokens per day

For production, enable billing at https://console.cloud.google.com/

### "Module not found: google.generativeai"

```bash
pip install google-generativeai==0.8.3
```

### Lower latency tips

1. Reduce `GEMINI_MAX_TOKENS` to 300-400
2. Use shorter system prompts
3. Keep conversation history to last 5 turns

---

## Free Tier Limits

**Gemini 2.5 Flash Free Tier:**
- ✅ 1500 requests per day
- ✅ 1 million tokens per day
- ✅ 15 requests per minute

**Enough for:**
- ~750 phone calls per day (2 requests/call avg)
- Perfect for testing and small deployments

**When to upgrade:**
- Production deployments
- > 500 calls/day
- Need higher rate limits

**Pricing (paid tier):**
- $0.075 per 1M input tokens
- $0.30 per 1M output tokens
- Still ~97% cheaper than GPT-4o!

---

## Best Practices

### 1. Monitor Usage

Check usage at: https://aistudio.google.com/app/apikey

### 2. Cache System Prompts

Gemini supports context caching - can save even more!

### 3. Optimize Prompts

Shorter prompts = lower latency + lower cost

### 4. Test Different Temperatures

```env
GEMINI_TEMPERATURE=0.5  # More focused
GEMINI_TEMPERATURE=0.7  # Balanced (default)
GEMINI_TEMPERATURE=0.9  # More creative
```

For voice calls, `0.7` is usually best.

---

## What Changes?

✅ **Works exactly the same** - same function calling, same actions  
✅ **Same conversation quality** - excellent understanding  
✅ **Same safety guardrails** - medical advice refusal, etc.  
✅ **Faster responses** - lower latency  
✅ **Much cheaper** - 97% cost reduction  

**Nothing in your code needs to change!** Just swap the API key.

---

## Production Deployment

For production with high volume:

1. **Enable billing** at https://console.cloud.google.com/billing
2. **Set up quotas** to avoid surprise bills
3. **Monitor costs** in Google Cloud Console
4. **Consider multiple API keys** for failover

---

## Support & Resources

- **Gemini Docs**: https://ai.google.dev/docs
- **API Reference**: https://ai.google.dev/api/python
- **Pricing**: https://ai.google.dev/pricing
- **Status Page**: https://status.cloud.google.com/

---

## Summary

✅ **You're now using Gemini 2.5 Flash!**

**Your setup:**
```env
FEATURE_LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
```

**Benefits:**
- ⚡ Faster responses
- 💰 97% cheaper
- 🎯 Same quality
- 🆓 Generous free tier

**Next steps:**
1. Test it with some calls
2. Monitor your usage
3. Enjoy the cost savings!

---

**Questions?** See the main README.md or create an issue on GitHub.

**Happy calling!** 📞✨

