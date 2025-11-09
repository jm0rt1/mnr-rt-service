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
import logging
import requests
from flask import Flask, jsonify, request
from pathlib import Path
import yaml
from src.mta_gtfs_client import MTAGTFSRealtimeClient
from src.gtfs_realtime import mta_railroad_pb2
from src.shared.settings import GlobalSettings
from src.gtfs_downloader import GTFSDownloader
from src.gtfs_static_reader import GTFSStaticReader
from src.travel_assist import TravelAssistant

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
client = None
gtfs_reader = None
travel_assistant = None
FEATURE_FLAGS = GlobalSettings.FeatureFlags.as_dict()


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
        'timestamp': None,  # NEW: When vehicle's real-time progress was measured
        'delay': None,  # NEW: Overall trip delay in seconds
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
    
    # NEW: Extract trip-level timestamp (when position was last measured)
    if trip_update.HasField('timestamp'):
        train_info['timestamp'] = timestamp_to_datetime(trip_update.timestamp)
    
    # NEW: Extract trip-level delay (overall schedule deviation)
    if trip_update.HasField('delay'):
        train_info['delay'] = trip_update.delay

    # Extract stop time updates
    if trip_update.stop_time_update:
        for i, stu in enumerate(trip_update.stop_time_update):
            stop_info = {
                'stop_id': stu.stop_id if stu.HasField('stop_id') else None,
                'stop_sequence': None,  # NEW: Stop sequence number
                'arrival_time': None,
                'arrival_delay': None,  # NEW: Arrival delay in seconds
                'arrival_uncertainty': None,  # NEW: Arrival prediction uncertainty
                'departure_time': None,
                'departure_delay': None,  # NEW: Departure delay in seconds
                'departure_uncertainty': None,  # NEW: Departure prediction uncertainty
                'track': None,
                'status': None,
                'schedule_relationship': None  # NEW: SCHEDULED, SKIPPED, NO_DATA, UNSCHEDULED
            }

            # NEW: Get stop sequence
            if stu.HasField('stop_sequence'):
                stop_info['stop_sequence'] = stu.stop_sequence

            # Get arrival time and NEW: delay and uncertainty
            if stu.HasField('arrival'):
                if stu.arrival.HasField('time'):
                    stop_info['arrival_time'] = timestamp_to_datetime(
                        stu.arrival.time)
                if stu.arrival.HasField('delay'):
                    stop_info['arrival_delay'] = stu.arrival.delay
                if stu.arrival.HasField('uncertainty'):
                    stop_info['arrival_uncertainty'] = stu.arrival.uncertainty

            # Get departure time and NEW: delay and uncertainty
            if stu.HasField('departure'):
                if stu.departure.HasField('time'):
                    stop_info['departure_time'] = timestamp_to_datetime(
                        stu.departure.time)
                if stu.departure.HasField('delay'):
                    stop_info['departure_delay'] = stu.departure.delay
                if stu.departure.HasField('uncertainty'):
                    stop_info['departure_uncertainty'] = stu.departure.uncertainty

            # NEW: Get schedule relationship
            if stu.HasField('schedule_relationship'):
                relationship = stu.schedule_relationship
                # Convert enum to string
                if relationship == 0:
                    stop_info['schedule_relationship'] = 'SCHEDULED'
                elif relationship == 1:
                    stop_info['schedule_relationship'] = 'SKIPPED'
                elif relationship == 2:
                    stop_info['schedule_relationship'] = 'NO_DATA'
                elif relationship == 3:
                    stop_info['schedule_relationship'] = 'UNSCHEDULED'

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


