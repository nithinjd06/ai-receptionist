# Knowledge Base & FAQ Guide

This guide explains how to customize and extend the knowledge base for your AI receptionist.

## Overview

The AI receptionist has two types of knowledge:

1. **FAQ Knowledge Base** - Static Q&A for common questions (hours, location, policies)
2. **LLM Knowledge** - Dynamic understanding through GPT-4o's general knowledge

Both work together to provide accurate, helpful responses.

---

## FAQ Knowledge Base

### Location

All FAQ data is stored in:
```
ai_receptionist/data/faq.json
```

### Format

```json
{
  "category_name": {
    "question": "Example question that customers might ask",
    "answer": "The response the AI should give"
  }
}
```

### How It Works

1. **Automatic Loading**: The system loads `faq.json` on startup
2. **LLM Context**: FAQ data is added to GPT-4o's system prompt
3. **Natural Matching**: The AI understands question variations
   - "What are your hours?" 
   - "When are you open?"
   - "What time do you close?"
   → All trigger the same "hours" FAQ answer

4. **Action Logging**: All FAQ responses are logged as `action: answer_faq`

### Example: Medical Office

```json
{
  "hours": {
    "question": "What are your office hours?",
    "answer": "We're open Monday-Friday, 8 AM to 5 PM. Closed weekends and holidays."
  },
  "location": {
    "question": "Where are you located?",
    "answer": "123 Main Street, Suite 100, Dallas, TX 75201"
  },
  "insurance": {
    "question": "What insurance do you accept?",
    "answer": "We accept Blue Cross, UnitedHealthcare, Aetna, and Cigna."
  },
  "new_patient": {
    "question": "Do you accept new patients?",
    "answer": "Yes! Please bring your insurance card and ID to your first visit."
  }
}
```

### Example: Restaurant

```json
{
  "hours": {
    "question": "What are your hours?",
    "answer": "We're open Tuesday-Sunday, 5 PM to 10 PM. Closed Mondays."
  },
  "reservations": {
    "question": "Do I need a reservation?",
    "answer": "We recommend reservations, especially on weekends. I can help you book one now!"
  },
  "menu": {
    "question": "What type of food do you serve?",
    "answer": "We specialize in modern Italian cuisine with locally-sourced ingredients."
  },
  "parking": {
    "question": "Is parking available?",
    "answer": "Yes, free valet parking is available at our main entrance."
  },
  "dress_code": {
    "question": "What's the dress code?",
    "answer": "Smart casual. We ask that guests avoid shorts and flip-flops."
  }
}
```

### Example: Retail Store

```json
{
  "hours": {
    "question": "When are you open?",
    "answer": "Monday-Saturday 9 AM to 8 PM, Sunday 11 AM to 6 PM."
  },
  "returns": {
    "question": "What's your return policy?",
    "answer": "We accept returns within 30 days with receipt for full refund."
  },
  "shipping": {
    "question": "Do you offer shipping?",
    "answer": "Yes! Free shipping on orders over $50. Standard shipping is $5.99."
  },
  "store_credit": {
    "question": "Do you have store credit?",
    "answer": "Yes, we offer store credit for returns without receipt."
  }
}
```

---

## Customizing Your Knowledge Base

### Step 1: Edit faq.json

```bash
cd ai_receptionist
nano data/faq.json  # or use any text editor
```

### Step 2: Add Your Business Info

Replace the example data with YOUR information:

```json
{
  "hours": {
    "question": "What are your hours?",
    "answer": "YOUR ACTUAL HOURS HERE"
  },
  "location": {
    "question": "Where are you located?",
    "answer": "YOUR ACTUAL ADDRESS HERE"
  }
}
```

### Step 3: Add Custom FAQs

Add new categories for your specific needs:

```json
{
  "pricing": {
    "question": "How much does it cost?",
    "answer": "Our services start at $X. I can schedule a consultation to discuss specific pricing."
  },
  "wifi": {
    "question": "Do you have WiFi?",
    "answer": "Yes! Free WiFi is available. The password is GuestWiFi2024."
  },
  "gift_cards": {
    "question": "Do you sell gift cards?",
    "answer": "Yes! Gift cards are available in any amount at our location or online."
  }
}
```

### Step 4: Restart Server

The FAQ is loaded on startup, so restart to apply changes:

```bash
# Stop server (Ctrl+C)
# Start again
python -m uvicorn server.main:app --reload
```

---

## Advanced: Dynamic FAQ Loading

The system now includes a `FAQKnowledgeBase` class that:
- Loads FAQs automatically
- Injects them into LLM context
- Supports runtime updates (with save)

### Adding FAQs Programmatically

```python
from server.convo.faq_loader import faq_kb

# Add a new FAQ
faq_kb.add_faq(
    category="holiday_hours",
    question="What are your holiday hours?",
    answer="We're open 10 AM to 4 PM on most holidays. Closed Christmas and Thanksgiving."
)

# This automatically saves to faq.json
```

### Searching FAQs

