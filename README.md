# MNR Real-Time Service

A simple web server that provides real-time Metro-North Railroad (MNR) train information in easy-to-use JSON format. This service acts as a relay between the MTA's GTFS-RT (General Transit Feed Specification - Real Time) protobuf feed and clients that need simpler data formats.

Perfect for Arduino projects, embedded systems, home automation, or any application that needs simple train data without complex protobuf parsing.

## Features

- **Simple JSON API**: Returns train data in easy-to-parse JSON format instead of binary protobuf
- **Real-time Data**: Fetches live train information from MTA's GTFS-RT feed
- **Enriched Data**: Automatically enriches real-time data with human-readable names, route colors, and destination information from GTFS static schedule data
- **Automatic GTFS Updates**: Downloads and updates static schedule data automatically (max once per day)
- **Easy to Use**: Single GET request to get upcoming trains with ETA and status
- **Home Network Ready**: Designed to run on any device with Python (Raspberry Pi, home server, etc.)
- **Lightweight**: Minimal dependencies, easy to deploy
- **Arduino-Friendly**: Simple text-based JSON format that's easy to parse in C++
- **GUI Management**: Full-featured graphical interface for server control, configuration, and data visualization (see [GUI Documentation](docs/GUI_README.md))

## Quick Start

### Prerequisites

- Python 3.7 or higher
- Internet connection to fetch MTA data

### Installation

1. Clone the repository:
```bash
git clone https://github.com/jm0rt1/mnr-rt-service.git
cd mnr-rt-service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Server

Start the web server:

```bash
python web_server.py
```

The server will start on `http://0.0.0.0:5000` by default and will be accessible from other devices on your home network.

**Or, use the GUI:**

```bash
python gui_app.py
```

The GUI provides a full-featured interface for:
- Server control (start/stop/restart)
- Configuration management
- GTFS data updates
- Log monitoring
- Real-time train data visualization

See [GUI Documentation](docs/GUI_README.md) for detailed information.

#### Command-Line Options

- `--port PORT`: Specify a different port (default: 5000)
- `--host HOST`: Specify a different host (default: 0.0.0.0, listens on all interfaces)
- `--api-key KEY`: Optional MTA API key (if required)
- `--debug`: Run in debug mode with auto-reload
- `--skip-gtfs-update`: Skip automatic GTFS data update check on startup

Example with custom port:
```bash
python web_server.py --port 8080
```

### GTFS Data Management

The service automatically downloads and updates GTFS static schedule data from MTA on startup if the data is older than 24 hours. This ensures you always have the latest schedule information.

#### Manual GTFS Update

You can manually update the GTFS data using the included utility:

```bash
# Check current status
python update_gtfs.py --info

# Update GTFS data (respects rate limiting)
python update_gtfs.py

# Force update (bypass rate limiting)
python update_gtfs.py --force
```

The GTFS data is downloaded from `https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip` and includes:
- Station information
- Routes and trips
- Schedule data (typically updated for the next 7-10 days)
- Transfer information
- Geographic shapes

**Rate Limiting**: To prevent excessive downloads, updates are limited to once per 24 hours by default. The last download timestamp is tracked automatically.

## API Usage

### Get Train Information

**Endpoint:** `GET /trains`

**Parameters:**
- `city` (optional): Filter by city/region. Currently supports `mnr`, `metro-north`, or `metronorth`. Default: `mnr`
- `limit` (optional): Maximum number of trains to return. Default: 20, Max: 100
- `origin_station` (optional): Filter trains passing through this station (use station ID from `/stations` endpoint)
- `destination_station` (optional): Filter trains going to this destination (use station ID from `/stations` endpoint)
- `route` (optional): Filter by route/line ID (use route ID from `/routes` endpoint)
- `time_from` (optional): Filter trains arriving after this time (HH:MM format, e.g., "14:00")
- `time_to` (optional): Filter trains arriving before this time (HH:MM format, e.g., "16:00")

**Example Requests:**
```bash
# Get all trains (up to 20)
curl "http://localhost:5000/trains?city=mnr&limit=20"

# Filter by origin station (e.g., Grand Central)
curl "http://localhost:5000/trains?origin_station=1&limit=10"

# Filter by route (e.g., Hudson Line)
curl "http://localhost:5000/trains?route=1&limit=10"

# Filter by time range
curl "http://localhost:5000/trains?time_from=14:00&time_to=16:00&limit=10"

# Combine filters
curl "http://localhost:5000/trains?origin_station=1&route=1&time_from=14:00&limit=5"
```

