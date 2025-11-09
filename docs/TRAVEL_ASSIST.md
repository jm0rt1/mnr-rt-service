# Travel Assistance Module Documentation

## Overview

The Travel Assistance Module is a production-grade Python system that provides intelligent travel assistance by combining network location detection, walking distance calculations, and real-time train schedule optimization.

## Features

### 🌍 Network Location Detection
- **Multi-API Geolocation**: Uses multiple fallback APIs (ip-api, ipapi, ipinfo) for robust location detection
- **Offline Caching**: Stores location data locally for resilience
- **LAN Device Discovery**: Identifies devices on your local network
- **Arduino Detection**: Automatically finds Arduino webservers on the network

### 🚶 Walking Distance & Time Calculation
- **Routing API Integration**: Uses OpenRouteService for accurate pedestrian routing
- **Direct Distance Fallback**: Haversine formula when routing API unavailable
- **Configurable Walking Speed**: Supports slow, normal, and fast walking speeds
- **Safety Buffer**: Automatically adds buffer time to estimates

### 🚂 Departure Time Optimization
- **Real-Time Train Data**: Integrates with MTA GTFS real-time feeds
- **Smart Suggestions**: Recommends optimal trains based on walking time
- **Delay Handling**: Accounts for train delays and status updates
- **Multiple Options**: Provides several departure alternatives

### ⚡ Performance
- **Async Operations**: Non-blocking API calls using asyncio and aiohttp
- **Concurrent Queries**: Parallel execution of location, distance, and schedule lookups
- **Smart Caching**: Reduces API calls and improves response times

## Architecture

### Module Structure

```
src/travel_assist/
├── __init__.py              # Package exports
├── network_locator.py       # Network location detection
├── travel_calculator.py     # Distance/time calculations
├── scheduler.py             # Departure optimization
└── main.py                  # Main orchestrator
```

### Component Responsibilities

#### NetworkLocator
- Detects physical location via IP geolocation
- Discovers devices on local network
- Identifies Arduino webservers
- Manages location caching

#### TravelCalculator
- Calculates walking distances and times
- Integrates with OpenRouteService API
- Provides direct distance fallback
- Handles different walking speeds

#### DepartureScheduler
- Fetches real-time train schedules
- Filters trains by station and route
- Calculates optimal departure times
- Handles train delays

#### TravelAssistant
- Orchestrates all components
- Provides simple unified API
- Supports sync and async operations
- Formats results for display

## Installation

### Prerequisites
- Python 3.12 or higher
- Network access for API calls
- MTA API access for train data

### Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `aiohttp>=3.8.0` - Async HTTP client
- `PyYAML>=6.0.0` - Configuration parsing
- `requests>=2.28.0` - HTTP requests
- `protobuf>=4.21.0` - GTFS-RT parsing

### Configuration

1. Copy the example configuration:
```bash
cp config/travel_assist.example.yml config/travel_assist.yml
```

2. Edit `config/travel_assist.yml` with your settings:

```yaml
home_station:
  station_id: "1"  # Your home station ID
  latitude: 40.752998
  longitude: -73.977056
  name: "Grand Central Terminal"

api_keys:
  mta_api_key: null  # Optional
  ors_api_key: null  # Optional for routing
```

## Usage

### Command Line Usage

#### Get Current Location
```bash
curl http://localhost:5000/travel/location
```

Response:
```json
{
  "timestamp": "2025-11-09T19:30:00Z",
  "location": {
    "latitude": 40.7589,
    "longitude": -73.9851,
    "city": "New York",
    "country": "United States",
    "isp": "Optimum Online",
    "ip": "1.2.3.4",
    "source": "ip-api",
    "timestamp": "2025-11-09T19:30:00"
  }
}
```

#### Calculate Walking Distance
```bash
curl http://localhost:5000/travel/distance
```

Response:
```json
{
  "timestamp": "2025-11-09T19:30:00Z",
  "distance": {
    "distance_km": 1.5,
    "distance_miles": 0.93,
    "duration_minutes": 18.0,
    "route_points": [[40.7589, -73.9851], [40.753, -73.977]],
    "method": "routing"
  },
  "formatted": "1.50 km (18 min walk)"
}
```

#### Get Next Optimal Train
```bash
curl "http://localhost:5000/travel/next-train?route=1"
```

