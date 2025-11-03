"""
Unit tests for GTFS Static Reader
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from src.gtfs_static_reader import GTFSStaticReader


class TestGTFSStaticReader(unittest.TestCase):
    """Test cases for GTFS Static Reader"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test GTFS data
        self.test_dir = tempfile.mkdtemp()
        self.gtfs_dir = Path(self.test_dir) / "gtfs"
        self.gtfs_dir.mkdir()
        
        # Create test routes.txt
        routes_content = """route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_url,route_color,route_text_color
1,1,,Hudson,Hudson Line,2,,0039A6,FFFFFF
2,1,,Harlem,Harlem Line,2,,0039A6,FFFFFF
"""
        with open(self.gtfs_dir / "routes.txt", 'w') as f:
            f.write(routes_content)
        
        # Create test stops.txt
        stops_content = """stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station,wheelchair_boarding
1,0NY,Grand Central,,40.752998,-73.977056,,https://new.mta.info/stations/grand-central-terminal,0,,1
4,0HL,Harlem-125 St,,40.805157,-73.939149,,https://new.mta.info/stations/harlem-125-street,0,,1
"""
        with open(self.gtfs_dir / "stops.txt", 'w') as f:
            f.write(stops_content)
        
        # Create test trips.txt
        trips_content = """route_id,service_id,trip_id,trip_headsign,trip_short_name,direction_id,block_id,shape_id,wheelchair_accessible,peak_offpeak
1,1,TRIP_001,Poughkeepsie,4819,0,,12,1,0
1,1,TRIP_002,Grand Central,4860,1,,1,1,0
"""
        with open(self.gtfs_dir / "trips.txt", 'w') as f:
            f.write(trips_content)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.test_dir)
    
    def test_load_gtfs_data(self):
        """Test loading GTFS data"""
        reader = GTFSStaticReader(self.gtfs_dir)
        result = reader.load()
        
        self.assertTrue(result)
        self.assertTrue(reader.is_loaded())
    
    def test_get_route_info(self):
        """Test getting route information"""
        reader = GTFSStaticReader(self.gtfs_dir)
        reader.load()
        
        route_info = reader.get_route_info('1')
        self.assertIsNotNone(route_info)
        self.assertEqual(route_info['route_long_name'], 'Hudson')
        self.assertEqual(route_info['route_color'], '0039A6')
        
        # Test non-existent route
        route_info = reader.get_route_info('999')
        self.assertIsNone(route_info)
    
    def test_get_stop_info(self):
        """Test getting stop information"""
        reader = GTFSStaticReader(self.gtfs_dir)
        reader.load()
        
        stop_info = reader.get_stop_info('1')
        self.assertIsNotNone(stop_info)
        self.assertEqual(stop_info['stop_name'], 'Grand Central')
        self.assertEqual(stop_info['stop_lat'], '40.752998')
        self.assertEqual(stop_info['stop_lon'], '-73.977056')
        
        # Test non-existent stop
        stop_info = reader.get_stop_info('999')
        self.assertIsNone(stop_info)
    
    def test_get_trip_info(self):
        """Test getting trip information"""
        reader = GTFSStaticReader(self.gtfs_dir)
        reader.load()
        
        trip_info = reader.get_trip_info('TRIP_001')
        self.assertIsNotNone(trip_info)
        self.assertEqual(trip_info['trip_headsign'], 'Poughkeepsie')
        self.assertEqual(trip_info['direction_id'], '0')
        
        # Test non-existent trip
        trip_info = reader.get_trip_info('TRIP_999')
        self.assertIsNone(trip_info)
    
    def test_enrich_train_info(self):
        """Test enriching train information"""
        reader = GTFSStaticReader(self.gtfs_dir)
        reader.load()
        
        # Create basic train info
        train_info = {
            'trip_id': 'TRIP_001',
            'route_id': '1',
            'current_stop': '1',
            'next_stop': '4',
            'stops': [
                {'stop_id': '1'},
                {'stop_id': '4'},
            ]
        }
        
        enriched = reader.enrich_train_info(train_info)
        
        # Check route enrichment
        self.assertEqual(enriched['route_name'], 'Hudson')
        self.assertEqual(enriched['route_color'], '0039A6')
        
        # Check trip enrichment
        self.assertEqual(enriched['trip_headsign'], 'Poughkeepsie')
        self.assertEqual(enriched['direction_id'], '0')
        
        # Check stop enrichment
        self.assertEqual(enriched['current_stop_name'], 'Grand Central')
        self.assertEqual(enriched['next_stop_name'], 'Harlem-125 St')
        
        # Check stops list enrichment
        self.assertEqual(enriched['stops'][0]['stop_name'], 'Grand Central')
        self.assertEqual(enriched['stops'][0]['stop_lat'], '40.752998')
        self.assertEqual(enriched['stops'][1]['stop_name'], 'Harlem-125 St')
    
    def test_enrich_train_info_not_loaded(self):
        """Test enrichment when data is not loaded"""
        reader = GTFSStaticReader(self.gtfs_dir)
        # Don't call load()
        
        train_info = {
            'trip_id': 'TRIP_001',
            'route_id': '1',
        }
        
        enriched = reader.enrich_train_info(train_info)
        
        # Should return original info unchanged
        self.assertEqual(enriched, train_info)
        self.assertNotIn('route_name', enriched)
    
    def test_load_missing_files(self):
        """Test loading with missing GTFS files"""
        empty_dir = Path(self.test_dir) / "empty"
        empty_dir.mkdir()
        
        reader = GTFSStaticReader(empty_dir)
        result = reader.load()
        
        # Should still return True but with empty data
        self.assertTrue(result)
        self.assertEqual(len(reader._routes), 0)
        self.assertEqual(len(reader._stops), 0)
        self.assertEqual(len(reader._trips), 0)


if __name__ == '__main__':
    unittest.main()
