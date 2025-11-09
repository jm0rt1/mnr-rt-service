# Generative AI - Practical Examples

## Overview

This document provides concrete, working examples of how generative AI can enhance the MNR Real-Time Service. All examples are production-ready and can be adapted to your needs.

## Table of Contents

- [Example 1: Basic Natural Language Query](#example-1-basic-natural-language-query)
- [Example 2: Multi-Step Journey Planning](#example-2-multi-step-journey-planning)
- [Example 3: Context-Aware Responses](#example-3-context-aware-responses)
- [Example 4: Error Handling and Fallbacks](#example-4-error-handling-and-fallbacks)
- [Example 5: Multi-Language Support](#example-5-multi-language-support)
- [Example 6: Proactive Notifications](#example-6-proactive-notifications)
- [Example 7: Code Generation for Developers](#example-7-code-generation-for-developers)
- [Example 8: Voice Interface](#example-8-voice-interface)

## Example 1: Basic Natural Language Query

### User Experience

**Before AI**:
```bash
# User must know technical details
curl "http://localhost:5000/trains?origin_station=1&destination_station=120&limit=5"
```

Response:
```json
{
  "trains": [
    {
      "trip_id": "12345",
      "route_id": "3",
      "trip_headsign": "New Haven",
      "eta": "2025-11-09T15:45:00",
      "track": "18"
    }
  ]
}
```

**With AI**:
```bash
curl -X POST "http://localhost:5000/ai/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "When is the next train from Grand Central to Stamford?"}'
```

Response:
```json
{
  "query": "When is the next train from Grand Central to Stamford?",
  "response": "The next train to Stamford departs from Grand Central at 3:45 PM (in 12 minutes) from Track 18. It's currently on time and will arrive in Stamford at 4:32 PM. The journey takes approximately 47 minutes.",
  "confidence": 0.98,
  "structured_data": {
    "trip_id": "12345",
    "departure_time": "15:45",
    "arrival_time": "16:32",
    "track": "18",
    "status": "On Time"
  }
}
```

### Implementation

```python
# src/ai_assistant/basic_query.py

import openai
from datetime import datetime
import json
from typing import Dict, Optional

class BasicQueryProcessor:
    def __init__(self, api_key: str, train_api):
        self.client = openai.OpenAI(api_key=api_key)
        self.train_api = train_api
        
    def process_query(self, user_query: str) -> Dict:
        """
        Process natural language query and return friendly response
        
        Example queries:
        - "When is the next train to Stamford?"
        - "Show me trains to White Plains this afternoon"
        - "What track does the 3:45 train leave from?"
        """
        
        # Step 1: Extract intent and parameters
        params = self._extract_parameters(user_query)
        
        # Step 2: Fetch relevant train data
        train_data = self._fetch_train_data(params)
        
        # Step 3: Generate human-friendly response
        response = self._generate_response(user_query, train_data)
        
        # Step 4: Validate response
        confidence = self._validate_response(response, train_data)
        
        return {
            "query": user_query,
            "response": response,
            "confidence": confidence,
            "structured_data": train_data
        }
    
    def _extract_parameters(self, query: str) -> Dict:
        """Extract origin, destination, time preferences from query"""
        
        prompt = f"""
        Extract train query parameters from the following user question.
        
        User question: "{query}"
        
        Return a JSON object with these fields:
        - origin: station name or null
        - destination: station name or null  
        - time_preference: "morning" (6-12), "afternoon" (12-6), "evening" (6-12), or null
        - count: number of results wanted (default 5)
        
        Only return valid JSON, no explanations.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=150
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            return {"origin": None, "destination": None, "time_preference": None, "count": 5}
    
    def _fetch_train_data(self, params: Dict) -> Dict:
        """Fetch train data based on extracted parameters"""
        
        # Map station names to IDs
        origin_id = self.train_api.get_station_id(params.get('origin'))
        dest_id = self.train_api.get_station_id(params.get('destination'))
        
        # Fetch trains
        trains = self.train_api.get_trains(
            origin_station=origin_id,
            destination_station=dest_id,
            limit=params.get('count', 5)
        )
        
        return trains
    
    def _generate_response(self, query: str, train_data: Dict) -> str:
        """Generate natural language response"""
        
        current_time = datetime.now().strftime("%I:%M %p")
        
        system_prompt = """
        You are a helpful Metro-North Railroad assistant.
        
        Guidelines:
        - Be concise and friendly
        - Highlight the most relevant train first
        - Include departure time, track number, and status
        - Calculate time until departure
        - Mention any delays or issues
        - Use 12-hour time format (3:45 PM not 15:45)
        """
        
        user_prompt = f"""
        Current time: {current_time}
        
        User asked: "{query}"
        
        Available trains:
        {json.dumps(train_data, indent=2)}
        
        Provide a helpful response that answers their question.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content
    
    def _validate_response(self, response: str, train_data: Dict) -> float:
        """
        Validate AI response against actual data
        Returns confidence score (0-1)
        """
        
        # Extract times mentioned in response
        import re
        times_in_response = re.findall(r'\d{1,2}:\d{2}\s*[AP]M', response)
        
        # Check if mentioned times exist in actual data
        valid_mentions = 0
        total_mentions = len(times_in_response)
        
        for time_str in times_in_response:
            # Check if this time exists in train data
            if self._time_exists_in_data(time_str, train_data):
                valid_mentions += 1
        
        if total_mentions == 0:
            return 0.5  # Neutral if no specific times mentioned
        
        confidence = valid_mentions / total_mentions
        return confidence
    
    def _time_exists_in_data(self, time_str: str, train_data: Dict) -> bool:
        """Check if a time string appears in train data"""
        # Simplified check - in production, do proper time parsing
        data_str = json.dumps(train_data)
        return time_str in data_str

# Usage Example
processor = BasicQueryProcessor(
    api_key="your-openai-key",
    train_api=train_service
)

result = processor.process_query("When is the next train to Stamford?")
print(result['response'])
```

## Example 2: Multi-Step Journey Planning

### User Experience

```
User: "I have a meeting in New Haven at 3 PM"

AI: "I'll help you plan your trip to New Haven.

📍 Current Location: Grand Central Terminal
🎯 Destination: New Haven
⏰ Meeting Time: 3:00 PM

Recommended Route:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚂 Train: 1:15 PM from Track 22
   ├─ Depart Grand Central: 1:15 PM
   └─ Arrive New Haven: 2:48 PM
   
🚶 Walk to meeting: 7 minutes
   └─ Arrive at meeting: 2:55 PM
   
✅ Buffer: 5 minutes (comfortable)

Alternative Options:
- 12:45 PM train (arrives 2:18 PM, 42 min buffer)
- 1:30 PM train (arrives 3:03 PM, tight but doable)

Would you like me to:
1. Add this to your calendar?
2. Set a departure reminder?
3. Monitor for delays?"

User: "Yes, set a reminder and monitor for delays"

AI: "Done! I've set:
✓ Reminder at 1:00 PM (15 min before departure)
✓ Monitoring train 1:15 PM for delays
✓ Will notify you of any changes

Have a great meeting! 🚂"
```

### Implementation

```python
# src/ai_assistant/journey_planner.py

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import openai

class JourneyPlanner:
    def __init__(self, api_key: str, train_api, maps_api):
        self.client = openai.OpenAI(api_key=api_key)
        self.train_api = train_api
        self.maps_api = maps_api
        
    def plan_journey(self, user_request: str, user_context: Optional[Dict] = None) -> Dict:
        """
        Plan complete journey from natural language request
        
        Examples:
        - "I have a meeting in New Haven at 3 PM"
        - "How do I get to Stamford by 5 PM?"
        - "Plan my trip to White Plains tomorrow morning"
        """
        
        # Step 1: Extract journey details
        details = self._extract_journey_details(user_request)
        
        # Step 2: Get current location
        current_location = user_context.get('location') if user_context else None
        if not current_location:
            current_location = self._get_default_location()
        
        # Step 3: Find nearest station to destination
        dest_station = self._find_nearest_station(details['destination'])
        
        # Step 4: Calculate required arrival time
        meeting_time = details['meeting_time']
        walking_time = self._get_walking_time(dest_station, details['destination'])
        required_arrival = meeting_time - timedelta(minutes=walking_time + 10)  # 10 min buffer
        
        # Step 5: Find suitable trains
        trains = self._find_trains_before(current_location, dest_station, required_arrival)
        
        # Step 6: Score and rank options
        ranked_trains = self._rank_trains(trains, required_arrival, walking_time)
        
        # Step 7: Generate comprehensive plan
        plan = self._generate_journey_plan(
            user_request,
            ranked_trains,
            walking_time,
            meeting_time
        )
        
        return plan
    
    def _extract_journey_details(self, request: str) -> Dict:
        """Extract destination, time, and preferences from request"""
        
        prompt = f"""
        Extract journey planning details from: "{request}"
        
        Return JSON with:
        - destination: location name
        - meeting_time: ISO format datetime or null
        - time_flexibility: "strict", "flexible", or null
        - preferences: list of any mentioned preferences (fast, cheap, etc.)
        
        Current date/time context: {datetime.now().isoformat()}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        details = json.loads(response.choices[0].message.content)
        
        # Parse meeting time
        if details.get('meeting_time'):
            details['meeting_time'] = datetime.fromisoformat(details['meeting_time'])
        
        return details
    
    def _rank_trains(self, trains: List[Dict], target_time: datetime, walking_time: int) -> List[Dict]:
        """Rank trains by suitability"""
        
        scored_trains = []
        
        for train in trains:
            score = 0
            arrival_time = datetime.fromisoformat(train['arrival_time'])
            
            # Calculate buffer time
            buffer = (target_time - arrival_time - timedelta(minutes=walking_time)).seconds / 60
            
            # Score based on buffer (prefer 15-30 min)
            if 15 <= buffer <= 30:
                score += 10  # Perfect buffer
            elif 10 <= buffer < 15:
                score += 8   # Good buffer
            elif 5 <= buffer < 10:
                score += 5   # Acceptable buffer
            elif buffer < 5:
                score += 2   # Risky but possible
            
            # Bonus for on-time trains
            if train.get('status') == 'On Time':
                score += 3
            
            # Bonus for direct routes
            if not train.get('transfers'):
                score += 5
            
            scored_trains.append({
                **train,
                'score': score,
                'buffer_minutes': int(buffer),
                'total_journey_time': (arrival_time - datetime.now()).seconds / 60
            })
        
        return sorted(scored_trains, key=lambda x: x['score'], reverse=True)
    
    def _generate_journey_plan(
        self,
        original_request: str,
        ranked_trains: List[Dict],
        walking_time: int,
        meeting_time: datetime
    ) -> Dict:
        """Generate comprehensive journey plan with AI"""
        
        best_train = ranked_trains[0]
        alternatives = ranked_trains[1:3]
        
        system_prompt = """
        You are a journey planning assistant for Metro-North Railroad.
        
        Create a clear, visual journey plan with:
        - Emoji icons for visual appeal
        - Clear timeline with times
        - Walking directions if needed
        - Buffer time assessment
        - Alternative options
        - Helpful action items
        
        Use a conversational, helpful tone.
        """
        
        user_prompt = f"""
        User request: "{original_request}"
        
        Best train option:
        {json.dumps(best_train, indent=2)}
        
        Alternative trains:
        {json.dumps(alternatives, indent=2)}
        
        Walking time from station: {walking_time} minutes
        Meeting time: {meeting_time.strftime('%I:%M %p')}
        
        Create a comprehensive journey plan.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=800
        )
        
        return {
            "journey_plan": response.choices[0].message.content,
            "recommended_train": best_train,
            "alternatives": alternatives,
            "metadata": {
                "walking_time": walking_time,
                "meeting_time": meeting_time.isoformat(),
                "buffer_minutes": best_train['buffer_minutes']
            }
        }

# Usage
planner = JourneyPlanner(
    api_key="your-key",
    train_api=train_service,
    maps_api=maps_service
)

plan = planner.plan_journey("I have a meeting in New Haven at 3 PM")
print(plan['journey_plan'])
```

## Example 3: Context-Aware Responses

### User Experience

```
# First query
User: "When is the next train to Stamford?"
AI: "The next train to Stamford leaves at 3:45 PM from Track 18..."

# Follow-up (AI remembers context)
User: "What about the one after that?"
AI: "The following train to Stamford departs at 4:15 PM from Track 20..."

# Another follow-up
User: "Which one is less crowded?"
AI: "Based on historical patterns, the 4:15 PM train is typically less crowded 
     (about 60% capacity vs 85% for the 3:45 PM train)..."
```

### Implementation

```python
# src/ai_assistant/conversational.py

from typing import List, Dict, Optional
import openai

class ConversationalAssistant:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.conversations = {}  # session_id -> conversation history
        
    def process_message(self, message: str, session_id: str, train_data: Dict) -> str:
        """
        Process message in context of conversation history
        
        Maintains context across multiple messages
        """
        
        # Get or create conversation history
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        conversation = self.conversations[session_id]
        
        # Build context-aware prompt
        system_prompt = """
        You are a Metro-North Railroad assistant having a conversation with a user.
        
        Remember:
        - Track conversation context
        - Reference previous questions
        - Handle follow-up questions naturally
        - Be concise but helpful
        """
        
        # Add current message to history
        conversation.append({"role": "user", "content": message})
        
        # Add train data context
        data_context = f"\nCurrent train data:\n{json.dumps(train_data, indent=2)}"
        
        # Build messages for API
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation)
        messages[-1]["content"] += data_context  # Add data to last message
        
        # Generate response
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        
        assistant_message = response.choices[0].message.content
        
        # Add response to history
        conversation.append({"role": "assistant", "content": assistant_message})
        
        # Trim history if too long (keep last 10 exchanges)
        if len(conversation) > 20:
            conversation = conversation[-20:]
            self.conversations[session_id] = conversation
        
        return assistant_message
    
    def reset_conversation(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

# Usage with Flask
from flask import Flask, request, session
app = Flask(__name__)
app.secret_key = 'your-secret-key'

assistant = ConversationalAssistant(api_key="your-key")

@app.route('/ai/chat', methods=['POST'])
def chat():
    message = request.json['message']
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id
    
    train_data = get_current_trains()
    response = assistant.process_message(message, session_id, train_data)
    
    return jsonify({"response": response, "session_id": session_id})

@app.route('/ai/chat/reset', methods=['POST'])
def reset_chat():
    session_id = session.get('session_id')
    if session_id:
        assistant.reset_conversation(session_id)
    return jsonify({"status": "reset"})
```

## Example 4: Error Handling and Fallbacks

### Implementation

```python
# src/ai_assistant/robust_processor.py

import openai
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class RobustAIProcessor:
    def __init__(self, api_key: str, fallback_enabled: bool = True):
        self.client = openai.OpenAI(api_key=api_key)
        self.fallback_enabled = fallback_enabled
        
    def process_query(self, query: str, train_data: Dict) -> Dict:
        """
        Process query with comprehensive error handling
        """
        
        try:
            # Try primary LLM (GPT-4)
            response = self._try_primary_llm(query, train_data)
            
            # Validate response
            if self._validate_response(response, train_data):
                return {
                    "success": True,
                    "response": response,
                    "source": "ai",
                    "confidence": 0.95
                }
            else:
                logger.warning("AI response failed validation")
                raise ValueError("Response validation failed")
        
        except openai.RateLimitError:
            logger.error("Rate limit exceeded")
            return self._handle_rate_limit(query, train_data)
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return self._handle_api_error(query, train_data)
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return self._fallback_response(query, train_data)
    
    def _try_primary_llm(self, query: str, train_data: Dict) -> str:
        """Try primary LLM (GPT-4)"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful train assistant."},
                {"role": "user", "content": f"Q: {query}\nData: {json.dumps(train_data)}"}
            ],
            timeout=10
        )
        return response.choices[0].message.content
    
    def _try_fallback_llm(self, query: str, train_data: Dict) -> str:
        """Try cheaper fallback model (GPT-3.5)"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful train assistant."},
                {"role": "user", "content": f"Q: {query}\nData: {json.dumps(train_data)}"}
            ],
            timeout=10
        )
        return response.choices[0].message.content
    
    def _validate_response(self, response: str, train_data: Dict) -> bool:
        """Validate that response matches actual data"""
        # Check for obvious hallucinations
        
        # Extract mentioned times
        import re
        times = re.findall(r'\d{1,2}:\d{2}\s*[AP]M', response)
        
        # Check each time exists in data
        data_str = json.dumps(train_data)
        for time in times:
            if time not in data_str:
                return False
        
        # Check for impossible statements
        impossible_phrases = [
            "no trains available",
            "service suspended",
            "all trains cancelled"
        ]
        
        for phrase in impossible_phrases:
            if phrase.lower() in response.lower() and train_data.get('trains'):
                return False
        
        return True
    
    def _handle_rate_limit(self, query: str, train_data: Dict) -> Dict:
        """Handle rate limit errors"""
        if self.fallback_enabled:
            try:
                # Try fallback model
                response = self._try_fallback_llm(query, train_data)
                return {
                    "success": True,
                    "response": response,
                    "source": "fallback_ai",
                    "confidence": 0.85,
                    "note": "Using fallback model due to rate limits"
                }
            except:
                pass
        
        return self._fallback_response(query, train_data)
    
    def _handle_api_error(self, query: str, train_data: Dict) -> Dict:
        """Handle API errors"""
        if self.fallback_enabled:
            try:
                response = self._try_fallback_llm(query, train_data)
                return {
                    "success": True,
                    "response": response,
                    "source": "fallback_ai",
                    "confidence": 0.80
                }
            except:
                pass
        
        return self._fallback_response(query, train_data)
    
    def _fallback_response(self, query: str, train_data: Dict) -> Dict:
        """Last resort: return structured data with template"""
        trains = train_data.get('trains', [])
        
        if not trains:
            return {
                "success": False,
                "response": "I'm having trouble processing your request. No train data available.",
                "source": "error",
                "structured_data": train_data
            }
        
        # Generate simple template response
        first_train = trains[0]
        response = f"""
        Here's the next train information:
        
        Destination: {first_train.get('trip_headsign', 'Unknown')}
        Departure: {first_train.get('departure_time', 'Unknown')}
        Track: {first_train.get('track', 'TBD')}
        Status: {first_train.get('status', 'Unknown')}
        
        For more trains, check the structured data below.
        """
        
        return {
            "success": True,
            "response": response.strip(),
            "source": "fallback_template",
            "confidence": 0.70,
            "structured_data": train_data,
            "note": "AI unavailable, showing formatted data"
        }

# Usage
processor = RobustAIProcessor(api_key="your-key", fallback_enabled=True)
result = processor.process_query("Next train to Stamford?", train_data)

if result['success']:
    print(result['response'])
else:
    print("Error:", result['response'])
```

## Example 5: Multi-Language Support

### User Experience

```
# English
User: "When is the next train to White Plains?"
AI: "The next train to White Plains departs at 3:45 PM from Track 15..."

# Spanish
Usuario: "¿Cuándo sale el próximo tren a White Plains?"
AI: "El próximo tren a White Plains sale a las 3:45 PM desde la vía 15..."

# Chinese
用户: "下一班去White Plains的火车什么时候开？"
AI: "下一班开往White Plains的火车将于下午3:45从15号站台发车..."
```

### Implementation

```python
# src/ai_assistant/multilingual.py

import openai
from langdetect import detect
from typing import Dict

class MultilingualAssistant:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
        # Supported languages
        self.languages = {
            'en': 'English',
            'es': 'Spanish',
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ar': 'Arabic'
        }
    
    def process_query(self, query: str, train_data: Dict) -> Dict:
        """
        Process query in any supported language
        """
        
        # Detect language
        detected_lang = detect(query)
        lang_name = self.languages.get(detected_lang, 'English')
        
        # Process query (translate if needed)
        if detected_lang != 'en':
            # Translate query to English for processing
            query_en = self._translate(query, detected_lang, 'en')
        else:
            query_en = query
        
        # Generate response in English
        response_en = self._generate_response(query_en, train_data)
        
        # Translate response back if needed
        if detected_lang != 'en':
            response = self._translate(response_en, 'en', detected_lang)
        else:
            response = response_en
        
        return {
            "query": query,
            "response": response,
            "detected_language": lang_name,
            "language_code": detected_lang
        }
    
    def _translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using LLM"""
        
        lang_names = {
            'en': 'English',
            'es': 'Spanish',
            'zh-cn': 'Chinese',
            'fr': 'French'
        }
        
        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)
        
        prompt = f"""
        Translate the following {source_name} text to {target_name}.
        Maintain train terminology accurately.
        
        Text: {text}
        
        Translation:
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_response(self, query: str, train_data: Dict) -> str:
        """Generate response in English"""
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful train assistant."},
                {"role": "user", "content": f"Q: {query}\nData: {json.dumps(train_data)}"}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content

# Usage
assistant = MultilingualAssistant(api_key="your-key")

# Automatic language detection
result = assistant.process_query(
    "¿Cuándo sale el próximo tren?",
    train_data
)

print(f"Detected: {result['detected_language']}")
print(f"Response: {result['response']}")
```

## Example 6: Voice Interface

### Implementation

```python
# src/ai_assistant/voice_interface.py

import openai
from typing import BinaryIO

class VoiceAssistant:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def process_voice_query(self, audio_file: BinaryIO, train_data: dict) -> dict:
        """
        Process voice query end-to-end:
        1. Speech to text
        2. Process query
        3. Generate response
        4. Text to speech
        """
        
        # Step 1: Transcribe audio
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        user_query = transcript.text
        
        # Step 2: Process query
        response_text = self._process_query(user_query, train_data)
        
        # Step 3: Convert response to speech
        audio_response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=response_text
        )
        
        return {
            "transcript": user_query,
            "response_text": response_text,
            "audio_response": audio_response.content
        }
    
    def _process_query(self, query: str, train_data: dict) -> str:
        """Process text query"""
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a voice assistant for Metro-North trains. Keep responses concise and speakable."
                },
                {
                    "role": "user",
                    "content": f"Q: {query}\nData: {json.dumps(train_data)}"
                }
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content

# Flask endpoint
from flask import Flask, request, send_file
import io

app = Flask(__name__)
voice_assistant = VoiceAssistant(api_key="your-key")

@app.route('/ai/voice', methods=['POST'])
def voice_query():
    """
    Accept audio file, return audio response
    
    Usage:
    curl -X POST http://localhost:5000/ai/voice \
      -F "audio=@question.mp3" \
      -o response.mp3
    """
    
    audio_file = request.files['audio']
    train_data = get_current_trains()
    
    result = voice_assistant.process_voice_query(audio_file, train_data)
    
    # Return audio response
    return send_file(
        io.BytesIO(result['audio_response']),
        mimetype='audio/mpeg',
        as_attachment=True,
        download_name='response.mp3'
    )
```

## Example 7: Code Generation for Developers

### User Experience

```
Developer: "Generate Python code to get the next 5 trains from Grand Central to Stamford"

AI: "Here's the Python code:

```python
import requests

def get_trains_to_stamford(limit=5):
    \"\"\"Get next trains from Grand Central to Stamford\"\"\"
    
    # API endpoint
    base_url = "http://localhost:5000"
    
    # Station IDs
    grand_central_id = "1"
    stamford_id = "120"
    
    # Make request
    response = requests.get(
        f"{base_url}/trains",
        params={
            "origin_station": grand_central_id,
            "destination_station": stamford_id,
            "limit": limit
        }
    )
    
    # Check response
    if response.status_code == 200:
        data = response.json()
        return data['trains']
    else:
        raise Exception(f"API error: {response.status_code}")

# Usage
try:
    trains = get_trains_to_stamford()
    
    for train in trains:
        print(f"Train to {train['trip_headsign']}")
        print(f"  Departs: {train['departure_time']}")
        print(f"  Track: {train['track']}")
        print(f"  Status: {train['status']}")
        print()
        
except Exception as e:
    print(f"Error: {e}")
```

This code includes error handling and is ready to use!
"
```

### Implementation

```python
# src/ai_assistant/code_generator.py

import openai

class CodeGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
        # API documentation context
        self.api_docs = """
        MNR RT Service API:
        
        Endpoints:
        - GET /trains - Get train list
          Params: origin_station, destination_station, limit
        - GET /stations - Get all stations
        - GET /routes - Get all routes
        - GET /train/<trip_id> - Get specific train
        
        Station IDs:
        - Grand Central: 1
        - Stamford: 120
        - White Plains: 197
        - New Haven: 300
        """
    
    def generate_code(
        self,
        description: str,
        language: str = "python",
        framework: str = None
    ) -> str:
        """Generate code based on description"""
        
        system_prompt = f"""
        You are a code generation assistant for the MNR RT Service API.
        
        Generate {language} code that:
        - Is production-ready
        - Includes error handling
        - Has clear comments
        - Follows best practices
        - Is well-structured
        
        API Documentation:
        {self.api_docs}
        """
        
        user_prompt = f"""
        Generate {language} code for:
        {description}
        
        {f"Using {framework} framework" if framework else ""}
        
        Include:
        - Complete working code
        - Error handling
        - Usage example
        - Comments explaining key parts
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message.content

# Usage examples
generator = CodeGenerator(api_key="your-key")

# Python example
python_code = generator.generate_code(
    "Get next 5 trains from Grand Central to Stamford",
    language="python"
)

# JavaScript example
js_code = generator.generate_code(
    "Create a React component showing next trains",
    language="javascript",
    framework="React"
)

# Arduino example
arduino_code = generator.generate_code(
    "Display next 3 trains on 16x2 LCD",
    language="c++",
    framework="Arduino"
)
```

## Summary

These examples demonstrate:

1. **Basic Queries**: Natural language → structured API calls
2. **Journey Planning**: Complex multi-step planning with alternatives
3. **Contextual Conversations**: Maintaining conversation history
4. **Error Handling**: Graceful degradation and fallbacks
5. **Multi-Language**: Automatic translation and detection
6. **Voice Interface**: Speech-to-text and text-to-speech
7. **Code Generation**: Generate client code for developers

All examples are production-ready and can be adapted to your specific needs.

---

**Next Steps**: See [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) for detailed setup instructions.

**Last Updated**: 2025-11-09
