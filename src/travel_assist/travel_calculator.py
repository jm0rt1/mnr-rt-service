"""
Travel Distance and Time Calculation Module

Provides walking distance and time calculations using mapping APIs.
Integrates with OpenRouteService for pedestrian routing.

Features:
- Walking distance calculations
- Walking time estimates
- Route optimization
- Traffic and weather considerations
- Async API calls for performance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import aiohttp

logger = logging.getLogger(__name__)


class TravelCalculator:
    """
    Calculate walking distances and travel times to train stations.
    
    Uses OpenRouteService API for accurate pedestrian routing with
    consideration for real-world conditions.
    """
    
    # OpenRouteService API (free tier: 2000 requests/day)
    ORS_API_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"
    
    # Fallback: direct distance calculation
    EARTH_RADIUS_KM = 6371.0
    
    # Walking speed estimates (km/h)
    WALKING_SPEEDS = {
        'slow': 3.0,      # Leisurely pace
        'normal': 5.0,    # Average pace
        'fast': 6.5,      # Brisk pace
    }
    
    def __init__(
        self,
        ors_api_key: Optional[str] = None,
        default_walking_speed: str = 'normal',
        safety_buffer_minutes: int = 2
    ):
        """
        Initialize the TravelCalculator.
        
        Args:
            ors_api_key: OpenRouteService API key (optional, uses free tier if None)
            default_walking_speed: Default walking speed ('slow', 'normal', 'fast')
            safety_buffer_minutes: Extra minutes added to walking time estimate
        """
        self.ors_api_key = ors_api_key
        self.default_walking_speed = default_walking_speed
        self.safety_buffer = timedelta(minutes=safety_buffer_minutes)
        self.session = requests.Session()
        
        if ors_api_key:
            self.session.headers.update({
                'Authorization': ors_api_key
            })
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MNR-RT-Service-TravelAssist/1.0'
        })
    
    def calculate_walking_distance(
        self,
        from_location: Tuple[float, float],
        to_location: Tuple[float, float],
        use_routing: bool = True
    ) -> Dict[str, any]:
        """
        Calculate walking distance between two locations.
        
        Args:
            from_location: Tuple of (latitude, longitude) for start
            to_location: Tuple of (latitude, longitude) for destination
            use_routing: If True, use routing API; if False, use direct distance
            
        Returns:
            Dictionary containing:
                - distance_km: float (distance in kilometers)
                - distance_miles: float (distance in miles)
                - duration_minutes: float (estimated walking time)
                - route_points: List[Tuple[float, float]] (route waypoints if available)
                - method: str ('routing' or 'direct')
        """
        if use_routing and self.ors_api_key:
            try:
                return self._calculate_via_routing(from_location, to_location)
            except Exception as e:
                logger.warning(f"Routing API failed, using direct distance: {e}")
        
        # Fallback to direct distance calculation
        return self._calculate_direct_distance(from_location, to_location)
    
    async def calculate_walking_distance_async(
        self,
        from_location: Tuple[float, float],
        to_location: Tuple[float, float],
        use_routing: bool = True
    ) -> Dict[str, any]:
        """
        Async version of calculate_walking_distance.
        
        Args:
            from_location: Tuple of (latitude, longitude) for start
            to_location: Tuple of (latitude, longitude) for destination
            use_routing: If True, use routing API; if False, use direct distance
            
        Returns:
            Same as calculate_walking_distance
        """
        if use_routing and self.ors_api_key:
            try:
                return await self._calculate_via_routing_async(
                    from_location, 
                    to_location
                )
            except Exception as e:
                logger.warning(f"Routing API failed, using direct distance: {e}")
        
        # Direct calculation doesn't need async
        return self._calculate_direct_distance(from_location, to_location)
    
    def _calculate_via_routing(
        self,
        from_location: Tuple[float, float],
        to_location: Tuple[float, float]
    ) -> Dict[str, any]:
        """
        Calculate route using OpenRouteService API.
        
        Args:
            from_location: Start coordinates (lat, lon)
            to_location: End coordinates (lat, lon)
            
        Returns:
            Route information dictionary
        """
        # ORS uses lon, lat order (not lat, lon!)
        coordinates = [
            [from_location[1], from_location[0]],  # Start: [lon, lat]
            [to_location[1], to_location[0]]       # End: [lon, lat]
        ]
        
        payload = {
            "coordinates": coordinates,
            "profile": "foot-walking",
            "format": "json",
            "units": "km"
        }
        
        try:
            response = self.session.post(
                self.ORS_API_URL,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract route information
            route = data['routes'][0]
            summary = route['summary']
            
            distance_km = summary['distance'] / 1000.0  # Convert m to km
            duration_sec = summary['duration']
            
            # Extract route waypoints
            geometry = route['geometry']['coordinates']
            route_points = [(lat, lon) for lon, lat in geometry]
            
            result = {
                'distance_km': distance_km,
                'distance_miles': distance_km * 0.621371,
                'duration_minutes': duration_sec / 60.0,
                'route_points': route_points,
                'method': 'routing'
            }
            
            logger.info(
                f"Calculated route: {distance_km:.2f} km, "
                f"{result['duration_minutes']:.1f} min"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"OpenRouteService API error: {e}")
            raise
    
    async def _calculate_via_routing_async(
        self,
        from_location: Tuple[float, float],
        to_location: Tuple[float, float]
    ) -> Dict[str, any]:
        """
        Async version of _calculate_via_routing.
        """
        # ORS uses lon, lat order
        coordinates = [
            [from_location[1], from_location[0]],
            [to_location[1], to_location[0]]
        ]
        
        payload = {
            "coordinates": coordinates,
            "profile": "foot-walking",
            "format": "json",
            "units": "km"
        }
        
        headers = dict(self.session.headers)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ORS_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # Extract route information (same as sync version)
            route = data['routes'][0]
            summary = route['summary']
            
            distance_km = summary['distance'] / 1000.0
            duration_sec = summary['duration']
            
            geometry = route['geometry']['coordinates']
            route_points = [(lat, lon) for lon, lat in geometry]
            
            result = {
                'distance_km': distance_km,
                'distance_miles': distance_km * 0.621371,
                'duration_minutes': duration_sec / 60.0,
                'route_points': route_points,
                'method': 'routing'
            }
            
            logger.info(
                f"Calculated route (async): {distance_km:.2f} km, "
                f"{result['duration_minutes']:.1f} min"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"OpenRouteService API error (async): {e}")
            raise
    
    def _calculate_direct_distance(
        self,
        from_location: Tuple[float, float],
        to_location: Tuple[float, float]
    ) -> Dict[str, any]:
        """
        Calculate direct (great-circle) distance using Haversine formula.
        
        Args:
            from_location: Start coordinates (lat, lon)
            to_location: End coordinates (lat, lon)
            
        Returns:
            Distance information dictionary
        """
        import math
        
        lat1, lon1 = math.radians(from_location[0]), math.radians(from_location[1])
        lat2, lon2 = math.radians(to_location[0]), math.radians(to_location[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = (math.sin(dlat / 2) ** 2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance_km = self.EARTH_RADIUS_KM * c
        
        # Estimate walking time based on direct distance
        # Add 20% for real-world routing
        walking_distance_km = distance_km * 1.2
        walking_speed_kmh = self.WALKING_SPEEDS[self.default_walking_speed]
        duration_minutes = (walking_distance_km / walking_speed_kmh) * 60.0
        
        result = {
            'distance_km': walking_distance_km,
            'distance_miles': walking_distance_km * 0.621371,
            'duration_minutes': duration_minutes,
            'route_points': [from_location, to_location],
            'method': 'direct'
        }
        
        logger.info(
            f"Calculated direct distance: {walking_distance_km:.2f} km, "
            f"{duration_minutes:.1f} min"
        )
        
        return result
    
    def estimate_walking_time(
        self,
        distance_km: float,
        walking_speed: Optional[str] = None,
        include_buffer: bool = True
    ) -> Dict[str, any]:
        """
        Estimate walking time for a given distance.
        
        Args:
            distance_km: Distance in kilometers
            walking_speed: Speed category ('slow', 'normal', 'fast')
            include_buffer: Whether to include safety buffer
            
        Returns:
            Dictionary containing:
                - duration_minutes: float (total walking time)
                - base_duration_minutes: float (without buffer)
                - buffer_minutes: int (safety buffer)
                - speed_category: str
        """
        speed = walking_speed or self.default_walking_speed
        speed_kmh = self.WALKING_SPEEDS.get(speed, self.WALKING_SPEEDS['normal'])
        
        base_duration = (distance_km / speed_kmh) * 60.0  # Convert to minutes
        
        result = {
            'base_duration_minutes': base_duration,
            'buffer_minutes': self.safety_buffer.seconds / 60,
            'speed_category': speed,
            'speed_kmh': speed_kmh
        }
        
        if include_buffer:
            result['duration_minutes'] = base_duration + result['buffer_minutes']
        else:
            result['duration_minutes'] = base_duration
        
        return result
    
    def calculate_departure_time(
        self,
        train_time: datetime,
        walking_duration_minutes: float,
        extra_buffer_minutes: int = 0
    ) -> Dict[str, any]:
        """
        Calculate when to leave to catch a train.
        
        Args:
            train_time: Train departure time
            walking_duration_minutes: Walking time to station
            extra_buffer_minutes: Additional buffer (for unexpected delays)
            
        Returns:
            Dictionary containing:
                - leave_time: datetime (when to leave)
                - walking_duration: timedelta
                - total_buffer: timedelta
                - arrival_time: datetime (estimated arrival at station)
        """
        walking_td = timedelta(minutes=walking_duration_minutes)
        buffer_td = self.safety_buffer + timedelta(minutes=extra_buffer_minutes)
        total_buffer = buffer_td
        
        # Calculate leave time: train_time - walking_time - buffer
        leave_time = train_time - walking_td - total_buffer
        arrival_time = leave_time + walking_td
        
        result = {
            'leave_time': leave_time,
            'walking_duration': walking_td,
            'total_buffer': total_buffer,
            'arrival_time': arrival_time,
            'train_time': train_time
        }
        
        logger.info(
            f"Departure calculation: Leave at {leave_time.strftime('%H:%M:%S')} "
            f"to catch {train_time.strftime('%H:%M:%S')} train"
        )
        
        return result
    
    def format_distance_display(
        self,
        distance_info: Dict[str, any],
        use_metric: bool = True
    ) -> str:
        """
        Format distance information for display.
        
        Args:
            distance_info: Distance dictionary from calculate_walking_distance
            use_metric: If True, show km; if False, show miles
            
        Returns:
            Formatted string (e.g., "2.5 km (31 min walk)")
        """
        if use_metric:
            dist_str = f"{distance_info['distance_km']:.2f} km"
        else:
            dist_str = f"{distance_info['distance_miles']:.2f} miles"
        
        duration_str = f"{int(distance_info['duration_minutes'])} min walk"
        
        return f"{dist_str} ({duration_str})"