def extract_vehicle_position_info(vehicle_position):
    """
    Extract vehicle position information from a GTFS-RT vehicle position update.
    
    Args:
        vehicle_position: VehiclePosition protobuf message
        
    Returns:
        dict: Vehicle position information
    """
    position_info = {
        'trip_id': None,
        'route_id': None,
        'vehicle_id': None,
        'latitude': None,
        'longitude': None,
        'bearing': None,
        'speed': None,
        'current_stop_sequence': None,
        'stop_id': None,
        'current_status': None,
        'timestamp': None,
        'congestion_level': None,
        'occupancy_status': None,
        'occupancy_percentage': None,
        'carriages': []
    }
    
    # Extract trip information
    if vehicle_position.HasField('trip'):
        trip = vehicle_position.trip
        if trip.HasField('trip_id'):
            position_info['trip_id'] = trip.trip_id
        if trip.HasField('route_id'):
            position_info['route_id'] = trip.route_id
    
    # Extract vehicle information
    if vehicle_position.HasField('vehicle'):
        vehicle = vehicle_position.vehicle
        if vehicle.HasField('id'):
            position_info['vehicle_id'] = vehicle.id
    
    # Extract position information
    if vehicle_position.HasField('position'):
        pos = vehicle_position.position
        if pos.HasField('latitude'):
            position_info['latitude'] = pos.latitude
        if pos.HasField('longitude'):
            position_info['longitude'] = pos.longitude
        if pos.HasField('bearing'):
            position_info['bearing'] = pos.bearing
        if pos.HasField('speed'):
            position_info['speed'] = pos.speed
    
    # Extract current stop information
    if vehicle_position.HasField('current_stop_sequence'):
        position_info['current_stop_sequence'] = vehicle_position.current_stop_sequence
    if vehicle_position.HasField('stop_id'):
        position_info['stop_id'] = vehicle_position.stop_id
    
    # Extract current status
    if vehicle_position.HasField('current_status'):
        status = vehicle_position.current_status
        if status == 0:
            position_info['current_status'] = 'INCOMING_AT'
        elif status == 1:
            position_info['current_status'] = 'STOPPED_AT'
        elif status == 2:
            position_info['current_status'] = 'IN_TRANSIT_TO'
    
    # Extract timestamp
    if vehicle_position.HasField('timestamp'):
        position_info['timestamp'] = timestamp_to_datetime(vehicle_position.timestamp)
    
    # Extract congestion level
    if vehicle_position.HasField('congestion_level'):
        congestion = vehicle_position.congestion_level
        if congestion == 0:
            position_info['congestion_level'] = 'UNKNOWN_CONGESTION_LEVEL'
        elif congestion == 1:
            position_info['congestion_level'] = 'RUNNING_SMOOTHLY'
        elif congestion == 2:
            position_info['congestion_level'] = 'STOP_AND_GO'
        elif congestion == 3:
            position_info['congestion_level'] = 'CONGESTION'
        elif congestion == 4:
            position_info['congestion_level'] = 'SEVERE_CONGESTION'
    
    # Extract occupancy status
    if vehicle_position.HasField('occupancy_status'):
        occupancy = vehicle_position.occupancy_status
        occupancy_map = {
            0: 'EMPTY',
            1: 'MANY_SEATS_AVAILABLE',
            2: 'FEW_SEATS_AVAILABLE',
            3: 'STANDING_ROOM_ONLY',
            4: 'CRUSHED_STANDING_ROOM_ONLY',
            5: 'FULL',
            6: 'NOT_ACCEPTING_PASSENGERS',
            7: 'NO_DATA_AVAILABLE',
            8: 'NOT_BOARDABLE'
        }
        position_info['occupancy_status'] = occupancy_map.get(occupancy, 'NO_DATA_AVAILABLE')
    
    # Extract occupancy percentage
    if vehicle_position.HasField('occupancy_percentage'):
        position_info['occupancy_percentage'] = vehicle_position.occupancy_percentage
    
    # Extract carriage details
    for carriage in vehicle_position.multi_carriage_details:
        carriage_info = {
            'id': None,
            'label': None,
            'sequence': None,
            'occupancy_status': None,
            'occupancy_percentage': None,
            'bicycles_allowed': None,
            'carriage_class': None,
            'quiet_carriage': None,
            'toilet_facilities': None
        }
        
        if carriage.HasField('id'):
            carriage_info['id'] = carriage.id
        if carriage.HasField('label'):
            carriage_info['label'] = carriage.label
        if carriage.HasField('carriage_sequence'):
            carriage_info['sequence'] = carriage.carriage_sequence
        
        # Carriage occupancy status
        if carriage.HasField('occupancy_status'):
            occupancy = carriage.occupancy_status
            occupancy_map = {
                0: 'EMPTY',
                1: 'MANY_SEATS_AVAILABLE',
                2: 'FEW_SEATS_AVAILABLE',
                3: 'STANDING_ROOM_ONLY',
                4: 'CRUSHED_STANDING_ROOM_ONLY',
                5: 'FULL',
                6: 'NOT_ACCEPTING_PASSENGERS',
                7: 'NO_DATA_AVAILABLE',
                8: 'NOT_BOARDABLE'
            }
            carriage_info['occupancy_status'] = occupancy_map.get(occupancy, 'NO_DATA_AVAILABLE')
        
        # Carriage occupancy percentage
        if carriage.HasField('occupancy_percentage'):
            occ_pct = carriage.occupancy_percentage
            if occ_pct >= 0:  # -1 means no data
                carriage_info['occupancy_percentage'] = occ_pct
        
        # MTA Railroad carriage extensions
        if carriage.HasExtension(mta_railroad_pb2.mta_railroad_carriage_details):
            mta_ext = carriage.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
            
            if mta_ext.HasField('bicycles_allowed'):
                bikes = mta_ext.bicycles_allowed
                if bikes == -1:
                    carriage_info['bicycles_allowed'] = 'unlimited'
                elif bikes == 0:
                    carriage_info['bicycles_allowed'] = 'prohibited'
                else:
                    carriage_info['bicycles_allowed'] = bikes
            
            if mta_ext.HasField('carriage_class'):
                carriage_info['carriage_class'] = mta_ext.carriage_class
            
            if mta_ext.HasField('quiet_carriage'):
                quiet = mta_ext.quiet_carriage
                if quiet == 1:
                    carriage_info['quiet_carriage'] = True
                elif quiet == 2:
                    carriage_info['quiet_carriage'] = False
            
            if mta_ext.HasField('toilet_facilities'):
                toilet = mta_ext.toilet_facilities
                if toilet == 1:
                    carriage_info['toilet_facilities'] = True
                elif toilet == 2:
                    carriage_info['toilet_facilities'] = False
        
        position_info['carriages'].append(carriage_info)
    
    return position_info