**Example Response:**
```json
{
  "timestamp": "2025-10-25T14:30:00",
  "city": "mnr",
  "total_trains": 20,
  "trains": [
    {
      "trip_id": "1234567",
      "route_id": "1",
      "route_name": "Hudson",
      "route_color": "009B3A",
      "trip_headsign": "Poughkeepsie",
      "direction_id": "0",
      "vehicle_id": "MNR_789",
      "current_stop": "1",
      "current_stop_name": "Grand Central",
      "next_stop": "4",
      "next_stop_name": "Harlem-125 St",
      "eta": "2025-10-25T14:45:00",
      "track": "42",
      "status": "On Time",
      "stops": [
        {
          "stop_id": "1",
          "stop_name": "Grand Central",
          "arrival_time": "2025-10-25T14:30:00",
          "departure_time": "2025-10-25T14:32:00",
          "track": "42",
          "status": "On Time"
        },
        {
          "stop_id": "4",
          "stop_name": "Harlem-125 St",
          "arrival_time": "2025-10-25T14:45:00",
          "departure_time": "2025-10-25T14:46:00",
          "track": "42",
          "status": "On Time"
        }
      ]
    }
  ]
}
```

**Response Fields:**
- `timestamp`: When the data was fetched from MTA
- `city`: The transit system (currently only `mnr`)
- `total_trains`: Number of trains in the response
- `trains`: Array of train objects with:
  - `trip_id`: Unique trip identifier
  - `route_id`: Route identifier (e.g., "1", "2", "3")
  - `route_name`: Human-readable route name (e.g., "Hudson", "Harlem", "New Haven") *enriched from GTFS*
  - `route_color`: Route color hex code *enriched from GTFS*
  - `trip_headsign`: Trip destination (e.g., "Poughkeepsie", "New Haven") *enriched from GTFS*
  - `direction_id`: Direction of travel (0 or 1) *enriched from GTFS*
  - `vehicle_id`: Vehicle identifier
  - `current_stop`: Current or next upcoming stop ID
  - `current_stop_name`: Human-readable stop name *enriched from GTFS*
  - `next_stop`: Stop ID after current stop
  - `next_stop_name`: Human-readable next stop name *enriched from GTFS*
  - `eta`: Estimated time of arrival at current stop (ISO 8601 format)
  - `track`: Track number at current stop
  - `status`: Train status (e.g., "On Time", "Delayed")
  - `stops`: Array of all upcoming stops with times and details (each stop also includes enriched `stop_name`, `stop_lat`, `stop_lon`)

### Get All Stations

**Endpoint:** `GET /stations`

Get a list of all available stations with IDs and names. Use these station IDs for filtering trains.

**Example Request:**
```bash
curl "http://localhost:5000/stations"
```

**Example Response:**
```json
{
  "timestamp": "2025-10-25T14:30:00",
  "total_stations": 114,
  "stations": [
    {
      "stop_id": "1",
      "stop_name": "Grand Central Terminal",
      "stop_code": "GCT",
      "stop_lat": "40.752998",
      "stop_lon": "-73.977056",
      "wheelchair_boarding": "1"
    },
    {
      "stop_id": "4",
      "stop_name": "Harlem-125 St",
      "stop_code": "HRL",
      "stop_lat": "40.805157",
      "stop_lon": "-73.939149",
      "wheelchair_boarding": "1"
    }
  ]
}
```

### Get All Routes

**Endpoint:** `GET /routes`

Get a list of all available routes/lines with IDs and colors. Use these route IDs for filtering trains.

**Example Request:**
```bash
curl "http://localhost:5000/routes"
```

**Example Response:**
```json
{
  "timestamp": "2025-10-25T14:30:00",
  "total_routes": 6,
  "routes": [
    {
      "route_id": "1",
      "route_long_name": "Hudson",
      "route_short_name": "",
      "route_color": "009B3A",
      "route_text_color": "FFFFFF",
      "route_type": "2"
    },
    {
      "route_id": "2",
      "route_long_name": "Harlem",
      "route_short_name": "",
      "route_color": "0039A6",
      "route_text_color": "FFFFFF",
      "route_type": "2"
    }
  ]
}
```

### Get Specific Train Details

**Endpoint:** `GET /train/<trip_id>`

Get detailed information about a specific train by its trip ID.

**Example Request:**
```bash
curl "http://localhost:5000/train/1234567"
```

