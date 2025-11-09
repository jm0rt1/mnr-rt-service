"""
Departure Time Optimization Module

Provides intelligent departure time suggestions based on:
- Real-time train schedules
- Walking distance and time
- Train delays and status
- User preferences

Features:
- Optimal train selection
- Dynamic delay handling
- Multiple departure options
- Real-time notifications
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.mta_gtfs_client import MTAGTFSRealtimeClient

logger = logging.getLogger(__name__)


class DepartureScheduler:
    """
    Optimize departure times based on train schedules and walking distance.
    
    Integrates with MTA GTFS real-time data to suggest the best trains
    to catch based on current location and walking time.
    """
    
    def __init__(
        self,
        mta_client: MTAGTFSRealtimeClient,
        min_buffer_minutes: int = 3,
        max_suggestions: int = 3
    ):
        """
        Initialize the DepartureScheduler.
        
        Args:
            mta_client: MTA GTFS real-time client instance
            min_buffer_minutes: Minimum buffer time at station before train
            max_suggestions: Maximum number of train suggestions to return
        """
        self.mta_client = mta_client
        self.min_buffer = timedelta(minutes=min_buffer_minutes)
        self.max_suggestions = max_suggestions
    
    def find_optimal_trains(
        self,
        origin_station_id: str,
        destination_station_id: Optional[str],
        walking_duration_minutes: float,
        current_time: Optional[datetime] = None,
        route_id: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Find optimal trains to catch based on walking time.
        
        Args:
            origin_station_id: Station ID to depart from
            destination_station_id: Destination station ID (optional)
            walking_duration_minutes: Walking time to origin station
            current_time: Current time (default: now)
            route_id: Filter by specific route (optional)
            
        Returns:
            List of train suggestions, each containing:
                - trip_id: str
                - route_id: str
                - route_name: str
                - departure_time: datetime
                - leave_time: datetime (when to start walking)
                - walking_duration: timedelta
                - buffer_time: timedelta
                - status: str
                - track: str
                - feasible: bool (can you catch it?)
                - minutes_until_departure: float
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Fetch real-time train data
        try:
            feed = self.mta_client.fetch_feed()
            trip_updates = self.mta_client.get_trip_updates(feed)
        except Exception as e:
            logger.error(f"Failed to fetch train data: {e}")
            return []
        
        suggestions = []
        
        for trip_update in trip_updates:
            # Check if this train stops at our origin station
            train_info = self._extract_train_info(
                trip_update,
                origin_station_id,
                destination_station_id,
                walking_duration_minutes,
                current_time,
                route_id
            )
            
            if train_info:
                suggestions.append(train_info)
        
        # Sort by departure time
        suggestions.sort(key=lambda x: x['departure_time'])
        
        # Return top N suggestions
        result = suggestions[:self.max_suggestions]
        
        logger.info(
            f"Found {len(result)} optimal train suggestions "
            f"for station {origin_station_id}"
        )
        
        return result
    
    async def find_optimal_trains_async(
        self,
        origin_station_id: str,
        destination_station_id: Optional[str],
        walking_duration_minutes: float,
        current_time: Optional[datetime] = None,
        route_id: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """
        Async version of find_optimal_trains.
        
        Uses asyncio to fetch train data without blocking.
        """
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.find_optimal_trains,
            origin_station_id,
            destination_station_id,
            walking_duration_minutes,
            current_time,
            route_id
        )
    
    def _extract_train_info(
        self,
        trip_update,
        origin_station_id: str,
        destination_station_id: Optional[str],
        walking_duration_minutes: float,
        current_time: datetime,
        route_id: Optional[str]
    ) -> Optional[Dict[str, any]]:
        """
        Extract relevant train information for scheduling.
        
        Args:
            trip_update: GTFS-RT trip update message
            origin_station_id: Origin station to check
            destination_station_id: Destination station to check
            walking_duration_minutes: Walking time to station
            current_time: Current time
            route_id: Filter by route (optional)
            
        Returns:
            Train info dictionary or None if not suitable
        """
        try:
            # Get trip details
            trip = trip_update.trip
            trip_id = trip.trip_id if trip.HasField('trip_id') else None
            trip_route_id = trip.route_id if trip.HasField('route_id') else None
            
            # Filter by route if specified
            if route_id and trip_route_id != route_id:
                return None
            
            # Check stop time updates
            for stu in trip_update.stop_time_update:
                stop_id = stu.stop_id if stu.HasField('stop_id') else None
                
                # Check if this is our origin station
                if stop_id != origin_station_id:
                    continue
                
                # Get departure time
                if not stu.HasField('departure'):
                    continue
                
                departure = stu.departure
                if not departure.HasField('time'):
                    continue
                
                departure_time = datetime.fromtimestamp(departure.time)
                
                # Calculate if this train is feasible
                walking_td = timedelta(minutes=walking_duration_minutes)
                required_leave_time = departure_time - walking_td - self.min_buffer
                
                feasible = required_leave_time >= current_time
                minutes_until = (departure_time - current_time).total_seconds() / 60.0
                
                # Get track information (MTA extension)
                track = None
                if hasattr(stu, 'Extensions'):
                    try:
                        from src.gtfs_realtime import mta_railroad_pb2
                        ext = stu.Extensions[mta_railroad_pb2.nyct_stop_time_update]
                        if ext.HasField('track'):
                            track = ext.track
                    except Exception as e:
                        # Could not access MTA extension for track info; log and continue
                        logger.debug(f"Failed to get track info from MTA extension: {e}", exc_info=True)
                
                # Get train status
                status = "On Time"
                if departure.HasField('delay'):
                    delay_sec = departure.delay
                    if delay_sec > 60:
                        status = f"Delayed {delay_sec // 60} min"
                
                # Check if train goes to destination (if specified)
                goes_to_destination = True
                if destination_station_id:
                    goes_to_destination = self._check_destination(
                        trip_update,
                        destination_station_id
                    )
                
                if not goes_to_destination:
                    return None
                
                return {
                    'trip_id': trip_id,
                    'route_id': trip_route_id,
                    'route_name': self._get_route_name(trip_route_id),
                    'departure_time': departure_time,
                    'leave_time': required_leave_time,
                    'walking_duration': walking_td,
                    'buffer_time': self.min_buffer,
                    'status': status,
                    'track': track or 'TBD',
                    'feasible': feasible,
                    'minutes_until_departure': minutes_until
                }
        
        except Exception as e:
            logger.debug(f"Failed to extract train info: {e}")
        
        return None
    
    def _check_destination(
        self,
        trip_update,
        destination_station_id: str
    ) -> bool:
        """
        Check if train stops at destination station.
        
        Args:
            trip_update: GTFS-RT trip update
            destination_station_id: Station ID to check
            
        Returns:
            True if train stops at destination
        """
        for stu in trip_update.stop_time_update:
            stop_id = stu.stop_id if stu.HasField('stop_id') else None
            if stop_id == destination_station_id:
                return True
        return False
    
    def _get_route_name(self, route_id: str) -> str:
        """
        Get human-readable route name.
        
        Args:
            route_id: Route ID
            
        Returns:
            Route name (e.g., "Hudson", "Harlem", "New Haven")
        """
        route_names = {
            '1': 'Hudson',
            '2': 'Harlem',
            '3': 'New Haven',
            '4': 'Pascack Valley',
            '5': 'Port Jervis',
            '6': 'Wassaic'
        }
        return route_names.get(route_id, f"Route {route_id}")
    
    def suggest_departure(
        self,
        train_suggestions: List[Dict[str, any]],
        preference: str = 'earliest'
    ) -> Optional[Dict[str, any]]:
        """
        Suggest the best train based on user preference.
        
        Args:
            train_suggestions: List of train suggestions
            preference: 'earliest' or 'most_time' (most buffer time)
            
        Returns:
            Best train suggestion or None
        """
        if not train_suggestions:
            return None
        
        # Filter to only feasible trains
        feasible = [t for t in train_suggestions if t['feasible']]
        
        if not feasible:
            logger.warning("No feasible trains found")
            return None
        
        if preference == 'earliest':
            # Return earliest feasible train
            return feasible[0]
        
        elif preference == 'most_time':
            # Return train with most buffer time
            return max(
                feasible,
                key=lambda t: (t['departure_time'] - datetime.now()).total_seconds()
            )
        
        else:
            # Default to earliest
            return feasible[0]
    
    def format_suggestion(
        self,
        suggestion: Dict[str, any],
        include_countdown: bool = True
    ) -> str:
        """
        Format train suggestion for display.
        
        Args:
            suggestion: Train suggestion dictionary
            include_countdown: Whether to include countdown timer
            
        Returns:
            Formatted string for display
        """
        parts = []
        
        # Route and status
        parts.append(f"{suggestion['route_name']} Line")
        parts.append(f"Track {suggestion['track']}")
        parts.append(f"({suggestion['status']})")
        
        # Times
        depart_str = suggestion['departure_time'].strftime('%I:%M %p')
        leave_str = suggestion['leave_time'].strftime('%I:%M %p')
        
        parts.append(f"\nDeparture: {depart_str}")
        parts.append(f"Leave by: {leave_str}")
        
        # Countdown
        if include_countdown:
            minutes = int(suggestion['minutes_until_departure'])
            parts.append(f"\n⏱ {minutes} minutes until departure")
        
        # Feasibility
        if not suggestion['feasible']:
            parts.append("\n⚠ Too late to catch this train")
        else:
            parts.append("\n✓ Feasible")
        
        return ' '.join(parts)
    
    def create_notification_message(
        self,
        suggestion: Dict[str, any],
        notification_time_minutes: int = 5
    ) -> Optional[str]:
        """
        Create notification message for when to leave.
        
        Args:
            suggestion: Train suggestion
            notification_time_minutes: Minutes before leave time to notify
            
        Returns:
            Notification message or None if not time yet
        """
        now = datetime.now()
        notify_at = suggestion['leave_time'] - timedelta(
            minutes=notification_time_minutes
        )
        
        if now >= notify_at and now < suggestion['leave_time']:
            leave_str = suggestion['leave_time'].strftime('%I:%M %p')
            route = suggestion['route_name']
            track = suggestion['track']
            
            return (
                f"🚂 Time to leave for {route} Line train!\n"
                f"Leave by {leave_str} to catch train on Track {track}"
            )
        
        return None