Response:
```json
{
  "timestamp": "2025-11-09T19:30:00",
  "location": {...},
  "distance": {...},
  "recommended_train": {
    "trip_id": "1234567",
    "route_id": "1",
    "route_name": "Hudson",
    "departure_time": "2025-11-09T20:00:00",
    "leave_time": "2025-11-09T19:37:00",
    "walking_duration": "0:18:00",
    "buffer_time": "0:05:00",
    "status": "On Time",
    "track": "42",
    "feasible": true,
    "minutes_until_departure": 30.0
  },
  "other_trains": [...],
  "formatted_summary": "📍 Current Location: New York, United States\n..."
}
```

#### Find Arduino Device
```bash
curl http://localhost:5000/travel/arduino-device
```

### Python API Usage

#### Basic Usage

```python
from src.travel_assist import TravelAssistant

# Initialize
assistant = TravelAssistant(
    home_station_id="1",
    home_station_coords=(40.752998, -73.977056)
)

# Get complete travel status
status = assistant.get_travel_status()

print(f"Location: {status['location']['city']}")
print(f"Distance: {status['distance']['distance_km']} km")
print(f"Next train: {status['recommended_train']['route_name']}")
```

#### Async Usage

```python
import asyncio
from src.travel_assist import TravelAssistant

async def main():
    assistant = TravelAssistant(
        home_station_id="1",
        home_station_coords=(40.752998, -73.977056)
    )
    
    # Get status asynchronously
    status = await assistant.get_travel_status_async()
    print(status)

asyncio.run(main())
```

#### Individual Components

```python
from src.travel_assist import NetworkLocator, TravelCalculator, DepartureScheduler

# Network location
locator = NetworkLocator()
location = locator.get_network_location()

# Walking distance
calculator = TravelCalculator()
distance = calculator.calculate_walking_distance(
    from_location=(40.7589, -73.9851),
    to_location=(40.753, -73.977)
)

# Train scheduling
from src.mta_gtfs_client import MTAGTFSRealtimeClient
mta_client = MTAGTFSRealtimeClient()
scheduler = DepartureScheduler(mta_client)

trains = scheduler.find_optimal_trains(
    origin_station_id="1",
    destination_station_id=None,
    walking_duration_minutes=18.0
)
```

## API Endpoints

### GET /travel/location
Get current network location based on public IP.

**Query Parameters:**
- `use_cache` (optional): Use cached data if available (default: true)

**Response:** Location object with coordinates, city, country, ISP

### GET /travel/distance
Calculate walking distance to configured home station.

**Response:** Distance object with km, miles, duration, and route points

### GET /travel/next-train
Get optimal train suggestions based on current location.

**Query Parameters:**
- `destination` (optional): Destination station ID
- `route` (optional): Preferred route ID

**Response:** Complete travel status with location, distance, and train suggestions

### GET /travel/arduino-device
Find Arduino webserver on local network.

**Response:** Arduino device info or not found message

## Configuration Reference

### Home Station
```yaml
home_station:
  station_id: "1"           # Station ID from GTFS data
  latitude: 40.752998       # Station latitude
  longitude: -73.977056     # Station longitude
  name: "Grand Central"     # Human-readable name
```

### API Keys
```yaml
api_keys:
  mta_api_key: null         # MTA API key (optional)
  ors_api_key: null         # OpenRouteService key (optional)
```

Get API keys:
- **MTA**: https://new.mta.info/developers
- **OpenRouteService**: https://openrouteservice.org/dev/#/signup (2000 requests/day free)

### Preferences
```yaml
preferences:
  walking_speed: "normal"              # slow, normal, fast
  safety_buffer_minutes: 2             # Extra time added
  min_station_buffer_minutes: 3        # Time at station before train
  max_train_suggestions: 3             # Number of suggestions
  departure_preference: "earliest"     # earliest or most_time
```

### Cache Settings
```yaml
cache:
  cache_dir: "./cache"                 # Cache directory
  cache_ttl_hours: 24                  # Cache expiration time
  use_cache: true                      # Enable caching
```

### Network Settings
```yaml
network:
  api_timeout: 10                      # API request timeout (seconds)
  device_discovery_timeout: 0.5        # Device scan timeout
  arduino_ports: [80, 8080, 5000]     # Ports to check
```

