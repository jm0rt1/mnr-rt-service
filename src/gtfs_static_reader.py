"""
GTFS Static Data Reader

This module provides functionality to read and cache GTFS static schedule data
(routes, stops, trips) to enrich real-time data with additional metadata.
"""

import csv
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class GTFSStaticReader:
    """
    Reads and caches GTFS static schedule data.
    
    This class loads routes, stops, and trips from GTFS text files
    and provides fast lookup methods to enrich real-time data.
    """
    
    def __init__(self, gtfs_dir: Path):
        """
        Initialize the GTFS static data reader.
        
        Args:
            gtfs_dir: Path to directory containing GTFS text files
        """
        self.gtfs_dir = Path(gtfs_dir)
        self._routes: Dict[str, dict] = {}
        self._stops: Dict[str, dict] = {}
        self._trips: Dict[str, dict] = {}
        self._loaded = False
    
    def load(self) -> bool:
        """
        Load GTFS static data from text files.
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            self._load_routes()
            self._load_stops()
            self._load_trips()
            self._loaded = True
            logger.info(f"Loaded GTFS data: {len(self._routes)} routes, "
                       f"{len(self._stops)} stops, {len(self._trips)} trips")
            return True
        except Exception as e:
            logger.error(f"Failed to load GTFS static data: {e}")
            self._loaded = False
            return False
    
    def _load_routes(self):
        """Load routes from routes.txt"""
        routes_file = self.gtfs_dir / "routes.txt"
        if not routes_file.exists():
            logger.warning(f"Routes file not found: {routes_file}")
            return
        
        with open(routes_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                route_id = row.get('route_id')
                if route_id:
                    self._routes[route_id] = {
                        'route_long_name': row.get('route_long_name', ''),
                        'route_short_name': row.get('route_short_name', ''),
                        'route_color': row.get('route_color', ''),
                        'route_text_color': row.get('route_text_color', ''),
                        'route_type': row.get('route_type', ''),
                        'route_desc': row.get('route_desc', ''),  # NEW: Route description
                        'route_url': row.get('route_url', ''),  # NEW: Route URL
                    }
    
    def _load_stops(self):
        """Load stops from stops.txt"""
        stops_file = self.gtfs_dir / "stops.txt"
        if not stops_file.exists():
            logger.warning(f"Stops file not found: {stops_file}")
            return
        
        with open(stops_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                stop_id = row.get('stop_id')
                if stop_id:
                    self._stops[stop_id] = {
                        'stop_name': row.get('stop_name', ''),
                        'stop_code': row.get('stop_code', ''),
                        'stop_lat': row.get('stop_lat', ''),
                        'stop_lon': row.get('stop_lon', ''),
                        'wheelchair_boarding': row.get('wheelchair_boarding', ''),
                        'stop_desc': row.get('stop_desc', ''),  # NEW: Stop description
                        'stop_url': row.get('stop_url', ''),  # NEW: Stop URL
                        'zone_id': row.get('zone_id', ''),  # NEW: Fare zone
                        'location_type': row.get('location_type', ''),  # NEW: Location type
                        'parent_station': row.get('parent_station', ''),  # NEW: Parent station
                        'platform_code': row.get('platform_code', ''),  # NEW: Platform code
                    }
    
    def _load_trips(self):
        """Load trips from trips.txt"""
        trips_file = self.gtfs_dir / "trips.txt"
        if not trips_file.exists():
            logger.warning(f"Trips file not found: {trips_file}")
            return
        
        with open(trips_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trip_id = row.get('trip_id')
                if trip_id:
                    self._trips[trip_id] = {
                        'trip_headsign': row.get('trip_headsign', ''),
                        'trip_short_name': row.get('trip_short_name', ''),
                        'direction_id': row.get('direction_id', ''),
                        'route_id': row.get('route_id', ''),
                        'block_id': row.get('block_id', ''),  # NEW: Block identifier
                        'shape_id': row.get('shape_id', ''),  # NEW: Shape for trip path
                        'wheelchair_accessible': row.get('wheelchair_accessible', ''),  # NEW: Wheelchair accessibility
                        'bikes_allowed': row.get('bikes_allowed', ''),  # NEW: Bike allowance
                    }
    
    def get_route_info(self, route_id: str) -> Optional[dict]:
        """
        Get route information by route ID.
        
        Args:
            route_id: The route ID to lookup
            
        Returns:
            Dictionary with route info, or None if not found
        """
        return self._routes.get(route_id)
    
    def get_stop_info(self, stop_id: str) -> Optional[dict]:
        """
        Get stop information by stop ID.
        
        Args:
            stop_id: The stop ID to lookup
            
        Returns:
            Dictionary with stop info, or None if not found
        """
        return self._stops.get(stop_id)
    
    def get_trip_info(self, trip_id: str) -> Optional[dict]:
        """
        Get trip information by trip ID.
        
        Args:
            trip_id: The trip ID to lookup
            
        Returns:
            Dictionary with trip info, or None if not found
        """
        return self._trips.get(trip_id)
    
    def is_loaded(self) -> bool:
        """Check if GTFS data has been loaded."""
        return self._loaded
    
    def get_all_stops(self) -> list:
        """
        Get all available stops/stations.
        
        Returns:
            List of dictionaries with stop information
        """
        if not self._loaded:
            return []
        
        stops_list = []
        for stop_id, stop_info in self._stops.items():
            stops_list.append({
                'stop_id': stop_id,
                'stop_name': stop_info.get('stop_name', ''),
                'stop_code': stop_info.get('stop_code', ''),
                'stop_lat': stop_info.get('stop_lat', ''),
                'stop_lon': stop_info.get('stop_lon', ''),
                'wheelchair_boarding': stop_info.get('wheelchair_boarding', '')
            })
        
        # Sort by stop name for easier browsing
        stops_list.sort(key=lambda x: x['stop_name'])
        return stops_list
    
    def get_all_routes(self) -> list:
        """
        Get all available routes/lines.
        
        Returns:
            List of dictionaries with route information
        """
        if not self._loaded:
            return []
        
        routes_list = []
        for route_id, route_info in self._routes.items():
            routes_list.append({
                'route_id': route_id,
                'route_long_name': route_info.get('route_long_name', ''),
                'route_short_name': route_info.get('route_short_name', ''),
                'route_color': route_info.get('route_color', ''),
                'route_text_color': route_info.get('route_text_color', ''),
                'route_type': route_info.get('route_type', '')
            })
        
        # Sort by route ID for consistency
        routes_list.sort(key=lambda x: x['route_id'])
        return routes_list
    
    def enrich_train_info(self, train_info: dict) -> dict:
        """
        Enrich train information with GTFS static data.
        
        Args:
            train_info: Dictionary with basic train information
            
        Returns:
            Enriched train information dictionary
        """
        if not self._loaded:
            return train_info
        
        # Enrich route information
        route_id = train_info.get('route_id')
        if route_id:
            route_info = self.get_route_info(route_id)
            if route_info:
                train_info['route_name'] = route_info.get('route_long_name', '')
                train_info['route_color'] = route_info.get('route_color', '')
                # NEW: Add additional route fields if available
                if route_info.get('route_desc'):
                    train_info['route_desc'] = route_info.get('route_desc', '')
                if route_info.get('route_url'):
                    train_info['route_url'] = route_info.get('route_url', '')
        
        # Enrich trip information
        trip_id = train_info.get('trip_id')
        if trip_id:
            trip_info = self.get_trip_info(trip_id)
            if trip_info:
                train_info['trip_headsign'] = trip_info.get('trip_headsign', '')
                train_info['direction_id'] = trip_info.get('direction_id', '')
                # NEW: Add additional trip fields if available
                if trip_info.get('wheelchair_accessible'):
                    train_info['wheelchair_accessible'] = trip_info.get('wheelchair_accessible', '')
                if trip_info.get('bikes_allowed'):
                    train_info['bikes_allowed'] = trip_info.get('bikes_allowed', '')
        
        # Enrich current stop
        current_stop = train_info.get('current_stop')
        if current_stop:
            stop_info = self.get_stop_info(current_stop)
            if stop_info:
                train_info['current_stop_name'] = stop_info.get('stop_name', '')
                # NEW: Add platform code if available
                if stop_info.get('platform_code'):
                    train_info['current_platform_code'] = stop_info.get('platform_code', '')
        
        # Enrich next stop
        next_stop = train_info.get('next_stop')
        if next_stop:
            stop_info = self.get_stop_info(next_stop)
            if stop_info:
                train_info['next_stop_name'] = stop_info.get('stop_name', '')
                # NEW: Add platform code if available
                if stop_info.get('platform_code'):
                    train_info['next_platform_code'] = stop_info.get('platform_code', '')
        
        # Enrich all stops in the stops list
        if 'stops' in train_info:
            for stop in train_info['stops']:
                stop_id = stop.get('stop_id')
                if stop_id:
                    stop_info = self.get_stop_info(stop_id)
                    if stop_info:
                        stop['stop_name'] = stop_info.get('stop_name', '')
                        stop['stop_lat'] = stop_info.get('stop_lat', '')
                        stop['stop_lon'] = stop_info.get('stop_lon', '')
        
        return train_info
