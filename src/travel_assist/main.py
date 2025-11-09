"""
Travel Assistant Main Orchestrator

Coordinates all travel assistance components:
- Network location detection
- Walking distance calculations
- Departure time optimization

This is the main entry point for the travel assistance functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from .network_locator import NetworkLocator
from .travel_calculator import TravelCalculator
from .scheduler import DepartureScheduler
from src.mta_gtfs_client import MTAGTFSRealtimeClient

logger = logging.getLogger(__name__)


class TravelAssistant:
    """
    Main orchestrator for travel assistance functionality.
    
    Coordinates network location detection, walking distance calculation,
    and optimal departure time suggestions in a single, easy-to-use interface.
    """
    
    def __init__(
        self,
        home_station_id: str,
        home_station_coords: Tuple[float, float],
        mta_api_key: Optional[str] = None,
        ors_api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize the TravelAssistant.
        
        Args:
            home_station_id: ID of home train station
            home_station_coords: Coordinates of home station (lat, lon)
            mta_api_key: MTA API key (optional)
            ors_api_key: OpenRouteService API key (optional)
            cache_dir: Directory for caching data
        """
        self.home_station_id = home_station_id
        self.home_station_coords = home_station_coords
        
        # Initialize components
        self.network_locator = NetworkLocator(cache_dir=cache_dir)
        self.travel_calculator = TravelCalculator(ors_api_key=ors_api_key)
        
        # Initialize MTA client
        self.mta_client = MTAGTFSRealtimeClient(api_key=mta_api_key)
        self.scheduler = DepartureScheduler(
            mta_client=self.mta_client,
            min_buffer_minutes=3
        )
        
        logger.info("TravelAssistant initialized")
    
    def get_travel_status(
        self,
        destination_station_id: Optional[str] = None,
        route_id: Optional[str] = None,
        use_cached_location: bool = True
    ) -> Dict[str, any]:
        """
        Get complete travel status including location, distance, and train suggestions.
        
        This is the main method that orchestrates all functionality.
        
        Args:
            destination_station_id: Destination station (optional)
            route_id: Preferred route (optional)
            use_cached_location: Whether to use cached location data
            
        Returns:
            Dictionary containing:
                - location: Network location info
                - distance: Walking distance and time
                - trains: List of suggested trains
                - recommended_train: Best train to catch
                - arduino_device: Arduino webserver info (if found)
        """
        try:
            # Step 1: Get network location
            logger.info("Determining network location...")
            location = self.network_locator.get_network_location(
                use_cache=use_cached_location
            )
            
            current_coords = (location['latitude'], location['longitude'])
            
            # Step 2: Calculate walking distance to home station
            logger.info("Calculating walking distance to station...")
            distance = self.travel_calculator.calculate_walking_distance(
                from_location=current_coords,
                to_location=self.home_station_coords,
                use_routing=True
            )
            
            # Step 3: Find optimal trains
            logger.info("Finding optimal trains...")
            trains = self.scheduler.find_optimal_trains(
                origin_station_id=self.home_station_id,
                destination_station_id=destination_station_id,
                walking_duration_minutes=distance['duration_minutes'],
                route_id=route_id
            )
            
            # Step 4: Get recommended train
            recommended = self.scheduler.suggest_departure(
                trains,
                preference='earliest'
            )
            
            # Step 5: Try to find Arduino device (non-blocking)
            arduino_device = None
            try:
                arduino_device = self.network_locator.find_arduino_webserver()
            except Exception as e:
                logger.warning(f"Failed to find Arduino device: {e}")
            
            result = {
                'location': location,
                'distance': distance,
                'trains': trains,
                'recommended_train': recommended,
                'arduino_device': arduino_device,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Travel status retrieved successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get travel status: {e}")
            raise
    
    async def get_travel_status_async(
        self,
        destination_station_id: Optional[str] = None,
        route_id: Optional[str] = None,
        use_cached_location: bool = True
    ) -> Dict[str, any]:
        """
        Async version of get_travel_status.
        
        Performs all operations concurrently for better performance.
        """
        try:
            # Get location (sync - fast with cache)
            location = self.network_locator.get_network_location(
                use_cache=use_cached_location
            )
            current_coords = (location['latitude'], location['longitude'])
            
            # Create async tasks for concurrent execution
            distance_task = self.travel_calculator.calculate_walking_distance_async(
                from_location=current_coords,
                to_location=self.home_station_coords,
                use_routing=True
            )
            
            # Wait for distance calculation
            distance = await distance_task
            
            # Now get trains based on walking duration
            trains_task = self.scheduler.find_optimal_trains_async(
                origin_station_id=self.home_station_id,
                destination_station_id=destination_station_id,
                walking_duration_minutes=distance['duration_minutes'],
                route_id=route_id
            )
            
            trains = await trains_task
            
            # Get recommended train
            recommended = self.scheduler.suggest_departure(
                trains,
                preference='earliest'
            )
            
            # Try to find Arduino device (non-blocking)
            arduino_device = None
            try:
                # Run in executor to not block
                loop = asyncio.get_event_loop()
                arduino_device = await loop.run_in_executor(
                    None,
                    self.network_locator.find_arduino_webserver
                )
            except Exception as e:
                logger.warning(f"Failed to find Arduino device: {e}")
            
            result = {
                'location': location,
                'distance': distance,
                'trains': trains,
                'recommended_train': recommended,
                'arduino_device': arduino_device,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info("Travel status retrieved successfully (async)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get travel status (async): {e}")
            raise
    
    def get_current_location(self, use_cache: bool = True) -> Dict[str, any]:
        """
        Get current network location only.
        
        Args:
            use_cache: Whether to use cached location data (default: True)
        
        Returns:
            Location information dictionary
        """
        return self.network_locator.get_network_location(use_cache=use_cache)
    
    def calculate_distance_to_station(
        self,
        from_coords: Optional[Tuple[float, float]] = None
    ) -> Dict[str, any]:
        """
        Calculate walking distance to home station.
        
        Args:
            from_coords: Starting coordinates (lat, lon)
                        If None, uses current network location
                        
        Returns:
            Distance information dictionary
        """
        if from_coords is None:
            location = self.network_locator.get_network_location()
            from_coords = (location['latitude'], location['longitude'])
        
        return self.travel_calculator.calculate_walking_distance(
            from_location=from_coords,
            to_location=self.home_station_coords,
            use_routing=True
        )
    
    def get_next_trains(
        self,
        destination_station_id: Optional[str] = None,
        route_id: Optional[str] = None,
        walking_duration_minutes: Optional[float] = None
    ) -> List[Dict[str, any]]:
        """
        Get next available trains.
        
        Args:
            destination_station_id: Destination station (optional)
            route_id: Preferred route (optional)
            walking_duration_minutes: Walking time (if None, calculated automatically)
            
        Returns:
            List of train suggestions
        """
        if walking_duration_minutes is None:
            distance = self.calculate_distance_to_station()
            walking_duration_minutes = distance['duration_minutes']
        
        return self.scheduler.find_optimal_trains(
            origin_station_id=self.home_station_id,
            destination_station_id=destination_station_id,
            walking_duration_minutes=walking_duration_minutes,
            route_id=route_id
        )
    
    def find_arduino_device(self) -> Optional[Dict[str, any]]:
        """
        Find Arduino webserver on the network.
        
        Returns:
            Arduino device information or None
        """
        return self.network_locator.find_arduino_webserver()
    
    def format_travel_summary(
        self,
        travel_status: Dict[str, any],
        verbose: bool = False
    ) -> str:
        """
        Format travel status for display.
        
        Args:
            travel_status: Result from get_travel_status
            verbose: Include detailed information
            
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Location
        loc = travel_status['location']
        lines.append(f"📍 Current Location: {loc['city']}, {loc['country']}")
        if verbose:
            lines.append(f"   IP: {loc['ip']} ({loc['isp']})")
            lines.append(f"   Coordinates: {loc['latitude']:.4f}, {loc['longitude']:.4f}")
        
        # Distance
        dist = travel_status['distance']
        dist_str = self.travel_calculator.format_distance_display(dist)
        lines.append(f"\n🚶 Distance to Station: {dist_str}")
        
        # Recommended train
        recommended = travel_status.get('recommended_train')
        if recommended:
            lines.append("\n🚂 Recommended Train:")
            lines.append(f"   {self.scheduler.format_suggestion(recommended)}")
        else:
            lines.append("\n⚠ No feasible trains found")
        
        # Other trains
        trains = travel_status.get('trains', [])
        if len(trains) > 1 and verbose:
            lines.append("\n📋 Other Options:")
            for train in trains[1:]:
                route = train['route_name']
                time = train['departure_time'].strftime('%I:%M %p')
                status = train['status']
                lines.append(f"   - {route} @ {time} ({status})")
        
        # Arduino device
        arduino = travel_status.get('arduino_device')
        if arduino:
            lines.append(f"\n🔌 Arduino Device: {arduino['ip']}:{arduino['port']}")
        
        return '\n'.join(lines)
