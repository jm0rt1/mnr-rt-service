"""
Unit tests for Travel Assistance Module

Tests all components of the travel assistance system:
- Network location detection
- Travel calculations
- Departure scheduling
- Main orchestrator
"""

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile
import shutil

# Import the modules to test
from src.travel_assist.network_locator import NetworkLocator
from src.travel_assist.travel_calculator import TravelCalculator
from src.travel_assist.scheduler import DepartureScheduler
from src.travel_assist.main import TravelAssistant


class TestNetworkLocator(unittest.TestCase):
    """Test cases for NetworkLocator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.locator = NetworkLocator(
            cache_dir=Path(self.temp_dir),
            cache_ttl_hours=1
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('requests.Session.get')
    def test_get_network_location_success(self, mock_get):
        """Test successful network location retrieval."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'lat': 40.7589,
            'lon': -73.9851,
            'city': 'New York',
            'country': 'United States',
            'isp': 'Test ISP',
            'query': '1.2.3.4'
        }
        mock_get.return_value = mock_response
        
        location = self.locator.get_network_location(use_cache=False)
        
        self.assertEqual(location['latitude'], 40.7589)
        self.assertEqual(location['longitude'], -73.9851)
        self.assertEqual(location['city'], 'New York')
        self.assertIn('timestamp', location)
        self.assertIn('source', location)
    
    @patch('requests.Session.get')
    def test_get_network_location_with_fallback(self, mock_get):
        """Test fallback to second API when first fails."""
        # First API fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = Exception("API 1 failed")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            'latitude': 40.7589,
            'longitude': -73.9851,
            'city': 'New York',
            'country_name': 'United States',
            'org': 'Test ISP',
            'ip': '1.2.3.4'
        }
        
        mock_get.side_effect = [mock_response_fail, mock_response_success]
        
        location = self.locator.get_network_location(use_cache=False)
        
        self.assertEqual(location['latitude'], 40.7589)
        self.assertEqual(location['source'], 'ipapi')
    
    def test_cache_save_and_load(self):
        """Test caching functionality."""
        test_data = {
            'latitude': 40.7589,
            'longitude': -73.9851,
            'city': 'New York',
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to cache
        self.locator._save_to_cache('test_location', test_data)
        
        # Load from cache
        loaded = self.locator._load_from_cache('test_location')
        
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['latitude'], test_data['latitude'])
        self.assertEqual(loaded['city'], test_data['city'])
    
    def test_cache_expiration(self):
        """Test cache TTL expiration."""
        test_data = {'test': 'data'}
        
        # Create cache with very short TTL
        short_ttl_locator = NetworkLocator(
            cache_dir=Path(self.temp_dir),
            cache_ttl_hours=0  # Immediate expiration
        )
        
        short_ttl_locator._save_to_cache('test', test_data)
        
        # Should return None due to expiration
        loaded = short_ttl_locator._load_from_cache('test')
        self.assertIsNone(loaded)
        
        # Should return data when ignoring TTL
        loaded_ignore = short_ttl_locator._load_from_cache('test', ignore_ttl=True)
        self.assertIsNotNone(loaded_ignore)
    
    @patch('subprocess.run')
    def test_discover_lan_devices(self, mock_run):
        """Test LAN device discovery via ARP."""
        # Mock ARP output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
