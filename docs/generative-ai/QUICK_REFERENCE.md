# Generative AI - Quick Reference Guide

## One-Page Overview

This quick reference provides essential information for getting started with generative AI integration in the MNR Real-Time Service.

## Quick Decision Tree

```
┌─────────────────────────────────────────────────────────────┐
│  Do you want to add AI features to MNR RT Service?          │
└────────────────────────┬────────────────────────────────────┘
                         │
                    Yes  │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  What's your priority?                                       │
├──────────────────┬──────────────────┬───────────────────────┤
│  Fast & Easy     │  Privacy         │  Production Quality   │
│  (Testing)       │  (No Cloud)      │  (Best Accuracy)      │
└────────┬─────────┴────────┬─────────┴─────────┬─────────────┘
         │                  │                    │
         ▼                  ▼                    ▼
    Cloud API          Local Model           RAG System
    $50-200/mo         $80 one-time          $100-300/mo
    2 hours setup      2-3 days setup        2-4 weeks setup
    95% accuracy       85% accuracy          98% accuracy
```

## Implementation Options Comparison

| Feature | Cloud API | Local Model | RAG System |
|---------|-----------|-------------|------------|
| **Setup Time** | 2 hours | 2-3 days | 2-4 weeks |
| **Monthly Cost** | $50-200 | $0 (after hardware) | $100-300 |
| **Initial Cost** | $0 | $80-500 (hardware) | $0-200 |
| **Accuracy** | 90-95% | 80-90% | 95-99% |
| **Speed** | Fast (1-2s) | Medium (3-5s) | Fast (1-3s) |
| **Privacy** | Low (data sent to cloud) | High (local only) | Medium (hybrid) |
| **Maintenance** | Low | Medium | Medium-High |
| **Scalability** | High | Low-Medium | High |
| **Internet Required** | Yes | No | Yes |
| **Best For** | Quick testing, prototypes | Privacy-sensitive, offline | Production, high accuracy |

## 30-Minute Quick Start

### Prerequisites
```bash
# Install dependencies
pip install openai langchain

# Get API key from https://platform.openai.com/
export OPENAI_API_KEY="sk-your-key-here"
```

### Minimal Code
```python
# src/ai_helper.py
import openai
import json

class SimpleAI:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def ask(self, question, train_data):
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Question: {question}\nTrain Data: {json.dumps(train_data)}\nAnswer:"
            }],
            max_tokens=200
        )
        return response.choices[0].message.content

# Usage
ai = SimpleAI("your-api-key")
answer = ai.ask("When's the next train?", {"trains": [...]})
print(answer)
```

### Add to Flask API
```python
# web_server.py
from src.ai_helper import SimpleAI

ai = SimpleAI(os.getenv('OPENAI_API_KEY'))

@app.route('/ai/query', methods=['POST'])
def ai_query():
    query = request.json['query']
    trains = get_current_trains()  # Your existing function
    answer = ai.ask(query, trains)
    return jsonify({"response": answer})
```

### Test It
```bash
curl -X POST http://localhost:5000/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query": "When is the next train to Stamford?"}'
```

## Common Patterns

### Pattern 1: Natural Language to API Parameters
```python
def extract_intent(query: str) -> dict:
    """Convert 'next train to Stamford' → {destination: 'Stamford'}"""
    response = llm.generate(f"Extract intent from: {query}")
    return json.loads(response)
```

### Pattern 2: Data to Natural Language
```python
def humanize_data(data: dict) -> str:
    """Convert JSON → 'Your train leaves in 5 minutes'"""
    return llm.generate(f"Explain this data naturally: {data}")
```

### Pattern 3: RAG (Grounded Responses)
```python
def answer_with_context(query: str) -> str:
    """Prevent hallucinations by including facts"""
    facts = vector_db.search(query)
    real_data = get_current_trains()
    return llm.generate(f"Facts: {facts}\nData: {real_data}\nQ: {query}")
```

