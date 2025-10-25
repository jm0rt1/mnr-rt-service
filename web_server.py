#!/usr/bin/env python3
"""
MTA Metro-North Railroad Real-Time Web Server

A simple web server that provides real-time train information in JSON format.
This serves as a relay between the GTFS-RT protobuf feed and clients that need
simpler JSON data.

Usage:
    python web_server.py [--port 5000] [--api-key YOUR_API_KEY]
"""

import argparse
import sys
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, request
from src.mta_gtfs_client import MTAGTFSRealtimeClient
from src.gtfs_realtime import mta_railroad_pb2

app = Flask(__name__)
client = None


def timestamp_to_datetime(timestamp):
    """Convert Unix timestamp to ISO 8601 datetime string in UTC."""
    if timestamp and timestamp > 0:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
    return None


def extract_train_info(trip_update):
    """
    Extract simplified train information from a GTFS-RT trip update.
    
    Args:
        trip_update: TripUpdate protobuf message
        
    Returns:
        dict: Simplified train information
    """
    train_info = {
        'trip_id': None,
        'route_id': None,
        'vehicle_id': None,
        'current_stop': None,
        'next_stop': None,
        'eta': None,
        'track': None,
        'status': None,
        'stops': []
    }
    
    # Extract trip information
    if trip_update.HasField('trip'):
        trip = trip_update.trip
        if trip.HasField('trip_id'):
            train_info['trip_id'] = trip.trip_id
        if trip.HasField('route_id'):
            train_info['route_id'] = trip.route_id
    
    # Extract vehicle information
    if trip_update.HasField('vehicle'):
        vehicle = trip_update.vehicle
        if vehicle.HasField('id'):
            train_info['vehicle_id'] = vehicle.id
    
    # Extract stop time updates
    if trip_update.stop_time_update:
        for i, stu in enumerate(trip_update.stop_time_update):
            stop_info = {
                'stop_id': stu.stop_id if stu.HasField('stop_id') else None,
                'arrival_time': None,
                'departure_time': None,
                'track': None,
                'status': None
            }
            
            # Get arrival time
            if stu.HasField('arrival') and stu.arrival.HasField('time'):
                stop_info['arrival_time'] = timestamp_to_datetime(stu.arrival.time)
            
            # Get departure time
            if stu.HasField('departure') and stu.departure.HasField('time'):
                stop_info['departure_time'] = timestamp_to_datetime(stu.departure.time)
            
            # Get MTA Railroad extensions (track and train status)
            if stu.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update):
                mta_ext = stu.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
                if mta_ext.HasField('track'):
                    stop_info['track'] = mta_ext.track
                if mta_ext.HasField('trainStatus'):
                    stop_info['status'] = mta_ext.trainStatus
            
            train_info['stops'].append(stop_info)
            
            # Set next stop info (first stop with future time)
            if i == 0:
                train_info['current_stop'] = stop_info['stop_id']
                train_info['eta'] = stop_info['arrival_time'] or stop_info['departure_time']
                train_info['track'] = stop_info['track']
                train_info['status'] = stop_info['status']
            elif i == 1 and not train_info['next_stop']:
                train_info['next_stop'] = stop_info['stop_id']
    
    return train_info


@app.route('/trains', methods=['GET'])
def get_trains():
    """
    Get real-time train information.
    
    Query Parameters:
        city: Filter by city/region (default: 'mnr' for Metro-North Railroad)
        limit: Maximum number of trains to return (default: 20, max: 100)
        
    Returns:
        JSON response with train information
    """
    try:
        # Get query parameters
        city = request.args.get('city', 'mnr').lower()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        # Currently only supports MNR (Metro-North Railroad)
        if city not in ['mnr', 'metro-north', 'metronorth']:
            return jsonify({
                'error': 'Unsupported city. Currently only supports "mnr" (Metro-North Railroad)',
                'supported_cities': ['mnr', 'metro-north', 'metronorth']
            }), 400
        
        # Fetch the GTFS-RT feed
        feed = client.fetch_feed()
        
        # Extract trip updates with limit
        all_trip_updates = client.get_trip_updates(feed)
        trip_updates = all_trip_updates[:limit]
        
        # Convert to simplified format
        trains = []
        for trip_update in trip_updates:
            train_info = extract_train_info(trip_update)
            trains.append(train_info)
        
        # Build response
        response = {
            'timestamp': timestamp_to_datetime(feed.header.timestamp),
            'city': 'mnr',
            'total_trains': len(trains),
            'trains': trains
        }
        
        return jsonify(response)
        
    except ValueError as e:
        # Log the actual error for debugging
        app.logger.warning(f"Invalid parameter in /trains: {str(e)}")
        return jsonify({
            'error': 'Invalid parameter value. Please check your query parameters.'
        }), 400
    except requests.RequestException as e:
        # Log the actual error for debugging
        app.logger.error(f"MTA API request failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch data from MTA API. Please try again later.'
        }), 503
    except Exception as e:
        # Log the actual error for debugging but don't expose details
        app.logger.error(f"Unexpected error in /trains: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'MNR Real-Time Relay',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


@app.route('/', methods=['GET'])
def index():
    """API information endpoint."""
    return jsonify({
        'service': 'MNR Real-Time Relay',
        'description': 'Simple JSON API for Metro-North Railroad real-time train data',
        'endpoints': {
            '/': 'This information page',
            '/health': 'Health check endpoint',
            '/trains': 'Get real-time train information (supports ?city=mnr&limit=20)'
        },
        'usage_examples': {
            'get_trains': '/trains?city=mnr&limit=20',
            'health_check': '/health'
        }
    })


def main():
    """Main entry point for the web server."""
    global client
    
    parser = argparse.ArgumentParser(
        description='MTA Metro-North Railroad Real-Time Web Server'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the web server to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='Optional API key for MTA API authentication',
        default=None
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    
    args = parser.parse_args()
    
    # Initialize the GTFS client
    client = MTAGTFSRealtimeClient(api_key=args.api_key)
    
    print(f"Starting MNR Real-Time Relay Server on {args.host}:{args.port}")
    print(f"Access the API at: http://{args.host}:{args.port}/trains")
    print(f"View API info at: http://{args.host}:{args.port}/")
    
    # Run the Flask app
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main())