## Testing

### Run All Tests
```bash
python -m unittest discover tests/
```

### Run Travel Assist Tests Only
```bash
python -m unittest tests.test_travel_assist
```

### Test Coverage

The module includes 19 comprehensive unit tests covering:
- Network location detection with fallback
- Cache save/load and expiration
- LAN device discovery
- Walking distance calculations
- Departure time optimization
- Train suggestions and formatting
- Complete workflow integration

All tests use mocked external APIs to ensure reliability.

## Troubleshooting

### "Travel assistance not configured" Error

**Solution:** Create `config/travel_assist.yml` with required settings:
```bash
cp config/travel_assist.example.yml config/travel_assist.yml
```

### Location Detection Fails

**Possible Causes:**
1. No internet connection
2. All geolocation APIs are down
3. Firewall blocking API access

**Solutions:**
- Check internet connection
- Wait and retry (uses cached data if available)
- Verify no firewall rules blocking http://ip-api.com

### Walking Distance Returns "direct" Method

**Cause:** OpenRouteService API key not configured or API unavailable

**Solution:**
1. Get free API key from https://openrouteservice.org
2. Add to `config/travel_assist.yml`:
```yaml
api_keys:
  ors_api_key: "your-key-here"
```

### No Trains Found

**Possible Causes:**
1. Wrong station ID configured
2. No trains scheduled at current time
3. MTA API issues

**Solutions:**
- Verify station ID using `/stations` endpoint
- Check time of day (may be no trains)
- Check MTA API status

### Arduino Device Not Found

**Expected Behavior:** Arduino detection is optional and may not find anything.

**To Improve Detection:**
1. Ensure Arduino is on same network
2. Ensure Arduino webserver is running
3. Add Arduino port to `arduino_ports` config if using non-standard port

## Performance Optimization

### Use Async Operations
Async methods provide better performance for multiple concurrent operations:

```python
# Faster
status = await assistant.get_travel_status_async()

# Slower
status = assistant.get_travel_status()
```

### Enable Caching
Cache reduces API calls:

```python
# Uses cache if available (faster)
location = locator.get_network_location(use_cache=True)

# Always fetches fresh data (slower)
location = locator.get_network_location(use_cache=False)
```

### Adjust Cache TTL
Longer TTL reduces API calls but may use stale data:

```yaml
cache:
  cache_ttl_hours: 24  # Increase for less frequent updates
```

## Security Considerations

### API Keys
- Store API keys in `config/travel_assist.yml` (not committed to git)
- Never hardcode API keys in source code
- Use environment variables for production deployments

### Network Scanning
- LAN device discovery uses non-intrusive ARP table lookup
- Arduino detection only checks common HTTP ports
- No aggressive port scanning or vulnerability testing

### Data Privacy
- Location data cached locally only
- No data sent to third-party services except geolocation APIs
- Geolocation APIs: ip-api, ipapi, ipinfo (see their privacy policies)

## Future Enhancements

Potential features for future development:

### Weather Integration
- Consider weather conditions in walking time
- Suggest earlier departure in rain/snow
- Weather-based route adjustments

### Historical Analysis
- Track typical travel patterns
- Learn optimal buffer times
- Predict delays based on history

### Push Notifications
- Send alerts when to leave
- Notify of train delays
- Update if missed train

### Multiple Locations
- Support multiple home locations
- Auto-detect which location you're at
- Different home stations per location

### Voice Integration
- Voice commands to get next train
- Voice alerts for departures
- Integration with smart speakers

## Contributing

When contributing to the travel assistance module:

1. Follow PEP 8 coding standards
2. Add type hints to all functions
3. Write comprehensive docstrings
4. Add unit tests for new features
5. Update documentation
6. Ensure all tests pass

## Support

For issues or questions:
1. Check this documentation
2. Review test cases for usage examples
3. Check logs for error details
4. Open an issue on GitHub

## License

See main repository LICENSE file.

## Acknowledgments

- **MTA**: Real-time train data via GTFS-RT
- **OpenRouteService**: Pedestrian routing API
- **ip-api.com**: Free IP geolocation
- **ipapi.co**: IP geolocation API
- **ipinfo.io**: IP geolocation API
