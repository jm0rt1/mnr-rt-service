"""
Integration test demonstrating GTFS-RT functionality with sample data
"""

import unittest
from src.mta_gtfs_client import MTAGTFSRealtimeClient
from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
from src.gtfs_realtime import mta_railroad_pb2


class TestGTFSRTIntegration(unittest.TestCase):
    """Integration test demonstrating full GTFS-RT workflow"""
    
    def test_full_workflow_with_mta_extensions(self):
        """Test complete workflow with MTA Railroad extensions"""
        
        # Create a sample feed with MTA Railroad extensions
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
        feed.header.timestamp = 1698249600
        
        # Add a trip update with MTA Railroad stop time extensions
        trip_entity = feed.entity.add()
        trip_entity.id = "trip_001"
        
        trip = trip_entity.trip_update.trip
        trip.trip_id = "MNR_TRIP_001"
        trip.route_id = "HUDSON"
        trip.start_date = "20251025"
        
        trip_entity.trip_update.vehicle.id = "TRAIN_123"
        
        # Add stop time update with MTA extension
        stu = trip_entity.trip_update.stop_time_update.add()
        stu.stop_id = "STOP_GCT"
        stu.arrival.delay = 120  # 2 minutes late
        stu.departure.delay = 180  # 3 minutes late
        
        # Add MTA Railroad extension for track and status
        mta_stop_ext = stu.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
        mta_stop_ext.track = "42"
        mta_stop_ext.trainStatus = "On Time"
        
        # Add another stop
        stu2 = trip_entity.trip_update.stop_time_update.add()
        stu2.stop_id = "STOP_125"
        stu2.arrival.delay = 60
        mta_stop_ext2 = stu2.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
        mta_stop_ext2.track = "1"
        mta_stop_ext2.trainStatus = "Approaching"
        
        # Add a vehicle position with MTA Railroad carriage extensions
        vehicle_entity = feed.entity.add()
        vehicle_entity.id = "vehicle_001"
        
        vehicle = vehicle_entity.vehicle
        vehicle.trip.trip_id = "MNR_TRIP_001"
        vehicle.trip.route_id = "HUDSON"
        vehicle.vehicle.id = "TRAIN_123"
        vehicle.position.latitude = 40.7527
        vehicle.position.longitude = -73.9772
        vehicle.current_stop_sequence = 1
        vehicle.stop_id = "STOP_GCT"
        
        # Add carriage details with MTA extensions
        carriage1 = vehicle.multi_carriage_details.add()
        carriage1.id = "CAR_1"
        carriage1.label = "First Class"
        
        mta_carriage1 = carriage1.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
        mta_carriage1.bicycles_allowed = 2
        mta_carriage1.carriage_class = "Premium"
        mta_carriage1.quiet_carriage = mta_railroad_pb2.MtaRailroadCarriageDetails.QUIET_CARRIAGE
        mta_carriage1.toilet_facilities = mta_railroad_pb2.MtaRailroadCarriageDetails.TOILET_ONBOARD
        
        carriage2 = vehicle.multi_carriage_details.add()
        carriage2.id = "CAR_2"
        carriage2.label = "Standard"
        
        mta_carriage2 = carriage2.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
        mta_carriage2.bicycles_allowed = 0  # No bikes
        mta_carriage2.carriage_class = "Standard"
        mta_carriage2.quiet_carriage = mta_railroad_pb2.MtaRailroadCarriageDetails.NOT_QUIET_CARRIAGE
        mta_carriage2.toilet_facilities = mta_railroad_pb2.MtaRailroadCarriageDetails.NO_TOILET_ONBOARD
        
        # Add a service alert
        alert_entity = feed.entity.add()
        alert_entity.id = "alert_001"
        
        alert = alert_entity.alert
        translation = alert.header_text.translation.add()
        translation.text = "Delays on Hudson Line"
        
        desc_translation = alert.description_text.translation.add()
        desc_translation.text = "Trains on the Hudson Line are experiencing delays of up to 15 minutes due to signal problems."
        
        affected = alert.informed_entity.add()
        affected.route_id = "HUDSON"
        
        # Now test the client with this feed
        client = MTAGTFSRealtimeClient()
        
        # Test trip updates
        trip_updates = client.get_trip_updates(feed)
        self.assertEqual(len(trip_updates), 1)
        
        trip_update = trip_updates[0]
        self.assertEqual(trip_update.trip.trip_id, "MNR_TRIP_001")
        self.assertEqual(trip_update.trip.route_id, "HUDSON")
        self.assertEqual(len(trip_update.stop_time_update), 2)
        
        # Verify MTA Railroad stop time extensions
        stu_first = trip_update.stop_time_update[0]
        self.assertTrue(stu_first.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update))
        mta_ext = stu_first.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
        self.assertEqual(mta_ext.track, "42")
        self.assertEqual(mta_ext.trainStatus, "On Time")
        
        # Test vehicle positions
        vehicle_positions = client.get_vehicle_positions(feed)
        self.assertEqual(len(vehicle_positions), 1)
        
        vehicle_pos = vehicle_positions[0]
        self.assertEqual(vehicle_pos.vehicle.id, "TRAIN_123")
        self.assertEqual(len(vehicle_pos.multi_carriage_details), 2)
        
        # Verify MTA Railroad carriage extensions
        carriage_first = vehicle_pos.multi_carriage_details[0]
        self.assertTrue(carriage_first.HasExtension(mta_railroad_pb2.mta_railroad_carriage_details))
        mta_carriage = carriage_first.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
        self.assertEqual(mta_carriage.bicycles_allowed, 2)
        self.assertEqual(mta_carriage.carriage_class, "Premium")
        self.assertEqual(mta_carriage.quiet_carriage, mta_railroad_pb2.MtaRailroadCarriageDetails.QUIET_CARRIAGE)
        self.assertEqual(mta_carriage.toilet_facilities, mta_railroad_pb2.MtaRailroadCarriageDetails.TOILET_ONBOARD)
        
        carriage_second = vehicle_pos.multi_carriage_details[1]
        mta_carriage2 = carriage_second.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
        self.assertEqual(mta_carriage2.bicycles_allowed, 0)
        self.assertEqual(mta_carriage2.quiet_carriage, mta_railroad_pb2.MtaRailroadCarriageDetails.NOT_QUIET_CARRIAGE)
        
        # Test service alerts
        alerts = client.get_service_alerts(feed)
        self.assertEqual(len(alerts), 1)
        
        alert = alerts[0]
        self.assertEqual(alert.header_text.translation[0].text, "Delays on Hudson Line")
        self.assertEqual(len(alert.informed_entity), 1)
        self.assertEqual(alert.informed_entity[0].route_id, "HUDSON")
        
        print("\n=== Integration Test Successful ===")
        print(f"Feed contains {len(feed.entity)} entities")
        print(f"Trip Updates: {len(trip_updates)}")
        print(f"Vehicle Positions: {len(vehicle_positions)}")
        print(f"Service Alerts: {len(alerts)}")
        print("\nMTA Railroad Extensions verified:")
        print(f"  - Track information: {mta_ext.track}")
        print(f"  - Train status: {mta_ext.trainStatus}")
        print(f"  - Carriage details: {len(vehicle_pos.multi_carriage_details)} carriages")
        print(f"  - Quiet carriage support: Yes")
        print(f"  - Toilet facilities support: Yes")
        print(f"  - Bicycle allowance support: Yes")


if __name__ == '__main__':
    unittest.main()