def extract_alert_info(alert):
    """
    Extract service alert information from a GTFS-RT alert.
    
    Args:
        alert: Alert protobuf message
        
    Returns:
        dict: Alert information
    """
    alert_info = {
        'active_periods': [],
        'informed_entities': [],
        'cause': None,
        'effect': None,
        'header_text': None,
        'description_text': None,
        'url': None,
        'severity_level': None
    }
    
    # Extract active periods
    for period in alert.active_period:
        period_info = {}
        if period.HasField('start'):
            period_info['start'] = timestamp_to_datetime(period.start)
        if period.HasField('end'):
            period_info['end'] = timestamp_to_datetime(period.end)
        alert_info['active_periods'].append(period_info)
    
    # Extract informed entities
    for entity in alert.informed_entity:
        entity_info = {}
        if entity.HasField('agency_id'):
            entity_info['agency_id'] = entity.agency_id
        if entity.HasField('route_id'):
            entity_info['route_id'] = entity.route_id
        if entity.HasField('route_type'):
            entity_info['route_type'] = entity.route_type
        if entity.HasField('trip'):
            trip_desc = {}
            if entity.trip.HasField('trip_id'):
                trip_desc['trip_id'] = entity.trip.trip_id
            if entity.trip.HasField('route_id'):
                trip_desc['route_id'] = entity.trip.route_id
            entity_info['trip'] = trip_desc
        if entity.HasField('stop_id'):
            entity_info['stop_id'] = entity.stop_id
        alert_info['informed_entities'].append(entity_info)
    
    # Extract cause
    if alert.HasField('cause'):
        cause_map = {
            1: 'UNKNOWN_CAUSE',
            2: 'OTHER_CAUSE',
            3: 'TECHNICAL_PROBLEM',
            4: 'STRIKE',
            5: 'DEMONSTRATION',
            6: 'ACCIDENT',
            7: 'HOLIDAY',
            8: 'WEATHER',
            9: 'MAINTENANCE',
            10: 'CONSTRUCTION',
            11: 'POLICE_ACTIVITY',
            12: 'MEDICAL_EMERGENCY'
        }
        alert_info['cause'] = cause_map.get(alert.cause, 'UNKNOWN_CAUSE')
    
    # Extract effect
    if alert.HasField('effect'):
        effect_map = {
            1: 'NO_SERVICE',
            2: 'REDUCED_SERVICE',
            3: 'SIGNIFICANT_DELAYS',
            4: 'DETOUR',
            5: 'ADDITIONAL_SERVICE',
            6: 'MODIFIED_SERVICE',
            7: 'OTHER_EFFECT',
            8: 'UNKNOWN_EFFECT',
            9: 'STOP_MOVED',
            10: 'NO_EFFECT',
            11: 'ACCESSIBILITY_ISSUE'
        }
        alert_info['effect'] = effect_map.get(alert.effect, 'UNKNOWN_EFFECT')
    
    # Extract header text
    if alert.HasField('header_text') and len(alert.header_text.translation) > 0:
        alert_info['header_text'] = alert.header_text.translation[0].text
    
    # Extract description text
    if alert.HasField('description_text') and len(alert.description_text.translation) > 0:
        alert_info['description_text'] = alert.description_text.translation[0].text
    
    # Extract URL
    if alert.HasField('url') and len(alert.url.translation) > 0:
        alert_info['url'] = alert.url.translation[0].text
    
    # Extract severity level (if available)
    if alert.HasField('severity_level'):
        severity_map = {
            1: 'UNKNOWN',
            2: 'INFO',
            3: 'WARNING',
            4: 'SEVERE'
        }
        alert_info['severity_level'] = severity_map.get(alert.severity_level, 'UNKNOWN')
    
    return alert_info


