"""
Unit tests for new API endpoints: /stations, /routes, /train/<trip_id>, and enhanced /trains filtering.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from web_server import app, _train_passes_through_station, _train_goes_to_destination, _train_in_time_range
from src.gtfs_static_reader import GTFSStaticReader


class TestNewEndpoints(unittest.TestCase):
    """Test new API endpoints."""

    def setUp(self):
        """Set up test client and mock data."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('web_server.gtfs_reader')
    def test_stations_endpoint_success(self, mock_gtfs_reader):
        """Test /stations endpoint returns list of stations."""
        # Mock GTFS reader
        mock_gtfs_reader.is_loaded.return_value = True
        mock_gtfs_reader.get_all_stops.return_value = [
            {
                'stop_id': '1',
                'stop_name': 'Grand Central Terminal',
                'stop_code': 'GCT',
                'stop_lat': '40.752998',
                'stop_lon': '-73.977056',
                'wheelchair_boarding': '1'
            },
            {
                'stop_id': '4',
                'stop_name': 'Harlem-125 St',
                'stop_code': 'HRL',
                'stop_lat': '40.805157',
                'stop_lon': '-73.939149',
                'wheelchair_boarding': '1'
            }
        ]

        response = self.client.get('/stations')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('stations', data)
        self.assertIn('total_stations', data)
        self.assertEqual(data['total_stations'], 2)
        self.assertEqual(len(data['stations']), 2)
        self.assertEqual(data['stations'][0]['stop_id'], '1')
        self.assertEqual(data['stations'][0]['stop_name'], 'Grand Central Terminal')

    @patch('web_server.gtfs_reader')
    def test_stations_endpoint_not_loaded(self, mock_gtfs_reader):
        """Test /stations endpoint when GTFS data is not loaded."""
        mock_gtfs_reader.is_loaded.return_value = False

        response = self.client.get('/stations')
        self.assertEqual(response.status_code, 503)
        
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('GTFS static data not available', data['error'])

    @patch('web_server.gtfs_reader')
    def test_routes_endpoint_success(self, mock_gtfs_reader):
        """Test /routes endpoint returns list of routes."""
        # Mock GTFS reader
        mock_gtfs_reader.is_loaded.return_value = True
        mock_gtfs_reader.get_all_routes.return_value = [
            {
                'route_id': '1',
                'route_long_name': 'Hudson Line',
                'route_short_name': 'HUD',
                'route_color': '009B3A',
                'route_text_color': 'FFFFFF',
                'route_type': '2'
            },
            {
                'route_id': '2',
                'route_long_name': 'Harlem Line',
                'route_short_name': 'HAR',
                'route_color': '0039A6',
                'route_text_color': 'FFFFFF',
                'route_type': '2'
            }
        ]

        response = self.client.get('/routes')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('routes', data)
        self.assertIn('total_routes', data)
        self.assertEqual(data['total_routes'], 2)
        self.assertEqual(len(data['routes']), 2)
        self.assertEqual(data['routes'][0]['route_id'], '1')
        self.assertEqual(data['routes'][0]['route_long_name'], 'Hudson Line')

    @patch('web_server.gtfs_reader')
    def test_routes_endpoint_not_loaded(self, mock_gtfs_reader):
        """Test /routes endpoint when GTFS data is not loaded."""
        mock_gtfs_reader.is_loaded.return_value = False

        response = self.client.get('/routes')
        self.assertEqual(response.status_code, 503)
        
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('GTFS static data not available', data['error'])

    @patch('web_server.gtfs_reader')
    @patch('web_server.client')
    def test_train_details_endpoint_success(self, mock_client, mock_gtfs_reader):
        """Test /train/<trip_id> endpoint returns train details."""
        from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
        
        # Create mock feed
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.timestamp = 1609459200  # 2021-01-01 00:00:00 UTC
        
        # Create mock trip update
        entity = feed.entity.add()
        entity.id = "1"
        trip_update = entity.trip_update
        trip_update.trip.trip_id = "TEST_TRIP_123"
        trip_update.trip.route_id = "1"
        trip_update.vehicle.id = "MNR_789"
        
        # Add a stop time update
        stu = trip_update.stop_time_update.add()
        stu.stop_id = "1"
        stu.arrival.time = 1609459500
        
        mock_client.fetch_feed.return_value = feed
        mock_client.get_trip_updates.return_value = [trip_update]
        
        mock_gtfs_reader.is_loaded.return_value = True
        mock_gtfs_reader.enrich_train_info.side_effect = lambda x: x

        response = self.client.get('/train/TEST_TRIP_123')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('train', data)
        self.assertEqual(data['train']['trip_id'], 'TEST_TRIP_123')

    @patch('web_server.client')
    def test_train_details_endpoint_not_found(self, mock_client):
        """Test /train/<trip_id> endpoint when train not found."""
        from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
        
        # Create mock feed with no matching trip
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.timestamp = 1609459200
        
        mock_client.fetch_feed.return_value = feed
        mock_client.get_trip_updates.return_value = []

        response = self.client.get('/train/NONEXISTENT_TRIP')
        self.assertEqual(response.status_code, 404)
        
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('not found', data['error'])

    @patch('web_server.gtfs_reader')
    @patch('web_server.client')
    def test_trains_endpoint_with_route_filter(self, mock_client, mock_gtfs_reader):
        """Test /trains endpoint with route filter."""
        from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
        
        # Create mock feed with multiple trains on different routes
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.timestamp = 1609459200
        
        # Train on route 1
        entity1 = feed.entity.add()
        entity1.id = "1"
        trip_update1 = entity1.trip_update
        trip_update1.trip.trip_id = "TRIP_1"
        trip_update1.trip.route_id = "1"
        
        # Train on route 2
        entity2 = feed.entity.add()
        entity2.id = "2"
        trip_update2 = entity2.trip_update
        trip_update2.trip.trip_id = "TRIP_2"
        trip_update2.trip.route_id = "2"
        
        mock_client.fetch_feed.return_value = feed
        mock_client.get_trip_updates.return_value = [trip_update1, trip_update2]
        
        mock_gtfs_reader.is_loaded.return_value = True
        mock_gtfs_reader.enrich_train_info.side_effect = lambda x: x

        response = self.client.get('/trains?route=1&limit=10')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('trains', data)
        # Should only return trains on route 1
        for train in data['trains']:
            self.assertEqual(train['route_id'], '1')

    @patch('web_server.gtfs_reader')
    @patch('web_server.client')
    def test_trains_endpoint_with_station_filter(self, mock_client, mock_gtfs_reader):
        """Test /trains endpoint with origin station filter."""
        from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
        
        # Create mock feed
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.timestamp = 1609459200
        
        # Train passing through station 1
        entity1 = feed.entity.add()
        entity1.id = "1"
        trip_update1 = entity1.trip_update
        trip_update1.trip.trip_id = "TRIP_1"
        trip_update1.trip.route_id = "1"
        stu1 = trip_update1.stop_time_update.add()
        stu1.stop_id = "1"
        
        # Train not passing through station 1
        entity2 = feed.entity.add()
        entity2.id = "2"
        trip_update2 = entity2.trip_update
        trip_update2.trip.trip_id = "TRIP_2"
        trip_update2.trip.route_id = "2"
        stu2 = trip_update2.stop_time_update.add()
        stu2.stop_id = "2"
        
        mock_client.fetch_feed.return_value = feed
        mock_client.get_trip_updates.return_value = [trip_update1, trip_update2]
        
        mock_gtfs_reader.is_loaded.return_value = True
        mock_gtfs_reader.enrich_train_info.side_effect = lambda x: x

        response = self.client.get('/trains?origin_station=1&limit=10')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('trains', data)
        # Should only return trains passing through station 1
        self.assertGreaterEqual(len(data['trains']), 1)
        self.assertEqual(data['trains'][0]['trip_id'], 'TRIP_1')


