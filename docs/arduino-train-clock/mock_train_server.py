#!/usr/bin/env python3
"""
Mock Train Data Server for Arduino Train Clock Testing

This Flask server provides mock Metro-North Railroad train data
for testing the Arduino train clock example.

Usage:
    python mock_train_server.py

Then configure your Arduino to point to:
    http://<your-ip>:5000/api/trains

Requirements:
    pip install flask
"""

from flask import Flask, jsonify
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Mock train routes
ROUTES = ["Hudson Line", "Harlem Line", "New Haven Line"]
DESTINATIONS = [
    "Grand Central Terminal",
    "White Plains",
    "Poughkeepsie",
    "New Haven",
    "Stamford"
]
STATUSES = ["On Time", "Delayed", "Boarding", "Departed"]


def generate_mock_trains(count=5):
    """Generate mock train data"""
    trains = []
    now = datetime.now()
    
    for i in range(count):
        # Generate random delay
        is_delayed = random.random() < 0.3  # 30% chance of delay
        delay_seconds = random.randint(60, 600) if is_delayed else 0
        
        # Generate arrival time
        minutes_from_now = 5 + (i * 7)
        arrival_time = now + timedelta(minutes=minutes_from_now, seconds=delay_seconds)
        
        # Determine status
        if delay_seconds > 300:
            status = "Delayed"
        elif delay_seconds > 0:
            status = "Delayed"
        else:
            status = random.choice(["On Time", "Boarding"])
        
        # Generate track number
        track = str(random.randint(1, 12)) if random.random() < 0.9 else "TBD"
        
        train = {
            "trip_id": f"MNR{1000000 + i}",
            "route": random.choice(ROUTES),
            "destination": random.choice(DESTINATIONS),
            "track": track,
            "arrival_time": arrival_time.strftime("%H:%M:%S"),
            "status": status,
            "delay_seconds": delay_seconds
        }
        trains.append(train)
    
    return trains


@app.route('/api/trains')
def get_trains():
    """Return mock train data as JSON"""
    trains = generate_mock_trains(count=5)
    return jsonify({"trains": trains})


@app.route('/api/trains/<int:count>')
def get_trains_count(count):
    """Return specified number of mock trains"""
    if count < 1 or count > 20:
        return jsonify({"error": "Count must be between 1 and 20"}), 400
    
    trains = generate_mock_trains(count=count)
    return jsonify({"trains": trains})


@app.route('/api/status')
def status():
    """Server status endpoint"""
    return jsonify({
        "status": "running",
        "server": "Mock MNR Train Data Server",
        "version": "1.0",
        "endpoints": {
            "/api/trains": "Get 5 upcoming trains",
            "/api/trains/<count>": "Get specified number of trains",
            "/api/status": "Server status"
        }
    })


@app.route('/')
def index():
    """Welcome page"""
    return """
    <html>
    <head><title>Mock MNR Train Server</title></head>
    <body>
        <h1>Mock Metro-North Railroad Train Data Server</h1>
        <p>This server provides mock train data for testing the Arduino train clock.</p>
        
        <h2>Available Endpoints:</h2>
        <ul>
            <li><a href="/api/trains">/api/trains</a> - Get 5 upcoming trains (JSON)</li>
            <li><a href="/api/trains/10">/api/trains/10</a> - Get 10 upcoming trains (JSON)</li>
            <li><a href="/api/status">/api/status</a> - Server status (JSON)</li>
        </ul>
        
        <h2>Arduino Configuration:</h2>
        <p>Update your Arduino config.h with:</p>
        <pre>
#define API_ENDPOINT "http://YOUR_IP_HERE:5000/api/trains"
        </pre>
        
        <h2>Sample Response:</h2>
        <pre>
{
  "trains": [
    {
      "trip_id": "MNR1000000",
      "route": "Hudson Line",
      "destination": "Grand Central Terminal",
      "track": "5",
      "arrival_time": "14:30:00",
      "status": "On Time",
      "delay_seconds": 0
    }
  ]
}
        </pre>
    </body>
    </html>
    """


if __name__ == '__main__':
    print("=" * 60)
    print("Mock Metro-North Railroad Train Data Server")
    print("=" * 60)
    print("\nStarting server on http://0.0.0.0:5000")
    print("\nEndpoints:")
    print("  - http://localhost:5000/api/trains")
    print("  - http://localhost:5000/api/status")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