@app.route('/trains', methods=['GET'])
def get_trains():
    """
    Get real-time train information with optional filtering.

    Query Parameters:
        city: Filter by city/region (default: 'mnr' for Metro-North Railroad)
        limit: Maximum number of trains to return (default: 20, max: 100)
        origin_station: Filter trains passing through this station (station ID)
        destination_station: Filter trains going to this destination (station ID)
        route: Filter by route/line ID
        time_from: Filter trains arriving after this time (HH:MM format)
        time_to: Filter trains arriving before this time (HH:MM format)

    Returns:
        JSON response with train information
    """
    try:
        # Get query parameters
        city = request.args.get('city', 'mnr').lower()
        limit_param = request.args.get('limit', 20)
        try:
            limit = int(limit_param)
        except (ValueError, TypeError):
            return jsonify({
                'error': f'Invalid value for "limit": {limit_param}. Must be an integer between 1 and 100.'
            }), 400
        if not (1 <= limit <= 100):
            return jsonify({
                'error': f'Invalid value for "limit": {limit}. Must be an integer between 1 and 100.'
            }), 400
        limit = min(limit, 100)
        origin_station = request.args.get('origin_station')
        destination_station = request.args.get('destination_station')
        route_filter = request.args.get('route')
        time_from = request.args.get('time_from')
        time_to = request.args.get('time_to')

        # Currently only supports MNR (Metro-North Railroad)
        if city not in ['mnr', 'metro-north', 'metronorth']:
            return jsonify({
                'error': 'Unsupported city. Currently only supports "mnr" (Metro-North Railroad)',
                'supported_cities': ['mnr', 'metro-north', 'metronorth']
            }), 400

        # Fetch the GTFS-RT feed
        feed = client.fetch_feed()

        # Extract trip updates
        all_trip_updates = client.get_trip_updates(feed)

        # Convert to simplified format and apply filters
        trains = []
        for trip_update in all_trip_updates:
            train_info = extract_train_info(trip_update)
            # Enrich with GTFS static data
            if gtfs_reader and gtfs_reader.is_loaded():
                train_info = gtfs_reader.enrich_train_info(train_info)
            
            # Apply filters
            if route_filter and train_info.get('route_id') != route_filter:
                continue
            
            if origin_station and not _train_passes_through_station(train_info, origin_station):
                continue
            
            if destination_station and not _train_goes_to_destination(train_info, destination_station):
                continue
            
            if time_from or time_to:
                if not _train_in_time_range(train_info, time_from, time_to):
                    continue
            
            trains.append(train_info)
            
            # Apply limit after filtering
            if len(trains) >= limit:
                break

        # Build response
        response = {
            'timestamp': timestamp_to_datetime(feed.header.timestamp),
            'city': 'mnr',
            'total_trains': len(trains),
            'trains': trains,
            'filters_applied': {
                'origin_station': origin_station,
                'destination_station': destination_station,
                'route': route_filter,
                'time_from': time_from,
                'time_to': time_to
            },
            'features': FEATURE_FLAGS
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
        app.logger.error(
            f"Unexpected error in /trains: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


def _train_passes_through_station(train_info, station_id):
    """
    Check if a train passes through a specific station.
    
    Args:
        train_info: Train information dictionary
        station_id: Station ID to check
        
    Returns:
        True if train passes through the station, False otherwise
    """
    if train_info.get('current_stop') == station_id:
        return True
    if train_info.get('next_stop') == station_id:
        return True
    for stop in train_info.get('stops', []):
        if stop.get('stop_id') == station_id:
            return True
    return False


def _train_goes_to_destination(train_info, station_id):
    """
    Check if a train's final destination is a specific station.
    
    Args:
        train_info: Train information dictionary
        station_id: Station ID to check
        
    Returns:
        True if train goes to the station, False otherwise
    """
    stops = train_info.get('stops', [])
    if stops and stops[-1].get('stop_id') == station_id:
        return True
    return False


def _train_in_time_range(train_info, time_from, time_to):
    """
    Check if a train's arrival time falls within a specified time range.
    
    Args:
        train_info: Train information dictionary
        time_from: Start time in HH:MM format (optional)
        time_to: End time in HH:MM format (optional)
        
    Returns:
        True if train is within time range, False otherwise
    """
    eta = train_info.get('eta')
    if not eta:
        return False
    
    try:
        # Parse ETA (ISO format)
        eta_dt = datetime.fromisoformat(eta.replace('Z', '+00:00'))
        eta_time = eta_dt.time()
        
        # Parse time_from if provided
        if time_from:
            from_parts = time_from.split(':')
            from_time = datetime.strptime(f"{from_parts[0]}:{from_parts[1]}", "%H:%M").time()
            if eta_time < from_time:
                return False
        
        # Parse time_to if provided
        if time_to:
            to_parts = time_to.split(':')
            to_time = datetime.strptime(f"{to_parts[0]}:{to_parts[1]}", "%H:%M").time()
            if eta_time > to_time:
                return False
        
        return True
    except (ValueError, IndexError) as e:
        logging.warning(
            f"Invalid time format in _train_in_time_range: eta='{eta}', time_from='{time_from}', time_to='{time_to}'. Error: {e}"
        )
        # If time parsing fails, exclude the train to be safe
        return False


@app.route('/stations', methods=['GET'])
def get_stations():
    """
    Get list of all available stations.
    
    Returns:
        JSON response with station information including IDs and names
    """
    try:
        if not gtfs_reader or not gtfs_reader.is_loaded():
            return jsonify({
                'error': 'GTFS static data not available. Stations cannot be listed.',
                'suggestion': 'Ensure GTFS data is loaded on server startup'
            }), 503
        
        stations = gtfs_reader.get_all_stops()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_stations': len(stations),
            'stations': stations
        })
    
    except Exception as e:
        app.logger.error(f"Unexpected error in /stations: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


@app.route('/routes', methods=['GET'])
def get_routes():
    """
    Get list of all available routes/lines.
    
    Returns:
        JSON response with route information including IDs, names, and colors
    """
    try:
        if not gtfs_reader or not gtfs_reader.is_loaded():
            return jsonify({
                'error': 'GTFS static data not available. Routes cannot be listed.',
                'suggestion': 'Ensure GTFS data is loaded on server startup'
            }), 503
        
        routes = gtfs_reader.get_all_routes()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_routes': len(routes),
            'routes': routes
        })
    
    except Exception as e:
        app.logger.error(f"Unexpected error in /routes: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


@app.route('/train/<trip_id>', methods=['GET'])
def get_train_details(trip_id):
    """
    Get detailed information about a specific train by trip ID.
    
    Args:
        trip_id: The trip ID of the train
        
    Returns:
        JSON response with detailed train information
    """
    try:
        # Fetch the GTFS-RT feed
        feed = client.fetch_feed()
        
        # Find the specific trip
        trip_updates = client.get_trip_updates(feed)
        train_info = None
        
        for trip_update in trip_updates:
            if trip_update.HasField('trip') and trip_update.trip.trip_id == trip_id:
                train_info = extract_train_info(trip_update)
                # Enrich with GTFS static data
                if gtfs_reader and gtfs_reader.is_loaded():
                    train_info = gtfs_reader.enrich_train_info(train_info)
                break
        
        if train_info is None:
            return jsonify({
                'error': f'Train with trip_id "{trip_id}" not found',
                'suggestion': 'Use /trains endpoint to list available trains'
            }), 404
        
        return jsonify({
            'timestamp': timestamp_to_datetime(feed.header.timestamp),
            'train': train_info
        })
    
    except requests.RequestException as e:
        app.logger.error(f"MTA API request failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch data from MTA API. Please try again later.'
        }), 503
    except Exception as e:
        app.logger.error(f"Unexpected error in /train/{trip_id}: {type(e).__name__}: {str(e)}")
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