class TestFilterHelpers(unittest.TestCase):
    """Test helper functions for filtering trains."""

    def test_train_passes_through_station_current_stop(self):
        """Test train passes through station - current stop."""
        train_info = {
            'current_stop': '1',
            'stops': []
        }
        self.assertTrue(_train_passes_through_station(train_info, '1'))
        self.assertFalse(_train_passes_through_station(train_info, '2'))

    def test_train_passes_through_station_next_stop(self):
        """Test train passes through station - next stop."""
        train_info = {
            'next_stop': '2',
            'stops': []
        }
        self.assertTrue(_train_passes_through_station(train_info, '2'))
        self.assertFalse(_train_passes_through_station(train_info, '1'))

    def test_train_passes_through_station_in_stops_list(self):
        """Test train passes through station - in stops list."""
        train_info = {
            'stops': [
                {'stop_id': '1'},
                {'stop_id': '2'},
                {'stop_id': '3'}
            ]
        }
        self.assertTrue(_train_passes_through_station(train_info, '2'))
        self.assertFalse(_train_passes_through_station(train_info, '5'))

    def test_train_goes_to_destination_true(self):
        """Test train goes to destination - true."""
        train_info = {
            'stops': [
                {'stop_id': '1'},
                {'stop_id': '2'},
                {'stop_id': '3'}
            ]
        }
        self.assertTrue(_train_goes_to_destination(train_info, '3'))

    def test_train_goes_to_destination_false(self):
        """Test train goes to destination - false."""
        train_info = {
            'stops': [
                {'stop_id': '1'},
                {'stop_id': '2'},
                {'stop_id': '3'}
            ]
        }
        self.assertFalse(_train_goes_to_destination(train_info, '1'))
        self.assertFalse(_train_goes_to_destination(train_info, '5'))

    def test_train_in_time_range_within(self):
        """Test train in time range - within range."""
        train_info = {
            'eta': '2021-01-01T14:30:00+00:00'
        }
        self.assertTrue(_train_in_time_range(train_info, '14:00', '15:00'))

    def test_train_in_time_range_before(self):
        """Test train in time range - before range."""
        train_info = {
            'eta': '2021-01-01T13:30:00+00:00'
        }
        self.assertFalse(_train_in_time_range(train_info, '14:00', '15:00'))

    def test_train_in_time_range_after(self):
        """Test train in time range - after range."""
        train_info = {
            'eta': '2021-01-01T16:30:00+00:00'
        }
        self.assertFalse(_train_in_time_range(train_info, '14:00', '15:00'))

    def test_train_in_time_range_only_from(self):
        """Test train in time range - only time_from specified."""
        train_info = {
            'eta': '2021-01-01T14:30:00+00:00'
        }
        self.assertTrue(_train_in_time_range(train_info, '14:00', None))
        self.assertFalse(_train_in_time_range(train_info, '15:00', None))

    def test_train_in_time_range_only_to(self):
        """Test train in time range - only time_to specified."""
        train_info = {
            'eta': '2021-01-01T14:30:00+00:00'
        }
        self.assertTrue(_train_in_time_range(train_info, None, '15:00'))
        self.assertFalse(_train_in_time_range(train_info, None, '14:00'))

    def test_train_in_time_range_no_eta(self):
        """Test train in time range - no ETA."""
        train_info = {}
        self.assertFalse(_train_in_time_range(train_info, '14:00', '15:00'))

    def test_train_in_time_range_invalid_time(self):
        """Test train in time range - invalid time format."""
        train_info = {
            'eta': '2021-01-01T14:30:00+00:00'
        }
        # Invalid time format should return False
        self.assertFalse(_train_in_time_range(train_info, 'invalid', '15:00'))