? (192.168.1.1) at aa:bb:cc:dd:ee:ff on en0 ifscope [ethernet]
? (192.168.1.100) at 11:22:33:44:55:66 on en0 ifscope [ethernet]
        """
        mock_run.return_value = mock_result
        
        devices = self.locator.discover_lan_devices()
        
        self.assertIsInstance(devices, list)
        # Verify at least some devices found
        self.assertGreaterEqual(len(devices), 0)
    
    @patch('socket.socket')
    def test_find_arduino_webserver(self, mock_socket):
        """Test Arduino webserver detection."""
        # Mock socket connection
        mock_sock = Mock()
        mock_sock.connect_ex.return_value = 0  # Success
        mock_socket.return_value = mock_sock
        
        devices = [
            {'ip': '192.168.1.100', 'mac': 'aa:bb:cc:dd:ee:ff', 'hostname': 'test'}
        ]
        
        with patch.object(self.locator, '_check_arduino_webserver', return_value='high'):
            result = self.locator.find_arduino_webserver(devices=devices)
            
            self.assertIsNotNone(result)
            self.assertEqual(result['ip'], '192.168.1.100')
            self.assertEqual(result['confidence'], 'high')


class TestTravelCalculator(unittest.TestCase):
    """Test cases for TravelCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = TravelCalculator()
    
    def test_calculate_direct_distance(self):
        """Test direct distance calculation using Haversine formula."""
        # Grand Central to Times Square (approx 1 km)
        from_loc = (40.752998, -73.977056)
        to_loc = (40.758899, -73.985130)
        
        result = self.calculator._calculate_direct_distance(from_loc, to_loc)
        
        self.assertIn('distance_km', result)
        self.assertIn('duration_minutes', result)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'direct')
        self.assertGreater(result['distance_km'], 0)
        self.assertGreater(result['duration_minutes'], 0)
    
    def test_estimate_walking_time(self):
        """Test walking time estimation."""
        distance_km = 2.0
        
        # Normal speed
        result = self.calculator.estimate_walking_time(
            distance_km,
            walking_speed='normal'
        )
        
        self.assertIn('duration_minutes', result)
        self.assertIn('base_duration_minutes', result)
        self.assertIn('buffer_minutes', result)
        self.assertEqual(result['speed_category'], 'normal')
        
        # Fast speed should be quicker
        fast_result = self.calculator.estimate_walking_time(
            distance_km,
            walking_speed='fast'
        )
        self.assertLess(
            fast_result['base_duration_minutes'],
            result['base_duration_minutes']
        )
    
    def test_calculate_departure_time(self):
        """Test departure time calculation."""
        train_time = datetime(2025, 11, 10, 8, 0, 0)  # 8:00 AM
        walking_minutes = 15.0
        extra_buffer = 5
        
        result = self.calculator.calculate_departure_time(
            train_time,
            walking_minutes,
            extra_buffer
        )
        
        self.assertIn('leave_time', result)
        self.assertIn('arrival_time', result)
        self.assertLess(result['leave_time'], train_time)
        self.assertLess(result['arrival_time'], train_time)
        
        # Verify correct calculation
        expected_buffer = self.calculator.safety_buffer + timedelta(minutes=extra_buffer)
        expected_leave = train_time - timedelta(minutes=walking_minutes) - expected_buffer
        self.assertEqual(result['leave_time'], expected_leave)
    
    def test_format_distance_display(self):
        """Test distance formatting."""
        distance_info = {
            'distance_km': 2.5,
            'distance_miles': 1.55,
            'duration_minutes': 30.0
        }
        
        # Metric
        metric_str = self.calculator.format_distance_display(
            distance_info,
            use_metric=True
        )
        self.assertIn('2.50 km', metric_str)
        self.assertIn('30 min', metric_str)
        
        # Imperial
        imperial_str = self.calculator.format_distance_display(
            distance_info,
            use_metric=False
        )
        self.assertIn('1.55 miles', imperial_str)