**Example Response:**
```json
{
  "timestamp": "2025-10-25T14:30:00",
  "train": {
    "trip_id": "1234567",
    "route_id": "1",
    "route_name": "Hudson",
    "route_color": "009B3A",
    "trip_headsign": "Poughkeepsie",
    "direction_id": "0",
    "vehicle_id": "MNR_789",
    "current_stop": "1",
    "current_stop_name": "Grand Central",
    "next_stop": "4",
    "next_stop_name": "Harlem-125 St",
    "eta": "2025-10-25T14:45:00",
    "track": "42",
    "status": "On Time",
    "stops": [...]
  }
}
```

### Health Check

**Endpoint:** `GET /health`

Check if the service is running and healthy:

```bash
curl "http://localhost:5000/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "MNR Real-Time Relay",
  "timestamp": "2025-10-25T14:30:00"
}
```

### API Information

**Endpoint:** `GET /`

Get API documentation and available endpoints:

```bash
curl "http://localhost:5000/"
```

**Response:**
```json
{
  "service": "MNR Real-Time Relay",
  "description": "Simple JSON API for Metro-North Railroad real-time train data",
  "endpoints": {
    "/": "This information page",
    "/health": "Health check endpoint",
    "/trains": "Get real-time train information with filtering options",
    "/stations": "Get list of all available stations",
    "/routes": "Get list of all available routes/lines",
    "/train/<trip_id>": "Get detailed information about a specific train"
  },
  "usage_examples": {
    "get_trains": "/trains?city=mnr&limit=20",
    "filter_by_station": "/trains?origin_station=1&limit=10",
    "filter_by_route": "/trains?route=1&limit=10",
    "filter_by_time": "/trains?time_from=14:00&time_to=16:00",
    "get_stations": "/stations",
    "get_routes": "/routes",
    "get_train_details": "/train/1234567",
    "health_check": "/health"
  }
}
```

## Use Cases

### Arduino/Embedded Systems
The simple JSON format is easy to parse in C++ using libraries like ArduinoJson. The new filtering capabilities make it perfect for Arduino projects that need to:

- **Select a specific station** to monitor incoming trains
- **Filter by destination** to only show trains going to a specific location
- **Filter by time range** to show trains arriving within a certain window
- **Select specific trains** by trip ID to track their progress

Example Arduino workflow:
1. Call `/stations` to get list of available stations (show on LCD/OLED)
2. Let user select home station and destination
3. Call `/trains?origin_station=<home>&destination_station=<dest>&limit=5`
4. Display matching trains with ETAs
5. Call `/train/<trip_id>` for detailed information on selected train

```cpp
// Arduino example - Get trains for specific station and time range
HTTPClient http;
http.begin("http://your-server:5000/trains?origin_station=1&time_from=14:00&time_to=16:00&limit=5");
int httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON with ArduinoJson and display on LCD/OLED
}

// Arduino example - Get list of stations for user selection
http.begin("http://your-server:5000/stations");
httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse and display station list for user to select
}

// Arduino example - Get details of specific train
http.begin("http://your-server:5000/train/1234567");
httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse and display detailed train information with all stops
}
```

### Home Automation
Display train times on smart home dashboards, trigger notifications when trains are delayed, or integrate with home assistant platforms.

### Mobile Apps
Simple REST API for quick train information without dealing with protobuf parsing.

### Web Dashboards
Show real-time train status on web pages using simple JavaScript fetch calls.

## Development

### Running Tests

Run all tests:
```bash
python -m unittest discover tests/
```

Run specific test file:
```bash
python -m unittest tests.test_web_server
python -m unittest tests.test_mta_gtfs_client
python -m unittest tests.test_gtfs_downloader
```

### Project Structure

