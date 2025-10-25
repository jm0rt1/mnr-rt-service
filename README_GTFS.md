# MTA Metro-North Railroad GTFS-RT API Integration

This Python program provides a client for accessing the MTA Metro-North Railroad GTFS-RT (Real-Time) API, which provides real-time transit information including trip updates, vehicle positions, and service alerts.

## Features

- Fetch real-time GTFS-RT feed from MTA Metro-North Railroad API
- Parse GTFS-RT protobuf data with MTA Railroad extensions
- Support for MTA-specific extensions including:
  - Track and train status information for stop time updates
  - Carriage details (quiet carriage, toilet facilities, bicycle allowance, etc.)
- Extract and display trip updates, vehicle positions, and service alerts
- Comprehensive test suite

## API Endpoint

The program uses the following MTA API endpoint:
```
https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- protobuf compiler (protoc) - for development only

### Setting up the Virtual Environment

1. Clone the repository and navigate to the project directory:
```bash
cd /path/to/mnr-rt-service
```

2. Initialize and activate the virtual environment:
```bash
./init-venv.sh
source ./venv/bin/activate
```

Alternatively, manually:
```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### Dependencies

The following Python packages are required:
- `protobuf>=4.21.0` - For parsing GTFS-RT protobuf data
- `requests>=2.28.0` - For making HTTP requests to the API

## Usage

### Running the Demo Program

The `mnr_gtfs_demo.py` script provides a demonstration of the GTFS-RT API client:

```bash
# Basic usage (without API key)
python mnr_gtfs_demo.py

# With API key (if required by MTA)
python mnr_gtfs_demo.py --api-key YOUR_API_KEY

# Customize number of items displayed
python mnr_gtfs_demo.py --max-trips 10 --max-vehicles 10 --max-alerts 5
```

### Using the Client Library

You can also use the `MTAGTFSRealtimeClient` class in your own Python programs:

```python
from src.mta_gtfs_client import MTAGTFSRealtimeClient

# Initialize the client
client = MTAGTFSRealtimeClient()

# Fetch the real-time feed
feed = client.fetch_feed()

# Get trip updates
trip_updates = client.get_trip_updates(feed)

# Get vehicle positions
vehicle_positions = client.get_vehicle_positions(feed)

# Get service alerts
alerts = client.get_service_alerts(feed)

# Display detailed information
for trip_update in trip_updates:
    client.print_trip_update_details(trip_update)
```

### Accessing MTA Railroad Extensions

The MTA Railroad GTFS-RT feed includes custom extensions for additional information:

#### Stop Time Update Extensions
- `track` - Track information for the stop
- `trainStatus` - Current train status

```python
from src.gtfs_realtime import mta_railroad_pb2

for trip_update in trip_updates:
    for stop_time_update in trip_update.stop_time_update:
        if stop_time_update.HasExtension(mta_railroad_pb2.mta_railroad_stop_time_update):
            mta_ext = stop_time_update.Extensions[mta_railroad_pb2.mta_railroad_stop_time_update]
            print(f"Track: {mta_ext.track}")
            print(f"Train Status: {mta_ext.trainStatus}")
```

#### Carriage Details Extensions
- `bicycles_allowed` - Number of bikes permitted (-1 = no limit, 0 = prohibited)
- `carriage_class` - Description of carriage type/model
- `quiet_carriage` - Whether the carriage is a quiet carriage
- `toilet_facilities` - Whether the carriage has toilet facilities

```python
for vehicle_pos in vehicle_positions:
    for carriage in vehicle_pos.multi_carriage_details:
        if carriage.HasExtension(mta_railroad_pb2.mta_railroad_carriage_details):
            mta_ext = carriage.Extensions[mta_railroad_pb2.mta_railroad_carriage_details]
            print(f"Bicycles Allowed: {mta_ext.bicycles_allowed}")
            print(f"Carriage Class: {mta_ext.carriage_class}")
            print(f"Quiet Carriage: {mta_ext.quiet_carriage}")
            print(f"Toilet Facilities: {mta_ext.toilet_facilities}")
```

## Testing

Run the test suite to verify the installation:

```bash
./test.sh
```

Or manually:
```bash
python -m unittest discover -s tests -p '*test*.py'
```

The test suite includes:
- Client initialization tests
- Feed fetching and parsing tests
- Entity extraction tests (trip updates, vehicle positions, alerts)
- Error handling tests

## Project Structure

```
mnr-rt-service/
├── proto/                          # Protocol buffer definitions
│   ├── com/google/transit/realtime/
│   │   └── gtfs-realtime.proto    # Standard GTFS-RT protobuf
│   └── mta_railroad.proto         # MTA Railroad extensions
├── src/
│   ├── gtfs_realtime/             # Generated protobuf Python code
│   │   ├── com/google/transit/realtime/
│   │   │   └── gtfs_realtime_pb2.py
│   │   └── mta_railroad_pb2.py
│   └── mta_gtfs_client.py         # MTA GTFS-RT API client
├── tests/
│   └── test_mta_gtfs_client.py    # Unit tests
├── mnr_gtfs_demo.py               # Demo program
├── requirements.txt               # Python dependencies
└── README_GTFS.md                 # This file
```

## Protobuf Files

### Standard GTFS-Realtime
The standard GTFS-Realtime protobuf specification is obtained from:
https://github.com/google/transit/blob/master/gtfs-realtime/proto/gtfs-realtime.proto

### MTA Railroad Extensions
The MTA Railroad extension protobuf (`mta_railroad.proto`) extends the standard GTFS-RT specification with:
- `MtaRailroadStopTimeUpdate` - Extends `TripUpdate.StopTimeUpdate`
- `MtaRailroadCarriageDetails` - Extends `VehiclePosition.CarriageDetails`

### Regenerating Protobuf Code

If you modify the protobuf files, regenerate the Python code:

```bash
# Ensure protoc is installed
sudo apt-get install protobuf-compiler

# Regenerate Python code
mkdir -p src/gtfs_realtime
protoc --proto_path=proto --python_out=src/gtfs_realtime proto/com/google/transit/realtime/gtfs-realtime.proto
protoc --proto_path=proto --python_out=src/gtfs_realtime proto/mta_railroad.proto

# Fix import in mta_railroad_pb2.py
# Change: from com.google.transit.realtime import gtfs_realtime_pb2
# To: from src.gtfs_realtime.com.google.transit.realtime import gtfs_realtime_pb2
```

## API Documentation

For more information about the MTA GTFS-RT API and data formats:
- [GTFS Realtime Reference](https://developers.google.com/transit/gtfs-realtime/reference)
- [MTA Developer Resources](https://new.mta.info/developers)

## License

This project follows the same license as the parent repository.

## Contributing

When contributing to this project:
1. Ensure all tests pass before submitting changes
2. Add tests for new functionality
3. Follow the existing code style
4. Update documentation as needed