### Pattern 4: Validation
```python
def validate_response(ai_response: str, actual_data: dict) -> bool:
    """Verify AI didn't make up facts"""
    mentioned_times = extract_times(ai_response)
    for time in mentioned_times:
        if time not in actual_data:
            return False
    return True
```

## Essential Code Snippets

### Caching (Save Money)
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def cached_query(query: str) -> str:
    return ai.ask(query, get_trains())
```

### Rate Limiting (Prevent Abuse)
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/ai/query')
@limiter.limit("10 per minute")
def ai_query():
    pass
```

### Error Handling
```python
def safe_ai_query(query: str) -> dict:
    try:
        response = ai.ask(query, get_trains())
        return {"success": True, "response": response}
    except Exception as e:
        logger.error(f"AI error: {e}")
        return {"success": False, "fallback": get_trains()}
```

### Cost Tracking
```python
import tiktoken

def estimate_cost(prompt: str, response: str, model: str = "gpt-4"):
    encoder = tiktoken.encoding_for_model(model)
    input_tokens = len(encoder.encode(prompt))
    output_tokens = len(encoder.encode(response))
    
    # GPT-4 pricing
    cost = (input_tokens * 0.03 + output_tokens * 0.06) / 1000
    return cost
```

## Best Practices Checklist

### Before Launch
- [ ] Implement caching (reduces costs by 50%+)
- [ ] Add rate limiting (prevent abuse)
- [ ] Validate responses (catch hallucinations)
- [ ] Set up error handling (fallback to regular API)
- [ ] Add logging (track usage and costs)
- [ ] Test with real users (10+ people)
- [ ] Monitor costs (set alerts at $50, $100, $200)

### For Production
- [ ] Use response validation
- [ ] Implement confidence scoring
- [ ] Add monitoring (Prometheus/Grafana)
- [ ] Set up cost alerts
- [ ] Create fallback mechanisms
- [ ] Document API changes
- [ ] Train support team
- [ ] Collect user feedback

### For Privacy
- [ ] Review data sent to LLM APIs
- [ ] Remove PII before processing
- [ ] Consider local models for sensitive data
- [ ] Add opt-out mechanism
- [ ] Document data handling
- [ ] Comply with privacy regulations

## Cost Calculator

### GPT-4 (High Quality)
```
Cost per query: ~$0.05
1,000 queries/day = $50/day = $1,500/month

With 50% cache hit rate: $750/month
With 70% cache hit rate: $450/month
```

### GPT-3.5-Turbo (Budget)
```
Cost per query: ~$0.005
1,000 queries/day = $5/day = $150/month

With 50% cache hit rate: $75/month
With 70% cache hit rate: $45/month
```

### Claude (Alternative)
```
Cost per query: ~$0.04
1,000 queries/day = $40/day = $1,200/month

With 50% cache hit rate: $600/month
```

### Local Model (Phi-3)
```
Hardware: $80-500 (one-time)
Electricity: ~$10/month
Total first year: $80-500 + $120 = $200-620
Total per query: $0.00 (unlimited)
```

## Troubleshooting Fast Reference

| Problem | Quick Fix |
|---------|-----------|
| Rate limit error | Add exponential backoff |
| Slow responses | Reduce max_tokens, use faster model |
| High costs | Add caching, use GPT-3.5 instead of GPT-4 |
| Hallucinations | Implement RAG, add validation |
| Privacy concerns | Switch to local models |
| API timeout | Increase timeout, reduce prompt length |
| Out of memory | Use smaller model, reduce batch size |

## Testing Checklist

### Basic Tests
```bash
# Test 1: Simple query
curl -X POST /ai/query -d '{"query": "next train?"}'

# Test 2: Complex query  
curl -X POST /ai/query -d '{"query": "I need to be in Stamford by 2 PM"}'

# Test 3: Invalid query
curl -X POST /ai/query -d '{"query": ""}'

# Test 4: Rate limit
for i in {1..20}; do curl -X POST /ai/query -d '{"query": "test"}'; done
```