@app.route('/vehicle-positions', methods=['GET'])
def get_vehicle_positions():
    """
    Get real-time vehicle position information.
    
    Query Parameters:
        limit: Maximum number of vehicles to return (default: 20, max: 100)
        route: Filter by route/line ID
        trip_id: Filter by specific trip ID
        
    Returns:
        JSON response with vehicle position information
    """
    try:
        # Get query parameters
        limit_param = request.args.get('limit', 20)
        try:
            limit = int(limit_param)
        except (ValueError, TypeError):
            return jsonify({
                'error': f'Invalid value for "limit": {limit_param}. Must be an integer between 1 and 100.'
            }), 400
        if not (1 <= limit <= 100):
            return jsonify({
                'error': f'Invalid value for "limit": {limit}. Must be an integer between 1 and 100.'
            }), 400
        limit = min(limit, 100)
        route_filter = request.args.get('route')
        trip_id_filter = request.args.get('trip_id')
        
        # Fetch the GTFS-RT feed
        feed = client.fetch_feed()
        
        # Extract vehicle positions
        all_vehicle_positions = client.get_vehicle_positions(feed)
        
        # Convert to simplified format and apply filters
        vehicles = []
        for vehicle_pos in all_vehicle_positions:
            position_info = extract_vehicle_position_info(vehicle_pos)
            
            # Enrich with GTFS static data
            if gtfs_reader and gtfs_reader.is_loaded():
                # Enrich route information
                route_id = position_info.get('route_id')
                if route_id:
                    route_info = gtfs_reader.get_route_info(route_id)
                    if route_info:
                        position_info['route_name'] = route_info.get('route_long_name', '')
                        position_info['route_color'] = route_info.get('route_color', '')
                
                # Enrich stop information
                stop_id = position_info.get('stop_id')
                if stop_id:
                    stop_info = gtfs_reader.get_stop_info(stop_id)
                    if stop_info:
                        position_info['stop_name'] = stop_info.get('stop_name', '')
            
            # Apply filters
            if route_filter and position_info.get('route_id') != route_filter:
                continue
            
            if trip_id_filter and position_info.get('trip_id') != trip_id_filter:
                continue
            
            vehicles.append(position_info)
            
            # Apply limit after filtering
            if len(vehicles) >= limit:
                break
        
        # Build response
        response = {
            'timestamp': timestamp_to_datetime(feed.header.timestamp),
            'total_vehicles': len(vehicles),
            'vehicles': vehicles,
            'filters_applied': {
                'route': route_filter,
                'trip_id': trip_id_filter
            }
        }
        
        return jsonify(response)
    
    except requests.RequestException as e:
        app.logger.error(f"MTA API request failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch data from MTA API. Please try again later.'
        }), 503
    except Exception as e:
        app.logger.error(f"Unexpected error in /vehicle-positions: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


@app.route('/alerts', methods=['GET'])
def get_alerts():
    """
    Get service alerts.
    
    Query Parameters:
        route: Filter by route/line ID
        stop: Filter by stop ID
        
    Returns:
        JSON response with service alert information
    """
    try:
        # Get query parameters
        route_filter = request.args.get('route')
        stop_filter = request.args.get('stop')
        
        # Fetch the GTFS-RT feed
        feed = client.fetch_feed()
        
        # Extract service alerts
        all_alerts = client.get_service_alerts(feed)
        
        # Convert to simplified format and apply filters
        alerts = []
        for alert in all_alerts:
            alert_info = extract_alert_info(alert)
            
            # Enrich with GTFS static data
            if gtfs_reader and gtfs_reader.is_loaded():
                for entity in alert_info.get('informed_entities', []):
                    # Enrich route information
                    route_id = entity.get('route_id')
                    if route_id:
                        route_info = gtfs_reader.get_route_info(route_id)
                        if route_info:
                            entity['route_name'] = route_info.get('route_long_name', '')
                    
                    # Enrich stop information
                    stop_id = entity.get('stop_id')
                    if stop_id:
                        stop_info = gtfs_reader.get_stop_info(stop_id)
                        if stop_info:
                            entity['stop_name'] = stop_info.get('stop_name', '')
            
            # Apply filters
            if route_filter or stop_filter:
                matches = False
                for entity in alert_info.get('informed_entities', []):
                    if route_filter and entity.get('route_id') == route_filter:
                        matches = True
                        break
                    if stop_filter and entity.get('stop_id') == stop_filter:
                        matches = True
                        break
                if not matches:
                    continue
            
            alerts.append(alert_info)
        
        # Build response
        response = {
            'timestamp': timestamp_to_datetime(feed.header.timestamp),
            'total_alerts': len(alerts),
            'alerts': alerts,
            'filters_applied': {
                'route': route_filter,
                'stop': stop_filter
            }
        }
        
        return jsonify(response)
    
    except requests.RequestException as e:
        app.logger.error(f"MTA API request failed: {str(e)}")
        return jsonify({
            'error': 'Failed to fetch data from MTA API. Please try again later.'
        }), 503
    except Exception as e:
        app.logger.error(f"Unexpected error in /alerts: {type(e).__name__}: {str(e)}")
        return jsonify({
            'error': 'An unexpected error occurred',
            'type': 'InternalServerError'
        }), 500


@app.route('/travel/location', methods=['GET'])
def get_network_location():
    """Get current network location."""
    if travel_assistant is None:
        return jsonify({
            'error': 'Travel assistance not configured',
            'suggestion': 'Configure travel_assist.yml to enable this feature'
        }), 503
    
    try:
        location = travel_assistant.get_current_location()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'location': location
        })
    
    except Exception as e:
        app.logger.error(f"Failed to get network location: {e}")
        return jsonify({
            'error': 'Failed to determine network location',
            'message': 'Please check server logs for details'
        }), 500