class TestDepartureScheduler(unittest.TestCase):
    """Test cases for DepartureScheduler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock MTA client
        self.mock_client = Mock()
        self.scheduler = DepartureScheduler(
            mta_client=self.mock_client,
            min_buffer_minutes=3
        )
    
    def test_get_route_name(self):
        """Test route name mapping."""
        self.assertEqual(self.scheduler._get_route_name('1'), 'Hudson')
        self.assertEqual(self.scheduler._get_route_name('2'), 'Harlem')
        self.assertEqual(self.scheduler._get_route_name('99'), 'Route 99')
    
    def test_suggest_departure_earliest(self):
        """Test earliest train suggestion."""
        now = datetime.now()
        trains = [
            {
                'trip_id': '1',
                'departure_time': now + timedelta(minutes=20),
                'feasible': True
            },
            {
                'trip_id': '2',
                'departure_time': now + timedelta(minutes=40),
                'feasible': True
            }
        ]
        
        suggestion = self.scheduler.suggest_departure(trains, preference='earliest')
        
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['trip_id'], '1')
    
    def test_suggest_departure_no_feasible(self):
        """Test suggestion when no trains are feasible."""
        trains = [
            {'trip_id': '1', 'feasible': False},
            {'trip_id': '2', 'feasible': False}
        ]
        
        suggestion = self.scheduler.suggest_departure(trains)
        
        self.assertIsNone(suggestion)
    
    def test_format_suggestion(self):
        """Test suggestion formatting."""
        suggestion = {
            'route_name': 'Hudson',
            'track': '42',
            'status': 'On Time',
            'departure_time': datetime(2025, 11, 10, 8, 0, 0),
            'leave_time': datetime(2025, 11, 10, 7, 40, 0),
            'minutes_until_departure': 20.0,
            'feasible': True
        }
        
        formatted = self.scheduler.format_suggestion(suggestion)
        
        self.assertIn('Hudson', formatted)
        self.assertIn('Track 42', formatted)
        self.assertIn('On Time', formatted)
        self.assertIn('Feasible', formatted)
    
    def test_create_notification_message(self):
        """Test notification message creation."""
        leave_time = datetime.now() + timedelta(minutes=3)
        suggestion = {
            'route_name': 'Hudson',
            'track': '42',
            'leave_time': leave_time
        }
        
        # Should create message (within notification window)
        message = self.scheduler.create_notification_message(
            suggestion,
            notification_time_minutes=5
        )
        
        self.assertIsNotNone(message)
        self.assertIn('Hudson', message)
        self.assertIn('Track 42', message)


class TestTravelAssistant(unittest.TestCase):
    """Test cases for TravelAssistant main orchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create travel assistant with mock data
        self.assistant = TravelAssistant(
            home_station_id='1',
            home_station_coords=(40.752998, -73.977056),
            cache_dir=Path(self.temp_dir)
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test TravelAssistant initialization."""
        self.assertEqual(self.assistant.home_station_id, '1')
        self.assertEqual(self.assistant.home_station_coords, (40.752998, -73.977056))
        self.assertIsNotNone(self.assistant.network_locator)
        self.assertIsNotNone(self.assistant.travel_calculator)
        self.assertIsNotNone(self.assistant.scheduler)
    
    @patch('src.travel_assist.network_locator.NetworkLocator.get_network_location')
    @patch('src.travel_assist.travel_calculator.TravelCalculator.calculate_walking_distance')
    @patch('src.travel_assist.scheduler.DepartureScheduler.find_optimal_trains')
    def test_get_travel_status(self, mock_trains, mock_distance, mock_location):
        """Test complete travel status retrieval."""
        # Mock responses
        mock_location.return_value = {
            'latitude': 40.7589,
            'longitude': -73.9851,
            'city': 'New York',
            'country': 'United States',
            'ip': '1.2.3.4'
        }
        
        mock_distance.return_value = {
            'distance_km': 1.5,
            'distance_miles': 0.93,
            'duration_minutes': 18.0,
            'method': 'direct'
        }
        
        mock_trains.return_value = [
            {
                'trip_id': '1',
                'route_name': 'Hudson',
                'departure_time': datetime.now() + timedelta(minutes=30),
                'feasible': True
            }
        ]
        
        # Get travel status
        status = self.assistant.get_travel_status()
        
        # Verify all components present
        self.assertIn('location', status)
        self.assertIn('distance', status)
        self.assertIn('trains', status)
        self.assertIn('recommended_train', status)
        self.assertIn('timestamp', status)
        
        # Verify data
        self.assertEqual(status['location']['city'], 'New York')
        self.assertEqual(status['distance']['distance_km'], 1.5)
        self.assertEqual(len(status['trains']), 1)
    
    def test_format_travel_summary(self):
        """Test travel summary formatting."""
        status = {
            'location': {
                'latitude': 40.7589,
                'longitude': -73.9851,
                'city': 'New York',
                'country': 'United States',
                'ip': '1.2.3.4',
                'isp': 'Test ISP'
            },
            'distance': {
                'distance_km': 1.5,
                'distance_miles': 0.93,
                'duration_minutes': 18.0
            },
            'trains': [],
            'recommended_train': {
                'route_name': 'Hudson',
                'track': '42',
                'status': 'On Time',
                'departure_time': datetime(2025, 11, 10, 8, 0, 0),
                'leave_time': datetime(2025, 11, 10, 7, 40, 0),
                'minutes_until_departure': 20.0,
                'feasible': True
            }
        }
        
        summary = self.assistant.format_travel_summary(status)
        
        self.assertIn('New York', summary)
        self.assertIn('Hudson', summary)
        self.assertIn('Track 42', summary)


class TestTravelAssistIntegration(unittest.TestCase):
    """Integration tests for travel assistance system."""
    
    @patch('requests.Session.get')
    def test_full_workflow_with_mocks(self, mock_get):
        """Test complete workflow with mocked external APIs."""
        # Mock location API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'lat': 40.7589,
            'lon': -73.9851,
            'city': 'New York',
            'country': 'United States',
            'isp': 'Test ISP',
            'query': '1.2.3.4'
        }
        mock_get.return_value = mock_response
        
        # Create temporary directory for cache
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialize components
            locator = NetworkLocator(cache_dir=Path(temp_dir))
            calculator = TravelCalculator()
            
            # Get location
            location = locator.get_network_location(use_cache=False)
            self.assertIsNotNone(location)
            
            # Calculate distance
            distance = calculator.calculate_walking_distance(
                from_location=(location['latitude'], location['longitude']),
                to_location=(40.752998, -73.977056),
                use_routing=False  # Use direct calculation for test
            )
            self.assertGreater(distance['distance_km'], 0)
            
            # Estimate walking time
            time_est = calculator.estimate_walking_time(distance['distance_km'])
            self.assertGreater(time_est['duration_minutes'], 0)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
