"""
Unit tests for the Web Server API
"""

from src.gtfs_realtime import mta_railroad_pb2
from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
from web_server import app, extract_train_info, timestamp_to_datetime
import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


class TestWebServer(unittest.TestCase):
    """Test cases for Web Server API"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True

    def test_index_endpoint(self):
        """Test the index endpoint returns API information"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('service', data)
        self.assertIn('endpoints', data)
        self.assertEqual(data['service'], 'MNR Real-Time Relay')
        self.assertIn('features', data)
        self.assertIn('gpt_5_codex_preview', data['features'])
        self.assertTrue(data['features']['gpt_5_codex_preview']['enabled'])
        self.assertEqual(
            data['features']['gpt_5_codex_preview']['rollout'], 'all_clients')
        self.assertEqual(
            data['features']['gpt_5_codex_preview']['stage'], 'preview')

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)

    def test_timestamp_to_datetime(self):
        """Test timestamp conversion"""
        # Test with valid timestamp
        result = timestamp_to_datetime(1234567890)
        self.assertIsNotNone(result)
        self.assertIn('2009-02-13', result)

        # Test with zero timestamp
        result = timestamp_to_datetime(0)
        self.assertIsNone(result)

        # Test with None
        result = timestamp_to_datetime(None)
        self.assertIsNone(result)

    def test_extract_train_info_basic(self):
        """Test extracting basic train information"""
        trip_update = gtfs_realtime_pb2.TripUpdate()
        trip_update.trip.trip_id = "TEST_TRIP_123"
        trip_update.trip.route_id = "TEST_ROUTE"
        trip_update.vehicle.id = "TEST_VEHICLE_456"

        info = extract_train_info(trip_update)

        self.assertEqual(info['trip_id'], "TEST_TRIP_123")
        self.assertEqual(info['route_id'], "TEST_ROUTE")
        self.assertEqual(info['vehicle_id'], "TEST_VEHICLE_456")
        self.assertEqual(len(info['stops']), 0)

    def test_extract_train_info_with_stops(self):
        """Test extracting train information with stop times"""
        trip_update = gtfs_realtime_pb2.TripUpdate()
        trip_update.trip.trip_id = "TEST_TRIP"

        # Add first stop
        stu1 = trip_update.stop_time_update.add()
        stu1.stop_id = "STOP_1"
        stu1.arrival.time = 1234567890

        # Add MTA extension with track info
        mta_ext = stu1.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
        mta_ext.track = "42"
        mta_ext.trainStatus = "On Time"

        # Add second stop
        stu2 = trip_update.stop_time_update.add()
        stu2.stop_id = "STOP_2"
        stu2.arrival.time = 1234567900

        info = extract_train_info(trip_update)

        self.assertEqual(len(info['stops']), 2)
        self.assertEqual(info['current_stop'], "STOP_1")
        self.assertEqual(info['next_stop'], "STOP_2")
        self.assertEqual(info['track'], "42")
        self.assertEqual(info['status'], "On Time")
        self.assertIsNotNone(info['eta'])

    @patch('web_server.client')
    def test_trains_endpoint_unsupported_city(self, mock_client):
        """Test /trains endpoint with unsupported city"""
        response = self.app.get('/trains?city=chicago')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('supported_cities', data)

    @patch('web_server.client')
    def test_trains_endpoint_success(self, mock_client):
        """Test /trains endpoint with successful response"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890

        # Add a trip update
        entity = mock_feed.entity.add()
        entity.id = "trip_1"
        entity.trip_update.trip.trip_id = "TEST_TRIP"
        entity.trip_update.trip.route_id = "TEST_ROUTE"

        # Add stop
        stu = entity.trip_update.stop_time_update.add()
        stu.stop_id = "STOP_1"
        stu.arrival.time = 1234567890

        # Mock client methods
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_trip_updates.return_value = [entity.trip_update]

        response = self.app.get('/trains?city=mnr&limit=10')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('trains', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['city'], 'mnr')
        self.assertEqual(len(data['trains']), 1)
        self.assertEqual(data['trains'][0]['trip_id'], "TEST_TRIP")
        self.assertIn('features', data)
        self.assertTrue(data['features']['gpt_5_codex_preview']['enabled'])

    @patch('web_server.client')
    def test_trains_endpoint_with_limit(self, mock_client):
        """Test /trains endpoint respects limit parameter"""
        # Create mock feed with multiple trips
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890

        trip_updates = []
        for i in range(30):
            trip_update = gtfs_realtime_pb2.TripUpdate()
            trip_update.trip.trip_id = f"TRIP_{i}"
            trip_updates.append(trip_update)

        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_trip_updates.return_value = trip_updates

        # Test with limit of 5
        response = self.app.get('/trains?limit=5')
        data = json.loads(response.data)
        self.assertEqual(len(data['trains']), 5)
        self.assertTrue(data['features']['gpt_5_codex_preview']['enabled'])

        # Test with default limit (20)
        response = self.app.get('/trains')
        data = json.loads(response.data)
        self.assertEqual(len(data['trains']), 20)
        self.assertTrue(data['features']['gpt_5_codex_preview']['enabled'])

        # Test that limit is capped at 100
        response = self.app.get('/trains?limit=200')
        data = json.loads(response.data)
        # Should return 30 trains (all available), capped by actual data not limit
        self.assertEqual(len(data['trains']), 30)
        self.assertTrue(data['features']['gpt_5_codex_preview']['enabled'])

    @patch('web_server.client')
    @patch('web_server.gtfs_reader')
    def test_trains_endpoint_with_enrichment(self, mock_gtfs_reader, mock_client):
        """Test /trains endpoint with GTFS static data enrichment"""
        # Create mock feed
        mock_feed = gtfs_realtime_pb2.FeedMessage()
        mock_feed.header.timestamp = 1234567890

        # Add a trip update
        entity = mock_feed.entity.add()
        entity.id = "trip_1"
        entity.trip_update.trip.trip_id = "TEST_TRIP"
        entity.trip_update.trip.route_id = "1"

        # Add stop
        stu = entity.trip_update.stop_time_update.add()
        stu.stop_id = "STOP_1"
        stu.arrival.time = 1234567890

        # Mock client methods
        mock_client.fetch_feed.return_value = mock_feed
        mock_client.get_trip_updates.return_value = [entity.trip_update]

        # Mock GTFS reader enrichment
        mock_gtfs_reader.is_loaded.return_value = True
        
        def mock_enrich(train_info):
            enriched = train_info.copy()
            enriched['route_name'] = 'Hudson Line'
            enriched['route_color'] = '0039A6'
            enriched['trip_headsign'] = 'Poughkeepsie'
            enriched['current_stop_name'] = 'Grand Central'
            return enriched
        
        mock_gtfs_reader.enrich_train_info = mock_enrich

        response = self.app.get('/trains?city=mnr&limit=10')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(len(data['trains']), 1)
        
        # Verify enriched data is present
        train = data['trains'][0]
        self.assertEqual(train['route_name'], 'Hudson Line')
        self.assertEqual(train['route_color'], '0039A6')
        self.assertEqual(train['trip_headsign'], 'Poughkeepsie')
        self.assertEqual(train['current_stop_name'], 'Grand Central')


if __name__ == '__main__':
    unittest.main()