@app.route('/travel/distance', methods=['GET'])
def get_walking_distance():
    """Calculate walking distance to home station."""
    if travel_assistant is None:
        return jsonify({
            'error': 'Travel assistance not configured',
            'suggestion': 'Configure travel_assist.yml to enable this feature'
        }), 503
    
    try:
        distance_info = travel_assistant.calculate_distance_to_station()
        
        return jsonify({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'distance': distance_info,
            'formatted': travel_assistant.travel_calculator.format_distance_display(
                distance_info
            )
        })
    
    except Exception as e:
        app.logger.error(f"Failed to calculate walking distance: {e}")
        return jsonify({
            'error': 'Failed to calculate walking distance',
            'message': 'Please check server logs for details'
        }), 500


@app.route('/travel/next-train', methods=['GET'])
def get_next_train():
    """Get next optimal train based on current location."""
    if travel_assistant is None:
        return jsonify({
            'error': 'Travel assistance not configured',
            'suggestion': 'Configure travel_assist.yml to enable this feature'
        }), 503
    
    try:
        # Get optional parameters
        destination_id = request.args.get('destination')
        route_id = request.args.get('route')
        
        # Get complete travel status
        status = travel_assistant.get_travel_status(
            destination_station_id=destination_id,
            route_id=route_id
        )
        
        return jsonify({
            'timestamp': status['timestamp'],
            'location': status['location'],
            'distance': status['distance'],
            'recommended_train': status['recommended_train'],
            'other_trains': status['trains'][1:] if len(status['trains']) > 1 else [],
            'arduino_device': status.get('arduino_device'),
            'formatted_summary': travel_assistant.format_travel_summary(status)
        })
    
    except Exception as e:
        app.logger.error(f"Failed to get next train: {e}")
        return jsonify({
            'error': 'Failed to get next train',
            'message': 'Please check server logs for details'
        }), 500


