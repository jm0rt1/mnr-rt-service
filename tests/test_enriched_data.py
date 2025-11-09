"""
Unit tests for enriched data endpoints (vehicle positions and alerts)
"""

from src.gtfs_realtime import mta_railroad_pb2
from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
from web_server import app, extract_vehicle_position_info, extract_alert_info
import unittest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class TestEnrichedData(unittest.TestCase):
    """Test cases for enriched data endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True

    def test_extract_vehicle_position_basic(self):
        """Test extracting basic vehicle position information"""
        vehicle_pos = gtfs_realtime_pb2.VehiclePosition()
        vehicle_pos.trip.trip_id = "TEST_TRIP_123"
        vehicle_pos.trip.route_id = "TEST_ROUTE"
        vehicle_pos.vehicle.id = "TEST_VEHICLE_456"
        vehicle_pos.position.latitude = 40.7589
        vehicle_pos.position.longitude = -73.9851
        vehicle_pos.position.bearing = 180.0
        vehicle_pos.position.speed = 25.5
        vehicle_pos.current_stop_sequence = 5
        vehicle_pos.stop_id = "STOP_5"
        vehicle_pos.current_status = 2  # IN_TRANSIT_TO
        vehicle_pos.timestamp = 1234567890
        vehicle_pos.occupancy_status = 2  # FEW_SEATS_AVAILABLE
        vehicle_pos.occupancy_percentage = 75

        info = extract_vehicle_position_info(vehicle_pos)

        self.assertEqual(info['trip_id'], "TEST_TRIP_123")
        self.assertEqual(info['route_id'], "TEST_ROUTE")
        self.assertEqual(info['vehicle_id'], "TEST_VEHICLE_456")
        self.assertAlmostEqual(info['latitude'], 40.7589, places=4)
        self.assertAlmostEqual(info['longitude'], -73.9851, places=4)
        self.assertAlmostEqual(info['bearing'], 180.0, places=1)
        self.assertAlmostEqual(info['speed'], 25.5, places=1)
        self.assertEqual(info['current_stop_sequence'], 5)
        self.assertEqual(info['stop_id'], "STOP_5")
        self.assertEqual(info['current_status'], 'IN_TRANSIT_TO')
        self.assertIsNotNone(info['timestamp'])
        self.assertEqual(info['occupancy_status'], 'FEW_SEATS_AVAILABLE')
        self.assertEqual(info['occupancy_percentage'], 75)
        self.assertEqual(len(info['carriages']), 0)

    def test_extract_vehicle_position_with_carriages(self):
        """Test extracting vehicle position with carriage details"""
        vehicle_pos = gtfs_realtime_pb2.VehiclePosition()
        vehicle_pos.trip.trip_id = "TEST_TRIP"
        
        # Add a carriage with MTA extensions
        carriage = vehicle_pos.multi_carriage_details.add()
        carriage.id = "CAR_1"
        carriage.label = "Car 1234"
        carriage.carriage_sequence = 1
        carriage.occupancy_status = 3  # STANDING_ROOM_ONLY
        carriage.occupancy_percentage = 90
        
        # Add MTA Railroad extensions
        mta_ext = carriage.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
        mta_ext.bicycles_allowed = 2
        mta_ext.carriage_class = "M8"
        mta_ext.quiet_carriage = 1  # QUIET_CARRIAGE
        mta_ext.toilet_facilities = 1  # TOILET_ONBOARD

        info = extract_vehicle_position_info(vehicle_pos)
        
        self.assertEqual(len(info['carriages']), 1)
        carriage_info = info['carriages'][0]
        self.assertEqual(carriage_info['id'], "CAR_1")
        self.assertEqual(carriage_info['label'], "Car 1234")
        self.assertEqual(carriage_info['sequence'], 1)
        self.assertEqual(carriage_info['occupancy_status'], 'STANDING_ROOM_ONLY')
        self.assertEqual(carriage_info['occupancy_percentage'], 90)
        self.assertEqual(carriage_info['bicycles_allowed'], 2)
        self.assertEqual(carriage_info['carriage_class'], "M8")
        self.assertTrue(carriage_info['quiet_carriage'])
        self.assertTrue(carriage_info['toilet_facilities'])

    def test_extract_alert_basic(self):
        """Test extracting basic alert information"""
        alert = gtfs_realtime_pb2.Alert()
        
        # Add active period
        period = alert.active_period.add()
        period.start = 1234567890
        period.end = 1234571490
        
        # Add informed entity
        entity = alert.informed_entity.add()
        entity.route_id = "1"
        entity.stop_id = "STOP_1"
        
        # Set cause and effect
        alert.cause = 8  # WEATHER
        alert.effect = 3  # SIGNIFICANT_DELAYS
        
        # Set header and description
        header_translation = alert.header_text.translation.add()
        header_translation.text = "Service Alert"
        header_translation.language = "en"
        
        desc_translation = alert.description_text.translation.add()
        desc_translation.text = "Delays due to weather"
        desc_translation.language = "en"

        info = extract_alert_info(alert)
        
        self.assertEqual(len(info['active_periods']), 1)
        self.assertIsNotNone(info['active_periods'][0]['start'])
        self.assertIsNotNone(info['active_periods'][0]['end'])
        
        self.assertEqual(len(info['informed_entities']), 1)
        self.assertEqual(info['informed_entities'][0]['route_id'], "1")
        self.assertEqual(info['informed_entities'][0]['stop_id'], "STOP_1")
        
        self.assertEqual(info['cause'], 'WEATHER')
        self.assertEqual(info['effect'], 'SIGNIFICANT_DELAYS')
        self.assertEqual(info['header_text'], "Service Alert")
        self.assertEqual(info['description_text'], "Delays due to weather")

    @patch('web_server.client')
    def test_vehicle_positions_endpoint(self, mock_client):
        """Test /vehicle-positions endpoint"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890
        
        # Add vehicle positions
        vehicle_positions = []
        for i in range(3):
            vehicle_pos = gtfs_realtime_pb2.VehiclePosition()
            vehicle_pos.trip.trip_id = f"TRIP_{i}"
            vehicle_pos.trip.route_id = "1"
            vehicle_pos.vehicle.id = f"VEH_{i}"
            vehicle_pos.position.latitude = 40.7589 + i * 0.01
            vehicle_pos.position.longitude = -73.9851 + i * 0.01
            vehicle_positions.append(vehicle_pos)
        
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_vehicle_positions.return_value = vehicle_positions
        
        response = self.app.get('/vehicle-positions')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('vehicles', data)
        self.assertEqual(len(data['vehicles']), 3)
        self.assertEqual(data['total_vehicles'], 3)
        
        # Check that vehicle data is present
        vehicle = data['vehicles'][0]
        self.assertEqual(vehicle['trip_id'], "TRIP_0")
        self.assertEqual(vehicle['route_id'], "1")
        self.assertIsNotNone(vehicle['latitude'])
        self.assertIsNotNone(vehicle['longitude'])

    @patch('web_server.client')
    def test_vehicle_positions_endpoint_with_filters(self, mock_client):
        """Test /vehicle-positions endpoint with filters"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890
        
        # Add vehicle positions on different routes
        vehicle_positions = []
        for i in range(5):
            vehicle_pos = gtfs_realtime_pb2.VehiclePosition()
            vehicle_pos.trip.trip_id = f"TRIP_{i}"
            vehicle_pos.trip.route_id = "1" if i < 3 else "2"
            vehicle_pos.vehicle.id = f"VEH_{i}"
            vehicle_positions.append(vehicle_pos)
        
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_vehicle_positions.return_value = vehicle_positions
        
        # Test route filter
        response = self.app.get('/vehicle-positions?route=1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['vehicles']), 3)
        
        # Test limit
        response = self.app.get('/vehicle-positions?limit=2')
        data = json.loads(response.data)
        self.assertEqual(len(data['vehicles']), 2)

    @patch('web_server.client')
    def test_alerts_endpoint(self, mock_client):
        """Test /alerts endpoint"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890
        
        # Add alerts
        alerts = []
        for i in range(2):
            alert = gtfs_realtime_pb2.Alert()
            entity = alert.informed_entity.add()
            entity.route_id = f"{i + 1}"
            alert.cause = 8  # WEATHER
            alert.effect = 3  # SIGNIFICANT_DELAYS
            header = alert.header_text.translation.add()
            header.text = f"Alert {i + 1}"
            alerts.append(alert)
        
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_service_alerts.return_value = alerts
        
        response = self.app.get('/alerts')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('alerts', data)
        self.assertEqual(len(data['alerts']), 2)
        self.assertEqual(data['total_alerts'], 2)
        
        # Check alert data
        alert = data['alerts'][0]
        self.assertEqual(alert['cause'], 'WEATHER')
        self.assertEqual(alert['effect'], 'SIGNIFICANT_DELAYS')
        self.assertIn('header_text', alert)

    @patch('web_server.client')
    def test_alerts_endpoint_with_filter(self, mock_client):
        """Test /alerts endpoint with route filter"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890
        
        # Add alerts for different routes
        alerts = []
        for i in range(3):
            alert = gtfs_realtime_pb2.Alert()
            entity = alert.informed_entity.add()
            entity.route_id = "1" if i < 2 else "2"
            alerts.append(alert)
        
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_service_alerts.return_value = alerts
        
        # Test route filter
        response = self.app.get('/alerts?route=1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(len(data['alerts']), 2)


if __name__ == '__main__':
    unittest.main()
