"""
Unit tests for MTA GTFS-RT Client
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.mta_gtfs_client import MTAGTFSRealtimeClient
from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2


class TestMTAGTFSRealtimeClient(unittest.TestCase):
    """Test cases for MTAGTFSRealtimeClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = MTAGTFSRealtimeClient()
    
    def test_init_without_api_key(self):
        """Test client initialization without API key"""
        client = MTAGTFSRealtimeClient()
        self.assertIsNone(client.api_key)
        self.assertIsNotNone(client.session)
    
    def test_init_with_api_key(self):
        """Test client initialization with API key"""
        api_key = "test_api_key_123"
        client = MTAGTFSRealtimeClient(api_key=api_key)
        self.assertEqual(client.api_key, api_key)
        self.assertEqual(client.session.headers.get('x-api-key'), api_key)
    
    def test_api_url(self):
        """Test that API URL is correctly set"""
        expected_url = "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr"
        self.assertEqual(MTAGTFSRealtimeClient.API_URL, expected_url)
    
    @patch('src.mta_gtfs_client.requests.Session.get')
    def test_fetch_feed_success(self, mock_get):
        """Test successful feed fetch"""
        # Create a mock feed message
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.gtfs_realtime_version = "2.0"
        mock_feed.header.incrementality = gtfs_realtime_pb2.FeedHeader.FULL_DATASET
        mock_feed.header.timestamp = 1234567890
        
        # Mock the response
        mock_response = Mock()
        mock_response.content = mock_feed.SerializeToString()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Fetch the feed
        feed = self.client.fetch_feed()
        
        # Verify the request was made correctly
        mock_get.assert_called_once_with(self.client.API_URL, timeout=30)
        
        # Verify the feed was parsed correctly
        self.assertEqual(feed.header.gtfs_realtime_version, "2.0")
        self.assertEqual(feed.header.timestamp, 1234567890)
    
    @patch('src.mta_gtfs_client.requests.Session.get')
    def test_fetch_feed_http_error(self, mock_get):
        """Test feed fetch with HTTP error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.client.fetch_feed()
    
    def test_get_trip_updates(self):
        """Test extracting trip updates from feed"""
        # Create a mock feed with trip updates
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        
        # Add a trip update entity
        entity = feed.entity.add()
        entity.id = "trip_1"
        entity.trip_update.trip.trip_id = "TEST_TRIP_1"
        entity.trip_update.trip.route_id = "TEST_ROUTE"
        
        # Add another trip update entity
        entity2 = feed.entity.add()
        entity2.id = "trip_2"
        entity2.trip_update.trip.trip_id = "TEST_TRIP_2"
        
        # Extract trip updates
        trip_updates = self.client.get_trip_updates(feed)
        
        # Verify
        self.assertEqual(len(trip_updates), 2)
        self.assertEqual(trip_updates[0].trip.trip_id, "TEST_TRIP_1")
        self.assertEqual(trip_updates[1].trip.trip_id, "TEST_TRIP_2")
    
    def test_get_vehicle_positions(self):
        """Test extracting vehicle positions from feed"""
        # Create a mock feed with vehicle positions
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        
        # Add a vehicle position entity
        entity = feed.entity.add()
        entity.id = "vehicle_1"
        entity.vehicle.trip.trip_id = "TEST_TRIP_1"
        entity.vehicle.vehicle.id = "TEST_VEHICLE_1"
        
        # Extract vehicle positions
        vehicle_positions = self.client.get_vehicle_positions(feed)
        
        # Verify
        self.assertEqual(len(vehicle_positions), 1)
        self.assertEqual(vehicle_positions[0].vehicle.id, "TEST_VEHICLE_1")
    
    def test_get_service_alerts(self):
        """Test extracting service alerts from feed"""
        # Create a mock feed with alerts
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        
        # Add an alert entity
        entity = feed.entity.add()
        entity.id = "alert_1"
        translation = entity.alert.header_text.translation.add()
        translation.text = "Test alert"
        
        # Extract alerts
        alerts = self.client.get_service_alerts(feed)
        
        # Verify
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].header_text.translation[0].text, "Test alert")
    
    def test_get_mixed_entities(self):
        """Test extracting from feed with mixed entity types"""
        # Create a mock feed with mixed entities
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        
        # Add a trip update
        entity1 = feed.entity.add()
        entity1.id = "trip_1"
        entity1.trip_update.trip.trip_id = "TEST_TRIP"
        
        # Add a vehicle position
        entity2 = feed.entity.add()
        entity2.id = "vehicle_1"
        entity2.vehicle.vehicle.id = "TEST_VEHICLE"
        
        # Add an alert
        entity3 = feed.entity.add()
        entity3.id = "alert_1"
        translation = entity3.alert.header_text.translation.add()
        translation.text = "Test alert"
        
        # Extract each type
        trip_updates = self.client.get_trip_updates(feed)
        vehicle_positions = self.client.get_vehicle_positions(feed)
        alerts = self.client.get_service_alerts(feed)
        
        # Verify
        self.assertEqual(len(trip_updates), 1)
        self.assertEqual(len(vehicle_positions), 1)
        self.assertEqual(len(alerts), 1)


if __name__ == '__main__':
    unittest.main()
