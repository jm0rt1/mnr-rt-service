#!/usr/bin/env python3
"""
MTA Metro-North Railroad GTFS-RT Demo Program

This program demonstrates how to fetch and display real-time transit data
from the MTA Metro-North Railroad GTFS-RT API.

Usage:
    python mnr_gtfs_demo.py [--api-key YOUR_API_KEY]
"""

import argparse
import sys
from src.mta_gtfs_client import MTAGTFSRealtimeClient


def main():
    """Main entry point for the MTA GTFS-RT demo program."""
    
    parser = argparse.ArgumentParser(
        description='Fetch and display MTA Metro-North Railroad real-time transit data'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='Optional API key for MTA API authentication',
        default=None
    )
    parser.add_argument(
        '--max-trips',
        type=int,
        help='Maximum number of trip updates to display',
        default=5
    )
    parser.add_argument(
        '--max-vehicles',
        type=int,
        help='Maximum number of vehicle positions to display',
        default=5
    )
    parser.add_argument(
        '--max-alerts',
        type=int,
        help='Maximum number of service alerts to display',
        default=5
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("MTA Metro-North Railroad GTFS-RT Feed Demo")
    print("=" * 80)
    
    try:
        # Initialize client
        client = MTAGTFSRealtimeClient(api_key=args.api_key)
        
        # Fetch the feed
        print("\nFetching GTFS-RT feed...")
        feed = client.fetch_feed()
        
        # Display feed header information
        print(f"\nFeed Header:")
        print(f"  GTFS Realtime Version: {feed.header.gtfs_realtime_version}")
        print(f"  Incrementality: {feed.header.incrementality}")
        print(f"  Timestamp: {feed.header.timestamp}")
        
        # Count different entity types
        trip_updates = client.get_trip_updates(feed)
        vehicle_positions = client.get_vehicle_positions(feed)
        alerts = client.get_service_alerts(feed)
        
        print(f"\nFeed Statistics:")
        print(f"  Total Entities: {len(feed.entity)}")
        print(f"  Trip Updates: {len(trip_updates)}")
        print(f"  Vehicle Positions: {len(vehicle_positions)}")
        print(f"  Service Alerts: {len(alerts)}")
        
        # Display trip updates
        if trip_updates:
            print("\n" + "=" * 80)
            print(f"TRIP UPDATES (showing up to {args.max_trips})")
            print("=" * 80)
            
            for i, trip_update in enumerate(trip_updates[:args.max_trips]):
                client.print_trip_update_details(trip_update)
        
        # Display vehicle positions
        if vehicle_positions:
            print("\n" + "=" * 80)
            print(f"VEHICLE POSITIONS (showing up to {args.max_vehicles})")
            print("=" * 80)
            
            for i, vehicle_pos in enumerate(vehicle_positions[:args.max_vehicles]):
                client.print_vehicle_position_details(vehicle_pos)
        
        # Display service alerts
        if alerts:
            print("\n" + "=" * 80)
            print(f"SERVICE ALERTS (showing up to {args.max_alerts})")
            print("=" * 80)
            
            for i, alert in enumerate(alerts[:args.max_alerts]):
                print(f"\n=== Alert {i + 1} ===")
                
                # Display header text
                if alert.header_text.translation:
                    print(f"Header: {alert.header_text.translation[0].text}")
                
                # Display description
                if alert.description_text.translation:
                    print(f"Description: {alert.description_text.translation[0].text}")
                
                # Display affected entities
                if alert.informed_entity:
                    print(f"Affected Entities:")
                    for entity in alert.informed_entity:
                        if entity.HasField('route_id'):
                            print(f"  - Route: {entity.route_id}")
                        if entity.HasField('trip'):
                            print(f"  - Trip: {entity.trip.trip_id}")
        
        print("\n" + "=" * 80)
        print("Feed fetch completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