```
mnr-rt-service/
├── web_server.py              # Main web server application (Flask-based API)
├── gui_app.py                 # GUI application for server management
├── update_gtfs.py             # GTFS data update utility
├── mnr_gtfs_demo.py           # Demo script showing GTFS-RT usage
├── run.py                     # Legacy entry point
├── src/
│   ├── main.py               # Legacy main module
│   ├── mta_gtfs_client.py    # MTA GTFS-RT API client
│   ├── gtfs_downloader.py    # GTFS static data downloader
│   ├── gui/                  # GUI application package
│   │   ├── controllers/      # GUI controllers (main window logic)
│   │   ├── views/            # GUI views
│   │   │   └── generated/    # Auto-generated UI files
│   │   └── models/           # GUI models
│   ├── gtfs_realtime/        # GTFS-RT protobuf definitions
│   │   ├── mta_railroad_pb2.py
│   │   └── com/google/transit/realtime/
│   │       └── gtfs_realtime_pb2.py
│   └── shared/
│       └── settings.py       # Application settings
├── resources/                # GUI resource files
│   └── main_window.ui       # Qt Designer UI file
├── tests/                    # Unit tests
│   ├── test_web_server.py
│   ├── test_mta_gtfs_client.py
│   ├── test_gtfs_downloader.py
│   └── test_gtfs_integration.py
├── gtfs/                     # GTFS static data
│   └── metro-north-railroad/
│       └── gtfsmnr/         # Downloaded GTFS files
├── docs/                     # Documentation
│   └── GUI_README.md        # GUI documentation
├── proto/                    # Protobuf definition files
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── QUICKSTART.md            # Quick start guide
```

## Technical Details

### How It Works

1. **Updates Static Data**: On startup, automatically downloads the latest GTFS static schedule data (if needed)
2. **Loads Static Data**: Parses GTFS static files (routes, stops, trips) into an in-memory cache for fast lookups
3. **Fetches Real-Time Data**: The service fetches real-time data from MTA's GTFS-RT feed (binary protobuf format)
4. **Parses Protobuf**: Uses Google's protobuf library to parse the binary data
5. **Extracts Information**: Pulls out train trip updates, stop times, and MTA-specific extensions (track numbers, train status)
6. **Enriches Data**: Looks up human-readable names, colors, and destination information from the static GTFS cache
7. **Converts to JSON**: Transforms the complex protobuf structure into simple, enriched JSON
8. **Serves via REST API**: Provides a Flask-based HTTP server with easy-to-use endpoints

### Technology Stack

- **Python 3.7+**: Core language
- **Flask 3.0+**: Web framework for REST API
- **Protobuf 4.21+**: For parsing GTFS-RT feeds
- **Requests 2.28+**: For HTTP requests to MTA API

### Data Sources

This service uses two data sources from the MTA:

1. **Real-Time Feed** (GTFS-RT):
   - **Endpoint**: `https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/mnr%2Fgtfs-mnr`
   - **Format**: GTFS-RT (protobuf)
   - **Update Frequency**: Real-time (updates every 30 seconds typically)
   - **Contains**: Live train positions, delays, track assignments, and status updates

2. **Static Schedule Data** (GTFS):
   - **Endpoint**: `https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip`
   - **Format**: GTFS ZIP file (CSV files)
   - **Update Frequency**: Updated frequently to include service changes for the next 7-10 days
   - **Contains**: Station information, routes, scheduled trips, and shapes
   - **Auto-Update**: Downloaded automatically by the service (max once per 24 hours)

The GTFS and GTFS-RT specifications are open standards developed by Google for public transit data.

## Deployment

### Running as a Service (Linux/systemd)

Create a systemd service file `/etc/systemd/system/mnr-rt-service.service`:

```ini
[Unit]
Description=MNR Real-Time Service
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/path/to/mnr-rt-service
ExecStart=/usr/bin/python3 /path/to/mnr-rt-service/web_server.py --port 5000
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable mnr-rt-service
sudo systemctl start mnr-rt-service
```

### Running on Raspberry Pi

This service is perfect for Raspberry Pi home servers:

1. Install Python and dependencies
2. Clone the repository
3. Run the server on boot (use systemd or rc.local)
4. Access from any device on your home network

### Docker (Optional)

You can also containerize this service:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "web_server.py", "--host", "0.0.0.0"]
```

## Troubleshooting

### Connection Refused
Make sure the server is running and you're using the correct host/port. If accessing from another device, use the server's IP address instead of `localhost`.

### No Data Returned
Check your internet connection. The service needs to reach `api-endpoint.mta.info` to fetch real-time data.

### MTA API Key
Some MTA APIs require an API key. If you get authentication errors, sign up for a free API key at the MTA developer portal and use `--api-key YOUR_KEY`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

See LICENSE file for details.

## Acknowledgments

- MTA for providing the real-time GTFS-RT feed
- Google for the GTFS-RT specification
- The open-source community for the excellent Python libraries

## Related Projects

- **GTFS-RT Specification**: https://gtfs.org/realtime/
- **MTA Developer Portal**: https://new.mta.info/developers
- **ArduinoJson**: https://arduinojson.org/ (for parsing JSON on Arduino)
