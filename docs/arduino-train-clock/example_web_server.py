"""
Example Web Server Implementation for Arduino Train Clock

This module demonstrates how to create a web service that transforms
GTFS-RT data into the JSON format expected by the Arduino train clock.

This is an EXAMPLE implementation showing how to integrate with the
existing MTA GTFS client to serve data to Arduino devices.

Requirements:
    - Flask web framework
    - Existing mta_gtfs_client module

Usage:
    python example_web_server.py
    
Then configure Arduino to use:
    http://YOUR_IP:5000/api/trains
"""

from flask import Flask, jsonify, request
from datetime import datetime
import sys
import os

# Add parent directory to path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from src.mta_gtfs_client import MTAGTFSRealtimeClient
    from src.gtfs_realtime import mta_railroad_pb2
    GTFS_AVAILABLE = True
except ImportError:
    GTFS_AVAILABLE = False
    print("Warning: GTFS client not available. Using mock data.")

app = Flask(__name__)

# Initialize MTA client if available
if GTFS_AVAILABLE:
    mta_client = MTAGTFSRealtimeClient()


def parse_gtfs_to_json(trip_updates, max_trains=10):
    """
    Transform GTFS-RT trip updates to Arduino-friendly JSON format
    
    Args:
        trip_updates: List of TripUpdate protobuf messages
        max_trains: Maximum number of trains to return
    
    Returns:
        dict: JSON-serializable dictionary with train data
    """
    trains = []
    
    for trip_update in trip_updates[:max_trains]:
        # Extract trip information
        trip_id = trip_update.trip.trip_id if trip_update.HasField('trip') else "Unknown"
        route_id = trip_update.trip.route_id if trip_update.HasField('trip') else "Unknown"
        
        # Get the next stop information
        if len(trip_update.stop_time_update) > 0:
            next_stop = trip_update.stop_time_update[0]
            
            # Extract arrival time
            arrival_time = "N/A"
            delay_seconds = 0
            
            if next_stop.HasField('arrival'):
                if next_stop.arrival.HasField('time'):
                    timestamp = next_stop.arrival.time
                    arrival_dt = datetime.fromtimestamp(timestamp)
                    arrival_time = arrival_dt.strftime("%H:%M:%S")
                
                if next_stop.arrival.HasField('delay'):
                    delay_seconds = next_stop.arrival.delay
            
            # Extract track and status from MTA Railroad extension
            track = "TBD"
            train_status = "Unknown"
            
            if next_stop.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update):
                mta_ext = next_stop.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
                
                if mta_ext.HasField('track'):
                    track = mta_ext.track
                
                if mta_ext.HasField('trainStatus'):
                    train_status = mta_ext.trainStatus
            
            # Determine status based on delay
            if delay_seconds > 300:
                status = "Delayed"
            elif delay_seconds > 0:
                status = "Running Late"
            else:
                status = train_status if train_status != "Unknown" else "On Time"
            
            # Map route ID to readable name
            route_name = route_id
            if "Hudson" in route_id:
                route_name = "Hudson Line"
            elif "Harlem" in route_id:
                route_name = "Harlem Line"
            elif "NewHaven" in route_id or "NH" in route_id:
                route_name = "New Haven Line"
            
            # Create train entry
            train = {
                "trip_id": trip_id,
                "route": route_name,
                "destination": "Grand Central Terminal",  # Could extract from GTFS
                "track": track,
                "arrival_time": arrival_time,
                "status": status,
                "delay_seconds": delay_seconds
            }
            
            trains.append(train)
    
    return {"trains": trains}


@app.route('/api/trains')
def get_trains():
    """
    Get upcoming trains in Arduino-compatible JSON format
    
    Query parameters:
        - limit: Maximum number of trains (default: 10)
    
    Returns:
        JSON response with train data
    """
    limit = request.args.get('limit', default=10, type=int)
    
    if not GTFS_AVAILABLE:
        # Return mock data if GTFS client not available
        return jsonify({
            "trains": [
                {
                    "trip_id": "MOCK001",
                    "route": "Hudson Line",
                    "destination": "Grand Central Terminal",
                    "track": "5",
                    "arrival_time": datetime.now().strftime("%H:%M:%S"),
                    "status": "On Time",
                    "delay_seconds": 0
                }
            ],
            "note": "Mock data - GTFS client not configured"
        })
    
    try:
        # Fetch real-time data from MTA
        feed = mta_client.fetch_feed()
        trip_updates = mta_client.get_trip_updates(feed)
        
        # Transform to JSON format
        result = parse_gtfs_to_json(trip_updates, max_trains=limit)
        
        # Add metadata
        result['updated_at'] = datetime.now().isoformat()
        result['source'] = 'MTA GTFS-RT'
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "trains": []
        }), 500


@app.route('/api/status')
def status():
    """Server status endpoint"""
    return jsonify({
        "status": "running",
        "gtfs_available": GTFS_AVAILABLE,
        "endpoints": {
            "/api/trains": "Get upcoming trains (JSON)",
            "/api/trains?limit=5": "Get specific number of trains",
            "/api/status": "Server status"
        }
    })


@app.route('/')
def index():
    """Welcome page"""
    gtfs_status = "Connected" if GTFS_AVAILABLE else "Not Available (using mock data)"
    
    return f"""
    <html>
    <head><title>MNR Train Clock API</title></head>
    <body>
        <h1>Metro-North Railroad Train Clock API</h1>
        <p>This server provides train data for Arduino devices.</p>
        
        <h2>Status</h2>
        <ul>
            <li>GTFS-RT Client: {gtfs_status}</li>
            <li>Server: Running</li>
        </ul>
        
        <h2>Endpoints</h2>
        <ul>
            <li><a href="/api/trains">/api/trains</a> - Get upcoming trains</li>
            <li><a href="/api/trains?limit=5">/api/trains?limit=5</a> - Limit results</li>
            <li><a href="/api/status">/api/status</a> - Server status</li>
        </ul>
        
        <h2>Arduino Configuration</h2>
        <pre>
#define API_ENDPOINT "http://YOUR_IP:5000/api/trains"
        </pre>
    </body>
    </html>
    """


if __name__ == '__main__':
    print("=" * 60)
    print("Metro-North Railroad Train Clock API Server")
    print("=" * 60)
    
    if GTFS_AVAILABLE:
        print("\n✓ GTFS-RT client available")
        print("  Will fetch real-time data from MTA")
    else:
        print("\n✗ GTFS-RT client not available")
        print("  Will serve mock data for testing")
    
    print("\nStarting server on http://0.0.0.0:5000")
    print("\nEndpoints:")
    print("  - http://localhost:5000/api/trains")
    print("  - http://localhost:5000/api/status")
    print("\nPress Ctrl+C to stop")
    print("=" * 60 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
