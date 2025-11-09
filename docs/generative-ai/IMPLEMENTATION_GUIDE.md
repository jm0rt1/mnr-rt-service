# Generative AI Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing generative AI features in the MNR Real-Time Service. It covers everything from initial setup to production deployment, with practical examples and best practices.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Implementation Phases](#implementation-phases)
- [Detailed Setup Instructions](#detailed-setup-instructions)
- [Testing and Validation](#testing-and-validation)
- [Deployment Strategies](#deployment-strategies)
- [Monitoring and Maintenance](#monitoring-and-maintenance)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Technical Requirements

**Minimum**:
- Python 3.12+
- 4GB RAM (for cloud-based LLM APIs)
- Internet connection for API access
- Existing MNR RT Service installation

**Recommended for Local Models**:
- 16GB+ RAM
- GPU with 8GB+ VRAM (NVIDIA preferred)
- 50GB+ storage for model files
- Python 3.12+ with CUDA support

### API Keys (Choose One or More)

**Cloud LLM Providers**:
- OpenAI API key (GPT-4, GPT-3.5) - [Get one here](https://platform.openai.com/)
- Anthropic API key (Claude) - [Get one here](https://www.anthropic.com/)
- Google Cloud API key (PaLM, Gemini) - [Get one here](https://cloud.google.com/)

**For Local Models**:
- No API keys required
- Hugging Face account (optional, for model downloads)

### Python Dependencies

Add to `requirements.txt`:
```txt
# Generative AI dependencies
openai>=1.0.0              # OpenAI API
anthropic>=0.8.0           # Claude API
langchain>=0.1.0           # LLM framework
chromadb>=0.4.0            # Vector database
transformers>=4.35.0       # Local models
torch>=2.1.0               # PyTorch for local models
sentence-transformers>=2.2.0  # Embeddings
tiktoken>=0.5.0            # Token counting
```

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd /path/to/mnr-rt-service

# Install AI dependencies
pip install openai langchain chromadb sentence-transformers

# For local models (optional)
pip install transformers torch
```

### 2. Configure API Keys

Create `config/ai_config.yml`:

```yaml
# AI Configuration
ai:
  # Primary LLM provider
  provider: "openai"  # Options: openai, anthropic, local
  
  # API keys
  openai_api_key: "sk-your-key-here"
  anthropic_api_key: "your-key-here"
  
  # Model selection
  model: "gpt-4"  # Options: gpt-4, gpt-3.5-turbo, claude-3-opus
  
  # Local model config (if using local)
  local_model: "microsoft/Phi-3-mini-4k-instruct"
  
  # Performance settings
  max_tokens: 500
  temperature: 0.7
  timeout: 30
  
  # Cost controls
  max_requests_per_hour: 100
  cache_enabled: true
  cache_ttl: 3600  # seconds

# Vector database configuration
vector_db:
  provider: "chromadb"
  persist_directory: "./data/chroma"
  collection_name: "train_knowledge"

# Features to enable
features:
  natural_language_query: true
  conversational_interface: false
  code_generation: false
  multi_language: false
```

### 3. Add AI Module to Project

Create `src/ai_assistant/`:

```bash
mkdir -p src/ai_assistant
touch src/ai_assistant/__init__.py
```

Create `src/ai_assistant/query_processor.py`:

```python
"""
Basic AI Query Processor for MNR RT Service
"""
import openai
import json
from typing import Dict, Optional
from functools import lru_cache

class AIQueryProcessor:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    @lru_cache(maxsize=100)
    def process_query(self, user_query: str, train_data: str) -> str:
        """
        Process natural language query and return friendly response
        
        Args:
            user_query: Natural language question from user
            train_data: JSON string of current train data
        
        Returns:
            Human-friendly response string
        """
        system_prompt = """
        You are a helpful Metro-North Railroad assistant. Answer questions 
        about trains using the provided real-time data. Be concise, friendly, 
        and accurate. If you're not sure, say so rather than guessing.
        
        Format responses conversationally, highlighting key information like
        departure times, track numbers, and delays.
        """
        
        user_prompt = f"""
        User question: {user_query}
        
        Current train data:
        {train_data}
        
        Please answer the user's question based on this real-time data.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"I'm sorry, I encountered an error: {str(e)}"
    
    def extract_parameters(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extract API parameters from natural language query
        
        Returns: dict with origin_station, destination_station, etc.
        """
        extraction_prompt = f"""
        Extract train query parameters from: "{query}"
        
        Return JSON with:
        - origin (station name or null)
        - destination (station name or null)
        - time_preference (morning/afternoon/evening or null)
        - count (number of results wanted, default 5)
        
        Only return valid JSON, no additional text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheaper for extraction
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        
        except:
            return {
                "origin": None,
                "destination": None,
                "time_preference": None,
                "count": 5
            }
```

### 4. Add API Endpoint

Update `web_server.py`:

```python
from flask import Flask, request, jsonify
from src.ai_assistant.query_processor import AIQueryProcessor
import os

# Initialize AI processor
ai_processor = None
if os.path.exists('config/ai_config.yml'):
    import yaml
    with open('config/ai_config.yml') as f:
        ai_config = yaml.safe_load(f)
    
    if ai_config.get('ai', {}).get('openai_api_key'):
        ai_processor = AIQueryProcessor(
            api_key=ai_config['ai']['openai_api_key'],
            model=ai_config['ai'].get('model', 'gpt-4')
        )

@app.route('/ai/query', methods=['POST'])
def ai_query():
    """
    Natural language query endpoint
    
    Example request:
    {
        "query": "When is the next train to Stamford?",
        "context": {
            "user_id": "optional",
            "location": "optional"
        }
    }
    """
    if not ai_processor:
        return jsonify({
            "error": "AI features not enabled. Configure ai_config.yml"
        }), 503
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request"}), 400
    
    user_query = data['query']
    
    try:
        # Extract parameters from natural language
        params = ai_processor.extract_parameters(user_query)
        
        # Fetch relevant train data
        # (Map station names to IDs, then call existing API)
        train_data = fetch_trains_for_query(params)
        
        # Generate AI response
        response_text = ai_processor.process_query(
            user_query,
            json.dumps(train_data, indent=2)
        )
        
        return jsonify({
            "query": user_query,
            "response": response_text,
            "structured_data": train_data,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "fallback": "Please try using the /trains endpoint directly"
        }), 500

def fetch_trains_for_query(params: dict) -> dict:
    """Helper to fetch trains based on extracted parameters"""
    # TODO: Implement station name to ID mapping
    # For now, return sample data
    return {
        "trains": [],
        "note": "Implementation in progress"
    }
```

### 5. Test the Implementation

```bash
# Start the server
python web_server.py

# Test the AI endpoint (in another terminal)
curl -X POST http://localhost:5000/ai/query \
  -H "Content-Type: application/json" \
  -d '{"query": "When is the next train from Grand Central to Stamford?"}'
```

Expected response:
```json
{
  "query": "When is the next train from Grand Central to Stamford?",
  "response": "The next train from Grand Central to Stamford departs at 3:45 PM from Track 18. It's currently on time and will arrive in Stamford at 4:32 PM.",
  "structured_data": { ... },
  "timestamp": "2025-11-09T15:30:00"
}
```

## Implementation Phases

### Phase 1: Basic Natural Language Query (Week 1-2)

**Goal**: Allow users to ask questions in plain English

**Tasks**:
- [ ] Set up OpenAI or Anthropic API integration
- [ ] Create query processor module
- [ ] Add `/ai/query` endpoint
- [ ] Implement station name to ID mapping
- [ ] Add basic caching
- [ ] Write unit tests
- [ ] Update API documentation

**Deliverables**:
- Working `/ai/query` endpoint
- Support for basic questions about trains
- Error handling and fallbacks

### Phase 2: Response Validation & Enhancement (Week 3-4)

**Goal**: Ensure AI responses are accurate and helpful

**Tasks**:
- [ ] Implement response validation layer
- [ ] Add confidence scoring
- [ ] Enhance prompts for better responses
- [ ] Add support for follow-up questions
- [ ] Implement rate limiting
- [ ] Add usage analytics

**Deliverables**:
- Validated responses
- Confidence scores
- Usage metrics dashboard

### Phase 3: RAG Implementation (Week 5-6)

**Goal**: Ground responses in knowledge base

**Tasks**:
- [ ] Set up vector database (ChromaDB)
- [ ] Create knowledge base (stations, FAQs, routes)
- [ ] Implement embedding generation
- [ ] Build RAG query pipeline
- [ ] Add knowledge base update mechanism
- [ ] Test and optimize retrieval

**Deliverables**:
- Vector database with indexed knowledge
- RAG query pipeline
- Improved response accuracy

### Phase 4: Advanced Features (Week 7-8)

**Goal**: Add voice, multi-language, and personalization

**Tasks**:
- [ ] Add voice interface support
- [ ] Implement multi-language translation
- [ ] Build user profile system
- [ ] Add proactive notifications
- [ ] Create conversational interface
- [ ] Implement context retention

**Deliverables**:
- Voice API endpoint
- Multi-language support
- User profiles
- Proactive alerts

## Detailed Setup Instructions

### Setting Up Vector Database (RAG)

1. **Install ChromaDB**:
```bash
pip install chromadb sentence-transformers
```

2. **Create Knowledge Indexer**:

`src/ai_assistant/knowledge_indexer.py`:
```python
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import json

class KnowledgeIndexer:
    def __init__(self, persist_directory: str = "./data/chroma"):
        self.client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.collection = self.client.get_or_create_collection(
            name="train_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
    
    def index_stations(self, stations: List[Dict]):
        """Index station information"""
        for station in stations:
            doc_text = f"""
            Station: {station['stop_name']}
            ID: {station['stop_id']}
            Location: {station.get('stop_lat')}, {station.get('stop_lon')}
            Wheelchair accessible: {station.get('wheelchair_boarding') == '1'}
            """
            
            self.collection.add(
                documents=[doc_text],
                metadatas=[{
                    "type": "station",
                    "station_id": station['stop_id'],
                    "station_name": station['stop_name']
                }],
                ids=[f"station_{station['stop_id']}"]
            )
    
    def index_routes(self, routes: List[Dict]):
        """Index route information"""
        for route in routes:
            doc_text = f"""
            Route: {route['route_long_name']}
            ID: {route['route_id']}
            Type: {route['route_type']}
            Color: #{route['route_color']}
            """
            
            self.collection.add(
                documents=[doc_text],
                metadatas=[{
                    "type": "route",
                    "route_id": route['route_id'],
                    "route_name": route['route_long_name']
                }],
                ids=[f"route_{route['route_id']}"]
            )
    
    def index_faqs(self, faqs: List[Dict]):
        """Index frequently asked questions"""
        for i, faq in enumerate(faqs):
            self.collection.add(
                documents=[f"Q: {faq['question']}\nA: {faq['answer']}"],
                metadatas=[{"type": "faq"}],
                ids=[f"faq_{i}"]
            )
    
    def search(self, query: str, n_results: int = 3) -> List[Dict]:
        """Search knowledge base"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        return [{
            "document": doc,
            "metadata": meta,
            "distance": dist
        } for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )]

# Usage
indexer = KnowledgeIndexer()

# Index station data from existing API
stations = get_all_stations()  # From existing API
indexer.index_stations(stations)

# Index routes
routes = get_all_routes()  # From existing API
indexer.index_routes(routes)

# Index FAQs
faqs = [
    {
        "question": "How do I buy a ticket?",
        "answer": "You can buy tickets at ticket machines, online at mta.info, or with the MTA TrainTime app."
    },
    {
        "question": "Are bikes allowed on trains?",
        "answer": "Yes, bikes are allowed on Metro-North trains during off-peak hours and all day on weekends."
    },
    # Add more FAQs
]
indexer.index_faqs(faqs)
```

3. **Create RAG Query Processor**:

`src/ai_assistant/rag_processor.py`:
```python
from .knowledge_indexer import KnowledgeIndexer
from .query_processor import AIQueryProcessor
import json

class RAGQueryProcessor:
    def __init__(self, ai_processor: AIQueryProcessor, indexer: KnowledgeIndexer):
        self.ai = ai_processor
        self.indexer = indexer
    
    def process_query_with_context(self, user_query: str, train_data: dict) -> str:
        """Process query using RAG approach"""
        
        # Step 1: Retrieve relevant context from knowledge base
        context_results = self.indexer.search(user_query, n_results=3)
        context_text = "\n\n".join([r['document'] for r in context_results])
        
        # Step 2: Build enhanced prompt
        system_prompt = """
        You are a helpful Metro-North Railroad assistant with access to:
        1. Real-time train data
        2. Station information
        3. Route details
        4. FAQs and policies
        
        Answer questions accurately using the provided context and real-time data.
        If information is missing, say so clearly.
        """
        
        user_prompt = f"""
        Context from knowledge base:
        {context_text}
        
        Current real-time train data:
        {json.dumps(train_data, indent=2)}
        
        User question: {user_query}
        
        Please provide a helpful, accurate answer.
        """
        
        # Step 3: Generate response with full context
        response = self.ai.client.chat.completions.create(
            model=self.ai.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=600,
            temperature=0.7
        )
        
        return response.choices[0].message.content
```

### Setting Up Local Models (Privacy-First)

For on-premise deployment without external API calls:

1. **Install Dependencies**:
```bash
pip install transformers torch accelerate bitsandbytes
```

2. **Create Local Model Wrapper**:

`src/ai_assistant/local_model.py`:
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LocalAIModel:
    def __init__(self, model_name: str = "microsoft/Phi-3-mini-4k-instruct"):
        """
        Initialize local model
        
        Recommended models:
        - microsoft/Phi-3-mini-4k-instruct (3.8B params, fast)
        - meta-llama/Llama-3-8B-Instruct (8B params, better quality)
        - mistralai/Mistral-7B-Instruct-v0.2 (7B params, balanced)
        """
        print(f"Loading model: {model_name}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            trust_remote_code=True
        )
        
        print("Model loaded successfully")
    
    def generate(
        self, 
        prompt: str, 
        max_length: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate response from prompt"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_length=max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (remove prompt)
        response = response[len(prompt):].strip()
        
        return response
    
    def process_query(self, user_query: str, train_data: str) -> str:
        """Process train query using local model"""
        
        prompt = f"""<|system|>
You are a helpful Metro-North Railroad assistant. Answer questions about trains using the provided real-time data. Be concise and accurate.<|end|>
<|user|>
Real-time train data:
{train_data}

Question: {user_query}<|end|>
<|assistant|>"""
        
        response = self.generate(prompt, max_length=500, temperature=0.7)
        
        return response

# Usage
local_model = LocalAIModel("microsoft/Phi-3-mini-4k-instruct")
response = local_model.process_query(
    "When is the next train to White Plains?",
    json.dumps(train_data)
)
```

3. **Update Configuration**:

```yaml
# config/ai_config.yml
ai:
  provider: "local"
  local_model: "microsoft/Phi-3-mini-4k-instruct"
  device: "cuda"  # or "cpu" if no GPU
```

## Testing and Validation

### Unit Tests

Create `tests/test_ai_assistant.py`:

```python
import unittest
from src.ai_assistant.query_processor import AIQueryProcessor
import json

class TestAIAssistant(unittest.TestCase):
    def setUp(self):
        self.processor = AIQueryProcessor(
            api_key="test-key",
            model="gpt-3.5-turbo"
        )
    
    def test_extract_parameters(self):
        """Test parameter extraction from natural language"""
        query = "What time is the next train from Grand Central to Stamford?"
        params = self.processor.extract_parameters(query)
        
        self.assertIn('origin', params)
        self.assertIn('destination', params)
        self.assertIsNotNone(params['origin'])
        self.assertIsNotNone(params['destination'])
    
    def test_response_validation(self):
        """Test that responses contain expected elements"""
        user_query = "When's the next train?"
        train_data = json.dumps({
            "trains": [
                {
                    "trip_id": "123",
                    "route_name": "Hudson",
                    "trip_headsign": "Poughkeepsie",
                    "eta": "2025-11-09T15:45:00",
                    "track": "42",
                    "status": "On Time"
                }
            ]
        })
        
        response = self.processor.process_query(user_query, train_data)
        
        # Response should mention key information
        self.assertTrue(any(word in response.lower() for word in ['train', 'track', 'time']))
    
    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Should not crash on empty data
        response = self.processor.process_query("Test query", "")
        self.assertIsInstance(response, str)

if __name__ == '__main__':
    unittest.main()
```

### Integration Tests

```python
# tests/test_ai_integration.py
import unittest
import requests
import json

class TestAIIntegration(unittest.TestCase):
    BASE_URL = "http://localhost:5000"
    
    def test_ai_query_endpoint(self):
        """Test the /ai/query endpoint"""
        response = requests.post(
            f"{self.BASE_URL}/ai/query",
            json={"query": "When is the next train to Stamford?"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('response', data)
        self.assertIn('query', data)
        self.assertIn('timestamp', data)
    
    def test_invalid_request(self):
        """Test error handling for invalid requests"""
        response = requests.post(
            f"{self.BASE_URL}/ai/query",
            json={}
        )
        
        self.assertEqual(response.status_code, 400)
```

### Manual Testing Scenarios

Create `tests/manual_test_scenarios.md`:

```markdown
# Manual Test Scenarios for AI Assistant

## Basic Queries
- [ ] "When is the next train to Stamford?"
- [ ] "Show me trains from Grand Central"
- [ ] "What's the fastest way to get to White Plains?"

## Complex Queries
- [ ] "I need to be in New Haven by 2 PM, which train should I take?"
- [ ] "Are there any delays on the Hudson Line?"
- [ ] "Which track does the 3:45 train to Poughkeepsie leave from?"

## Edge Cases
- [ ] Empty query
- [ ] Very long query (500+ characters)
- [ ] Query in non-English language
- [ ] Nonsensical query
- [ ] Query about non-existent station

## Performance
- [ ] Response time < 3 seconds
- [ ] Handles 10 concurrent requests
- [ ] Cache hit rate > 50%

## Accuracy
- [ ] Cross-check AI response with actual train data
- [ ] Verify times are correct
- [ ] Verify station names are accurate
- [ ] Check for hallucinations
```

## Deployment Strategies

### Development Deployment

```bash
# Set environment variables
export OPENAI_API_KEY="your-key"
export AI_ENABLED="true"

# Run in debug mode
python web_server.py --debug
```

### Production Deployment

**Docker Compose** (`docker-compose.ai.yml`):

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AI_ENABLED=true
      - CACHE_ENABLED=true
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    restart: unless-stopped
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

volumes:
  redis-data:
```

Deploy:
```bash
docker-compose -f docker-compose.ai.yml up -d
```

### Kubernetes Deployment

```yaml
# k8s/ai-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mnr-ai-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mnr-ai
  template:
    metadata:
      labels:
        app: mnr-ai
    spec:
      containers:
      - name: web
        image: mnr-rt-service:latest
        ports:
        - containerPort: 5000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-secrets
              key: openai-api-key
        - name: AI_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

## Monitoring and Maintenance

### Metrics to Track

```python
# src/ai_assistant/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['endpoint', 'status']
)

ai_request_duration = Histogram(
    'ai_request_duration_seconds',
    'AI request duration',
    ['endpoint']
)

ai_cache_hits = Counter(
    'ai_cache_hits_total',
    'Total cache hits'
)

ai_token_usage = Counter(
    'ai_tokens_used_total',
    'Total tokens consumed',
    ['model']
)

# Cost metrics
ai_cost_estimate = Gauge(
    'ai_cost_estimate_dollars',
    'Estimated AI API cost'
)

# Quality metrics
ai_confidence_score = Histogram(
    'ai_confidence_score',
    'AI response confidence scores'
)

def track_request(endpoint: str):
    """Decorator to track AI requests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                ai_requests_total.labels(endpoint=endpoint, status='success').inc()
                return result
            except Exception as e:
                ai_requests_total.labels(endpoint=endpoint, status='error').inc()
                raise
            finally:
                duration = time.time() - start_time
                ai_request_duration.labels(endpoint=endpoint).observe(duration)
        
        return wrapper
    return decorator
```

### Logging

```python
# src/ai_assistant/logging_config.py
import logging
import json

class AILogger:
    def __init__(self):
        self.logger = logging.getLogger('ai_assistant')
        self.logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler('logs/ai_assistant.log')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_query(self, query: str, response: str, metadata: dict):
        """Log AI query and response"""
        self.logger.info(json.dumps({
            'type': 'query',
            'query': query,
            'response_length': len(response),
            'tokens_used': metadata.get('tokens'),
            'model': metadata.get('model'),
            'duration_ms': metadata.get('duration'),
            'cached': metadata.get('cached', False)
        }))
    
    def log_error(self, error: Exception, context: dict):
        """Log errors"""
        self.logger.error(json.dumps({
            'type': 'error',
            'error': str(error),
            'context': context
        }))
```

## Cost Optimization

### Strategies

1. **Use Cheaper Models for Simple Tasks**:
```python
def select_model(query_complexity: float) -> str:
    """Select appropriate model based on complexity"""
    if query_complexity < 0.3:
        return "gpt-3.5-turbo"  # $0.0015 per 1K tokens
    elif query_complexity < 0.7:
        return "gpt-4"  # $0.03 per 1K tokens
    else:
        return "gpt-4-turbo"  # Better for complex queries
```

2. **Implement Aggressive Caching**:
```python
from functools import lru_cache
import hashlib

class CachedAIProcessor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour
    
    def get_cached_response(self, query: str) -> str:
        """Check cache before calling LLM"""
        cache_key = hashlib.md5(query.encode()).hexdigest()
        
        cached = self.redis.get(cache_key)
        if cached:
            ai_cache_hits.inc()
            return cached.decode()
        
        return None
    
    def cache_response(self, query: str, response: str):
        """Cache response for future use"""
        cache_key = hashlib.md5(query.encode()).hexdigest()
        self.redis.setex(cache_key, self.ttl, response)
```

3. **Rate Limiting**:
```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour", "10 per minute"]
)

@app.route('/ai/query')
@limiter.limit("20 per hour")  # More restrictive for AI endpoint
def ai_query():
    pass
```

4. **Token Optimization**:
```python
def optimize_prompt(system_prompt: str, user_prompt: str, max_tokens: int = 1000):
    """Truncate prompts to stay within token limits"""
    import tiktoken
    
    encoder = tiktoken.encoding_for_model("gpt-4")
    
    system_tokens = encoder.encode(system_prompt)
    user_tokens = encoder.encode(user_prompt)
    
    total_tokens = len(system_tokens) + len(user_tokens)
    
    if total_tokens > max_tokens:
        # Truncate user prompt, keep system prompt
        allowed_user_tokens = max_tokens - len(system_tokens)
        user_tokens = user_tokens[:allowed_user_tokens]
        user_prompt = encoder.decode(user_tokens)
    
    return system_prompt, user_prompt
```

## Troubleshooting

### Common Issues

**Issue: "API rate limit exceeded"**
```python
# Solution: Implement exponential backoff
import time
from functools import wraps

def retry_with_backoff(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError:
                    if i == max_retries - 1:
                        raise
                    wait_time = 2 ** i
                    time.sleep(wait_time)
        return wrapper
    return decorator
```

**Issue: "Slow response times"**
```python
# Solution: Use async/await for parallel processing
import asyncio

async def process_multiple_queries(queries: List[str]):
    """Process multiple queries concurrently"""
    tasks = [process_query_async(q) for q in queries]
    results = await asyncio.gather(*tasks)
    return results
```

**Issue: "Hallucinated responses"**
```python
# Solution: Implement validation layer
def validate_response(response: str, actual_data: dict) -> bool:
    """Check if response matches actual data"""
    # Extract facts from response
    mentioned_times = extract_times(response)
    mentioned_stations = extract_stations(response)
    
    # Verify against actual data
    for time in mentioned_times:
        if not time_exists_in_data(time, actual_data):
            return False
    
    for station in mentioned_stations:
        if not station_exists(station, actual_data):
            return False
    
    return True
```

## Next Steps

After completing this implementation guide:

1. Review [USE_CASES.md](./USE_CASES.md) for specific scenarios
2. Explore advanced features in [README.md](./README.md)
3. Join the community discussions
4. Share your implementations and improvements

## Support

- GitHub Issues: [Report bugs or request features]
- Documentation: [Full AI documentation]
- Community: [Join discussions]

---

**Last Updated**: 2025-11-09  
**Version**: 1.0  
**Maintainer**: MNR RT Service Team