```python
# Search for matching FAQ
answer = faq_kb.search_faq("when are you open")
# Returns the best matching answer
```

---

## Best Practices

### 1. Keep Answers Concise
```json
// ❌ BAD - Too long
"hours": {
  "answer": "Well, let me tell you about our hours. We open at 8 AM on weekdays, which is Monday through Friday, and we're open until 5 PM on those days. On weekends, that's Saturday and Sunday, we're closed. We're also closed on holidays like Christmas, Thanksgiving, New Year's Day, and Labor Day."
}

// ✅ GOOD - Clear and concise
"hours": {
  "answer": "We're open Monday-Friday, 8 AM to 5 PM. Closed weekends and major holidays."
}
```

### 2. Include Next Steps
```json
// ❌ OK - Just answers
"insurance": {
  "answer": "We accept Blue Cross, Aetna, and Cigna."
}

// ✅ BETTER - Includes action
"insurance": {
  "answer": "We accept Blue Cross, Aetna, and Cigna. Would you like to schedule an appointment?"
}
```

### 3. Handle Common Variations

The AI automatically understands variations, but ensure your answer works for all:

```json
"location": {
  "question": "Where are you located?",  // Also handles:
  // "Where is your office?"
  // "What's your address?"
  // "How do I find you?"
  // "Where are you?"
  "answer": "We're at 123 Main St, Dallas, TX. Parking in rear."
}
```

### 4. Redirect Complex Questions

```json
"medical_advice": {
  "question": "What should I take for my symptoms?",
  "answer": "I'm not able to provide medical advice. Let me schedule you with one of our providers who can help. What day works for you?"
}
```

---

## Testing Your Knowledge Base

### 1. Test Each FAQ

Call your number and ask questions different ways:

```
FAQ: hours
Test: "What are your hours?"
Test: "When are you open?"
Test: "What time do you close?"
Test: "Are you open on Saturday?"
```

### 2. Check Logs

Watch server logs to see which FAQ triggered:

```
INFO: Turn 1: action=answer_faq, category=hours, latency=1200ms
```

### 3. Review Call History

```bash
curl -u admin:password http://localhost:8000/admin/calls
```

Look for `action: "answer_faq"` and verify responses are correct.

---

## FAQ vs Conversation

### Use FAQ For:
- ✅ Facts that never change (address, hours)
- ✅ Policies (returns, cancellations)
- ✅ Common questions (parking, wifi)
- ✅ Quick factual answers

### Use Conversation (LLM) For:
- ✅ Dynamic responses (scheduling, availability)
- ✅ Follow-up questions
- ✅ Personalized interactions
- ✅ Multi-step processes

### Example Flow:

```
Caller: "What are your hours?"
→ FAQ answer: "We're open 9 AM to 5 PM, Monday-Friday"

Caller: "Can I come in today at 3 PM?"
→ LLM conversation: "Let me check... Yes! I can schedule you for 3 PM today. 
                     What type of appointment do you need?"

Caller: "A consultation"
→ LLM + Calendar: "Perfect! I've scheduled your consultation for today at 3 PM. 
                   You'll receive a confirmation text shortly."
```

---

## Updating FAQs Over Time

### Track Common Questions

Review call logs monthly to find:
- Questions that get asked frequently
- Questions the AI struggles with
- New services/policies to add

### Seasonal Updates

```json
// Summer hours
"summer_hours": {
  "question": "What are your summer hours?",
  "answer": "During summer (June-August), we're open 7 AM to 6 PM Monday-Friday."
}

// Holiday schedule
"holiday_schedule": {
  "question": "Are you open during the holidays?",
  "answer": "We're closed December 24-26 and January 1st. Regular hours otherwise."
}
```

### A/B Testing Responses

Try different answers and see which get better outcomes:

```json
// Version A
"pricing": {
  "answer": "Consultations are $150."
}

// Version B (better - includes value)
"pricing": {
  "answer": "Consultations are $150 and include a comprehensive assessment. 
            Would you like to schedule one?"
}
```

---

## Troubleshooting

### AI Not Using FAQ

**Symptom**: AI gives wrong answer despite FAQ existing

**Solutions**:
1. Check `faq.json` is valid JSON (use https://jsonlint.com)
2. Restart server to reload FAQ
3. Check logs for FAQ loading: `Loaded X FAQ entries`
4. Verify question phrasing matches user's question

### FAQ Too Long

**Symptom**: Responses feel robotic or too wordy

**Solution**: Edit to be more concise and conversational

### Conflicting Information

**Symptom**: FAQ says one thing, AI says another

**Solution**: The FAQ should be the source of truth. Update it and restart.

---

## Summary

✅ **You have a knowledge base!** It's in `data/faq.json`

✅ **Easy to customize** - Just edit the JSON file

✅ **Automatic integration** - FAQ loaded into every conversation

✅ **Natural understanding** - AI handles question variations

✅ **EHR integration possible** - See `EHR_INTEGRATION_GUIDE.md`

Your AI receptionist is ready to answer questions about your business!

