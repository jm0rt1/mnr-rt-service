# Quick Start Guide - MTA GTFS-RT API

## Installation

```bash
# Initialize virtual environment
./init-venv.sh
source ./venv/bin/activate

# Or manually
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Running the Demo

```bash
# Basic usage (no API key required)
python mnr_gtfs_demo.py

# With custom display limits
python mnr_gtfs_demo.py --max-trips 10 --max-vehicles 5 --max-alerts 3

# With API key (if required by MTA in the future)
python mnr_gtfs_demo.py --api-key YOUR_API_KEY
```

## Using in Your Code

```python
from src.mta_gtfs_client import MTAGTFSRealtimeClient
from src.gtfs_realtime import mta_railroad_pb2

# Initialize client
client = MTAGTFSRealtimeClient()

# Fetch the feed
feed = client.fetch_feed()

# Get trip updates
trip_updates = client.get_trip_updates(feed)

# Access MTA Railroad extensions
for trip_update in trip_updates:
    for stop in trip_update.stop_time_update:
        if stop.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update):
            ext = stop.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
            print(f"Track: {ext.track}, Status: {ext.trainStatus}")

# Get vehicle positions
vehicles = client.get_vehicle_positions(feed)

# Access carriage details
for vehicle in vehicles:
    for carriage in vehicle.multi_carriage_details:
        if carriage.HasExtension(mta_railroad_pb2.mta_railroad_carriage_details):
            ext = carriage.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
            print(f"Bikes: {ext.bicycles_allowed}")
            print(f"Quiet Car: {ext.quiet_carriage}")
            print(f"Toilets: {ext.toilet_facilities}")

# Get service alerts
alerts = client.get_service_alerts(feed)
for alert in alerts:
    if alert.header_text.translation:
        print(alert.header_text.translation[0].text)
```

## Running Tests

```bash
# Run all tests
./test.sh

# Or manually
python -m unittest discover -s tests -p 'test*.py'

# Run specific test
python -m unittest tests.test_mta_gtfs_client
python -m unittest tests.test_gtfs_integration
```

## MTA Railroad Extensions

### Stop Time Updates
- `track` - Platform/track number (string)
- `trainStatus` - Current train status (string)

### Carriage Details
- `bicycles_allowed` - Number of bikes permitted (0=no, -1=unlimited)
- `carriage_class` - Carriage type description (string)
- `quiet_carriage` - Quiet car status (QUIET_CARRIAGE, NOT_QUIET_CARRIAGE, UNKNOWN_QUIET_CARRIAGE)
- `toilet_facilities` - Toilet availability (TOILET_ONBOARD, NO_TOILET_ONBOARD, UNKNOWN_TOILET_FACILITIES)

## API Endpoint

```
https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr
```

## Regenerating Protobuf Code (if needed)

```bash
# Install protoc if not already installed
sudo apt-get install protobuf-compiler

# Regenerate Python code
mkdir -p src/gtfs_realtime
protoc --proto_path=proto --python_out=src/gtfs_realtime \
    proto/com/google/transit/realtime/gtfs-realtime.proto
protoc --proto_path=proto --python_out=src/gtfs_realtime \
    proto/mta_railroad.proto

# Fix import in mta_railroad_pb2.py (line 14)
# Change: from com.google.transit.realtime import gtfs_realtime_pb2
# To: from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
```

## File Structure

```
mnr-rt-service/
├── proto/                      # Protobuf definitions
│   ├── com/google/transit/realtime/gtfs-realtime.proto
│   └── mta_railroad.proto
├── src/
│   ├── gtfs_realtime/         # Generated protobuf code
│   └── mta_gtfs_client.py     # API client
├── tests/
│   ├── test_mta_gtfs_client.py
│   └── test_gtfs_integration.py
├── mnr_gtfs_demo.py           # Demo program
├── requirements.txt
├── README_GTFS.md            # Full documentation
└── IMPLEMENTATION_SUMMARY.md  # Implementation details
```

## For More Information

See `README_GTFS.md` for complete documentation including:
- Detailed API reference
- Advanced usage examples
- Extension field descriptions
- Troubleshooting guide