@app.route('/travel/arduino-device', methods=['GET'])
def find_arduino():
    """Find Arduino webserver on the network."""
    if travel_assistant is None:
        return jsonify({
            'error': 'Travel assistance not configured',
            'suggestion': 'Configure travel_assist.yml to enable this feature'
        }), 503
    
    try:
        device = travel_assistant.find_arduino_device()
        
        if device:
            return jsonify({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'found': True,
                'device': device
            })
        else:
            return jsonify({
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'found': False,
                'message': 'No Arduino webserver found on network'
            })
    
    except Exception as e:
        app.logger.error(f"Failed to find Arduino device: {e}")
        return jsonify({
            'error': 'Failed to find Arduino device',
            'message': 'Please check server logs for details'
        }), 500


@app.route('/', methods=['GET'])
def index():
    """API information endpoint."""
    endpoints = {
        '/': 'This information page',
        '/health': 'Health check endpoint',
        '/trains': 'Get real-time train information with filtering options',
        '/stations': 'Get list of all available stations',
        '/routes': 'Get list of all available routes/lines',
        '/train/<trip_id>': 'Get detailed information about a specific train',
        '/vehicle-positions': 'Get real-time vehicle positions with location and occupancy data',
        '/alerts': 'Get service alerts for routes and stops'
    }
    
    usage_examples = {
        'get_trains': '/trains?city=mnr&limit=20',
        'filter_by_station': '/trains?origin_station=1&limit=10',
        'filter_by_route': '/trains?route=1&limit=10',
        'filter_by_time': '/trains?time_from=14:00&time_to=16:00',
        'get_stations': '/stations',
        'get_routes': '/routes',
        'get_train_details': '/train/1234567',
        'get_vehicle_positions': '/vehicle-positions?limit=20',
        'filter_vehicles_by_route': '/vehicle-positions?route=1&limit=10',
        'get_alerts': '/alerts',
        'filter_alerts_by_route': '/alerts?route=1',
        'health_check': '/health'
    }
    
    # Add travel assistance endpoints if configured
    if travel_assistant is not None:
        endpoints.update({
            '/travel/location': 'Get current network location',
            '/travel/distance': 'Calculate walking distance to home station',
            '/travel/next-train': 'Get next optimal train based on location',
            '/travel/arduino-device': 'Find Arduino webserver on network'
        })
        usage_examples.update({
            'get_location': '/travel/location',
            'get_distance': '/travel/distance',
            'get_next_train': '/travel/next-train?destination=<station_id>&route=<route_id>',
            'find_arduino': '/travel/arduino-device'
        })
    
    return jsonify({
        'service': 'MNR Real-Time Relay',
        'description': 'Simple JSON API for Metro-North Railroad real-time train data',
        'endpoints': endpoints,
        'features': FEATURE_FLAGS,
        'usage_examples': usage_examples,
        'travel_assistance': travel_assistant is not None
    })


