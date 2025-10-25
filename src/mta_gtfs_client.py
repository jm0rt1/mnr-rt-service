"""
MTA Metro-North Railroad GTFS-RT API Client

This module provides functionality to fetch and parse real-time transit data
from the MTA Metro-North Railroad GTFS-RT API.
"""

import requests
from typing import Optional
from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
from src.gtfs_realtime import mta_railroad_pb2


class MTAGTFSRealtimeClient:
    """
    Client for accessing MTA Metro-North Railroad GTFS-RT API.
    
    The API provides real-time transit information including:
    - Trip updates with track and train status information
    - Vehicle positions with carriage details
    """
    
    # MTA Metro-North Railroad GTFS-RT API endpoint
    API_URL = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the MTA GTFS-RT client.
        
        Args:
            api_key: Optional API key for authentication (if required by MTA)
        """
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
    
    def fetch_feed(self) -> gtfs_realtime_pb2.FeedMessage:
        """
        Fetch the GTFS-RT feed from the MTA API.
        
        Returns:
            FeedMessage: Parsed protobuf FeedMessage containing real-time data
            
        Raises:
            requests.RequestException: If the API request fails
            google.protobuf.message.DecodeError: If the response cannot be parsed
        """
        response = self.session.get(self.API_URL, timeout=30)
        response.raise_for_status()
        
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed
    
    def get_trip_updates(self, feed: Optional[gtfs_realtime_pb2.FeedMessage] = None):
        """
        Extract trip updates from the feed.
        
        Args:
            feed: Optional FeedMessage to parse. If None, fetches a new feed.
            
        Returns:
            list: List of TripUpdate entities with MTA Railroad extensions
        """
        if feed is None:
            feed = self.fetch_feed()
        
        trip_updates = []
        for entity in feed.entity:
            if entity.HasField('trip_update'):
                trip_updates.append(entity.trip_update)
        
        return trip_updates
    
    def get_vehicle_positions(self, feed: Optional[gtfs_realtime_pb2.FeedMessage] = None):
        """
        Extract vehicle positions from the feed.
        
        Args:
            feed: Optional FeedMessage to parse. If None, fetches a new feed.
            
        Returns:
            list: List of VehiclePosition entities with MTA Railroad extensions
        """
        if feed is None:
            feed = self.fetch_feed()
        
        vehicle_positions = []
        for entity in feed.entity:
            if entity.HasField('vehicle'):
                vehicle_positions.append(entity.vehicle)
        
        return vehicle_positions
    
    def get_service_alerts(self, feed: Optional[gtfs_realtime_pb2.FeedMessage] = None):
        """
        Extract service alerts from the feed.
        
        Args:
            feed: Optional FeedMessage to parse. If None, fetches a new feed.
            
        Returns:
            list: List of Alert entities
        """
        if feed is None:
            feed = self.fetch_feed()
        
        alerts = []
        for entity in feed.entity:
            if entity.HasField('alert'):
                alerts.append(entity.alert)
        
        return alerts
    
    def print_trip_update_details(self, trip_update):
        """
        Print detailed information about a trip update including MTA Railroad extensions.
        
        Args:
            trip_update: TripUpdate entity to display
        """
        print(f"\n=== Trip Update ===")
        
        if trip_update.HasField('trip'):
            trip = trip_update.trip
            print(f"Trip ID: {trip.trip_id if trip.HasField('trip_id') else 'N/A'}")
            print(f"Route ID: {trip.route_id if trip.HasField('route_id') else 'N/A'}")
            print(f"Start Date: {trip.start_date if trip.HasField('start_date') else 'N/A'}")
        
        if trip_update.HasField('vehicle'):
            vehicle = trip_update.vehicle
            print(f"Vehicle ID: {vehicle.id if vehicle.HasField('id') else 'N/A'}")
        
        print(f"\nStop Time Updates: {len(trip_update.stop_time_update)}")
        for i, stu in enumerate(trip_update.stop_time_update):
            print(f"\n  Stop {i + 1}:")
            print(f"    Stop ID: {stu.stop_id if stu.HasField('stop_id') else 'N/A'}")
            
            if stu.HasField('arrival'):
                print(f"    Arrival Delay: {stu.arrival.delay if stu.arrival.HasField('delay') else 'N/A'} seconds")
            
            if stu.HasField('departure'):
                print(f"    Departure Delay: {stu.departure.delay if stu.departure.HasField('delay') else 'N/A'} seconds")
            
            # MTA Railroad extension
            if stu.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update):
                mta_ext = stu.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
                print(f"    Track: {mta_ext.track if mta_ext.HasField('track') else 'N/A'}")
                print(f"    Train Status: {mta_ext.trainStatus if mta_ext.HasField('trainStatus') else 'N/A'}")
    
    def print_vehicle_position_details(self, vehicle_position):
        """
        Print detailed information about a vehicle position including MTA Railroad extensions.
        
        Args:
            vehicle_position: VehiclePosition entity to display
        """
        print(f"\n=== Vehicle Position ===")
        
        if vehicle_position.HasField('trip'):
            trip = vehicle_position.trip
            print(f"Trip ID: {trip.trip_id if trip.HasField('trip_id') else 'N/A'}")
            print(f"Route ID: {trip.route_id if trip.HasField('route_id') else 'N/A'}")
        
        if vehicle_position.HasField('vehicle'):
            vehicle = vehicle_position.vehicle
            print(f"Vehicle ID: {vehicle.id if vehicle.HasField('id') else 'N/A'}")
        
        if vehicle_position.HasField('position'):
            pos = vehicle_position.position
            print(f"Latitude: {pos.latitude if pos.HasField('latitude') else 'N/A'}")
            print(f"Longitude: {pos.longitude if pos.HasField('longitude') else 'N/A'}")
        
        if vehicle_position.HasField('current_stop_sequence'):
            print(f"Current Stop Sequence: {vehicle_position.current_stop_sequence}")
        
        if vehicle_position.HasField('stop_id'):
            print(f"Stop ID: {vehicle_position.stop_id}")
        
        # MTA Railroad carriage details extension
        print(f"\nCarriage Details: {len(vehicle_position.multi_carriage_details)}")
        for i, carriage in enumerate(vehicle_position.multi_carriage_details):
            print(f"\n  Carriage {i + 1}:")
            print(f"    Carriage ID: {carriage.id if carriage.HasField('id') else 'N/A'}")
            print(f"    Label: {carriage.label if carriage.HasField('label') else 'N/A'}")
            
            if carriage.HasExtension(mta_railroad_pb2.mta_railroad_carriage_details):
                mta_ext = carriage.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
                
                if mta_ext.HasField('bicycles_allowed'):
                    bikes = mta_ext.bicycles_allowed
                    if bikes == -1:
                        print(f"    Bicycles: No limit")
                    elif bikes == 0:
                        print(f"    Bicycles: Prohibited")
                    else:
                        print(f"    Bicycles: {bikes} allowed")
                
                print(f"    Carriage Class: {mta_ext.carriage_class if mta_ext.HasField('carriage_class') else 'N/A'}")
                
                if mta_ext.HasField('quiet_carriage'):
                    quiet = mta_ext.quiet_carriage
                    if quiet == mta_railroad_pb2.MtaRailroadCarriageDetails.QUIET_CARRIAGE:
                        print(f"    Quiet Carriage: Yes")
                    elif quiet == mta_railroad_pb2.MtaRailroadCarriageDetails.NOT_QUIET_CARRIAGE:
                        print(f"    Quiet Carriage: No")
                    else:
                        print(f"    Quiet Carriage: Unknown")
                
                if mta_ext.HasField('toilet_facilities'):
                    toilet = mta_ext.toilet_facilities
                    if toilet == mta_railroad_pb2.MtaRailroadCarriageDetails.TOILET_ONBOARD:
                        print(f"    Toilet Facilities: Yes")
                    elif toilet == mta_railroad_pb2.MtaRailroadCarriageDetails.NO_TOILET_ONBOARD:
                        print(f"    Toilet Facilities: No")
                    else:
                        print(f"    Toilet Facilities: Unknown")