### Validation Tests
```python
# Test hallucination detection
response = ai.ask("When's the train to Mars?")
assert "Mars" not in response  # Should refuse or clarify

# Test accuracy
response = ai.ask("Next train to Stamford?")
actual_next_train = get_trains()[0]
assert actual_next_train['destination'] in response
```

## Key Metrics to Track

```python
# Add to your monitoring
metrics = {
    'requests_per_hour': 0,
    'average_response_time': 0,
    'cache_hit_rate': 0,
    'cost_per_request': 0,
    'error_rate': 0,
    'validation_failures': 0,  # Hallucinations caught
    'user_satisfaction': 0      # From feedback
}
```

## When to Use What

### Use Cloud API When:
- ✅ Just testing/prototyping
- ✅ Need best quality responses
- ✅ Don't have powerful hardware
- ✅ Want fast setup
- ✅ Low to medium query volume (<10,000/day)

### Use Local Model When:
- ✅ Privacy is critical
- ✅ Need to work offline
- ✅ High query volume (>50,000/day)
- ✅ Have GPU hardware
- ✅ Want no ongoing costs

### Use RAG When:
- ✅ Need high accuracy (>95%)
- ✅ Have lots of domain knowledge
- ✅ Building production system
- ✅ Can invest time in setup
- ✅ Want grounded responses

## Resources Quick Links

### Documentation
- [Full README](./README.md) - Complete overview
- [Use Cases](./USE_CASES.md) - Real-world scenarios
- [Implementation Guide](./IMPLEMENTATION_GUIDE.md) - Step-by-step
- [Index](./INDEX.md) - Navigation guide

### External Resources
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Anthropic Claude](https://docs.anthropic.com)
- [LangChain](https://python.langchain.com)
- [ChromaDB](https://docs.trychroma.com)
- [Hugging Face](https://huggingface.co/docs)

### Models
- **Cloud**: GPT-4, GPT-3.5, Claude-3
- **Local**: Phi-3, Llama-3, Mistral-7B
- **Embeddings**: text-embedding-ada-002, all-MiniLM-L6-v2

## Sample Prompts

### Good Prompts (Specific, Clear)
```
✅ "You are a Metro-North assistant. Answer using only the provided train data. Be concise."

✅ "Convert this JSON to a friendly sentence: {data}"

✅ "Extract the origin and destination from: 'next train to Stamford'"
```

### Bad Prompts (Vague, Open-ended)
```
❌ "Help with trains"

❌ "Answer any questions"

❌ "Be creative"
```

## Common Mistakes to Avoid

1. ❌ **Not validating responses** → AI makes up facts
   ✅ Always cross-check with actual data

2. ❌ **No caching** → High costs
   ✅ Cache common queries (50%+ savings)

3. ❌ **Using GPT-4 for everything** → Expensive
   ✅ Use GPT-3.5 for simple tasks

4. ❌ **No rate limiting** → API abuse, costs spike
   ✅ Limit to 10-20 requests/minute per user

5. ❌ **Sending full train database** → Slow, expensive
   ✅ Filter relevant data first

6. ❌ **No error handling** → Crashes on API errors
   ✅ Always have fallback to regular API

7. ❌ **Ignoring prompt size** → Wasted tokens
   ✅ Keep prompts under 1000 tokens

## Next Steps

1. **Learn**: Read [README.md](./README.md) for concepts
2. **Explore**: Check [USE_CASES.md](./USE_CASES.md) for scenarios
3. **Build**: Follow [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md)
4. **Reference**: Use this guide for quick lookups

---

**Pro Tip**: Start with the 30-minute quick start, test with real users, then decide whether to invest in RAG or local models based on feedback and usage patterns.

**Last Updated**: 2025-11-09  
**Version**: 1.0