def main():
    """Main entry point for the web server."""
    global client, gtfs_reader, travel_assistant

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
    parser.add_argument(
        '--skip-gtfs-update',
        action='store_true',
        help='Skip automatic GTFS data update on startup'
    )

    args = parser.parse_args()

    print("STARTUP_PHASE: INITIALIZING")
    print("Initializing MNR Real-Time Relay Server...")

    # Check for GTFS data updates on startup (unless skipped)
    if not args.skip_gtfs_update:
        print("STARTUP_PHASE: GTFS_CHECK")
        print("Checking for GTFS data updates...")
        downloader = GTFSDownloader(
            gtfs_url=GlobalSettings.GTFSDownloadSettings.GTFS_FEED_URL,
            output_dir=GlobalSettings.GTFS_MNR_DATA_DIR,
            min_download_interval=GlobalSettings.GTFSDownloadSettings.MIN_DOWNLOAD_INTERVAL
        )
        
        if downloader.should_download():
            print("STARTUP_PHASE: GTFS_DOWNLOAD")
            print("Downloading latest GTFS data...")
            try:
                success = downloader.download_and_extract()
                if success:
                    print("✓ GTFS data updated successfully")
                else:
                    print("⚠ GTFS data update failed (will use existing data)")
            except Exception as e:
                print(f"⚠ GTFS data update failed: {e} (will use existing data)")
        else:
            info = downloader.get_download_info()
            if info['last_download']:
                print(f"✓ GTFS data is up to date (last updated: {info['last_download']})")
            else:
                print("ℹ GTFS data exists (use update_gtfs.py to refresh)")
        print("STARTUP_PHASE: GTFS_CHECK_COMPLETE")
    else:
        print("STARTUP_PHASE: GTFS_CHECK_SKIPPED")

    # Initialize the GTFS client
    print("STARTUP_PHASE: CLIENT_INIT")
    print("Initializing GTFS real-time client...")
    client = MTAGTFSRealtimeClient(api_key=args.api_key)
    print("✓ GTFS real-time client initialized")
    
    # Initialize travel assistant if configured
    travel_config_path = Path(__file__).parent / 'config' / 'travel_assist.yml'
    if travel_config_path.exists():
        try:
            print("Initializing travel assistance...")
            with open(travel_config_path, 'r') as f:
                travel_config = yaml.safe_load(f)
            
            home_station = travel_config.get('home_station', {})
            api_keys = travel_config.get('api_keys', {})
            
            if home_station.get('station_id') and home_station.get('latitude') and home_station.get('longitude'):
                travel_assistant = TravelAssistant(
                    home_station_id=home_station['station_id'],
                    home_station_coords=(
                        home_station['latitude'],
                        home_station['longitude']
                    ),
                    mta_api_key=args.api_key or api_keys.get('mta_api_key'),
                    ors_api_key=api_keys.get('ors_api_key')
                )
                print("✓ Travel assistance initialized")
            else:
                print("⚠ Travel assistance config incomplete (skipping)")
        except Exception as e:
            print(f"⚠ Failed to initialize travel assistance: {e}")

    # Load GTFS static data for enrichment
    print("STARTUP_PHASE: GTFS_LOAD")
    print("Loading GTFS static data...")
    gtfs_reader = GTFSStaticReader(GlobalSettings.GTFS_MNR_DATA_DIR)
    if gtfs_reader.load():
        print("✓ GTFS static data loaded successfully")
    else:
        print("⚠ GTFS static data loading failed (real-time data will not be enriched)")

    print("STARTUP_PHASE: SERVER_START")
    print(f"Starting MNR Real-Time Relay Server on {args.host}:{args.port}")
    print(f"Access the API at: http://{args.host}:{args.port}/trains")
    print(f"View API info at: http://{args.host}:{args.port}/")

    # Run the Flask app
    print("STARTUP_PHASE: READY")
    print("✓ Server is ready and accepting connections")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    sys.exit(main())