class TestGTFSStaticReaderNewMethods(unittest.TestCase):
    """Test new methods in GTFSStaticReader."""

    def test_get_all_stops(self):
        """Test getting all stops."""
        import tempfile
        import csv
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create stops.txt
            stops_file = Path(tmpdir) / 'stops.txt'
            with open(stops_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'stop_id', 'stop_name', 'stop_code', 'stop_lat', 'stop_lon', 'wheelchair_boarding'
                ])
                writer.writeheader()
                writer.writerow({
                    'stop_id': '1',
                    'stop_name': 'Grand Central Terminal',
                    'stop_code': 'GCT',
                    'stop_lat': '40.752998',
                    'stop_lon': '-73.977056',
                    'wheelchair_boarding': '1'
                })
                writer.writerow({
                    'stop_id': '2',
                    'stop_name': 'Harlem-125 St',
                    'stop_code': 'HRL',
                    'stop_lat': '40.805157',
                    'stop_lon': '-73.939149',
                    'wheelchair_boarding': '1'
                })
            
            # Create empty routes.txt and trips.txt
            (Path(tmpdir) / 'routes.txt').touch()
            (Path(tmpdir) / 'trips.txt').touch()
            
            reader = GTFSStaticReader(tmpdir)
            reader.load()
            
            stops = reader.get_all_stops()
            self.assertEqual(len(stops), 2)
            self.assertEqual(stops[0]['stop_name'], 'Grand Central Terminal')

    def test_get_all_routes(self):
        """Test getting all routes."""
        import tempfile
        import csv
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create routes.txt
            routes_file = Path(tmpdir) / 'routes.txt'
            with open(routes_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'route_id', 'route_long_name', 'route_short_name', 
                    'route_color', 'route_text_color', 'route_type'
                ])
                writer.writeheader()
                writer.writerow({
                    'route_id': '1',
                    'route_long_name': 'Hudson Line',
                    'route_short_name': 'HUD',
                    'route_color': '009B3A',
                    'route_text_color': 'FFFFFF',
                    'route_type': '2'
                })
                writer.writerow({
                    'route_id': '2',
                    'route_long_name': 'Harlem Line',
                    'route_short_name': 'HAR',
                    'route_color': '0039A6',
                    'route_text_color': 'FFFFFF',
                    'route_type': '2'
                })
            
            # Create empty stops.txt and trips.txt
            (Path(tmpdir) / 'stops.txt').touch()
            (Path(tmpdir) / 'trips.txt').touch()
            
            reader = GTFSStaticReader(tmpdir)
            reader.load()
            
            routes = reader.get_all_routes()
            self.assertEqual(len(routes), 2)
            self.assertEqual(routes[0]['route_id'], '1')
            self.assertEqual(routes[0]['route_long_name'], 'Hudson Line')


if __name__ == '__main__':
    unittest.main()
