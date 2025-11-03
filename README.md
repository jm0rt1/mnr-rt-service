# MNR Real-Time Service

A simple web server that provides real-time Metro-North Railroad (MNR) train information in easy-to-use JSON format. This service acts as a relay between the MTA's GTFS-RT (General Transit Feed Specification - Real Time) protobuf feed and clients that need simpler data formats.

Perfect for Arduino projects, embedded systems, home automation, or any application that needs simple train data without complex protobuf parsing.

## Features

- **Simple JSON API**: Returns train data in easy-to-parse JSON format instead of binary protobuf
- **Real-time Data**: Fetches live train information from MTA's GTFS-RT feed
- **Automatic GTFS Updates**: Downloads and updates static schedule data automatically (max once per day)
- **Easy to Use**: Single GET request to get upcoming trains with ETA and status
- **Home Network Ready**: Designed to run on any device with Python (Raspberry Pi, home server, etc.)
- **Lightweight**: Minimal dependencies, easy to deploy
- **Arduino-Friendly**: Simple text-based JSON format that's easy to parse in C++

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

**Example Request:**
```bash
curl "http://localhost:5000/trains?city=mnr&limit=20"
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
      "route_id": "Hudson",
      "vehicle_id": "MNR_789",
      "current_stop": "Grand_Central",
      "next_stop": "125th_Street",
      "eta": "2025-10-25T14:45:00",
      "track": "42",
      "status": "On Time",
      "stops": [
        {
          "stop_id": "Grand_Central",
          "arrival_time": "2025-10-25T14:30:00",
          "departure_time": "2025-10-25T14:32:00",
          "track": "42",
          "status": "On Time"
        },
        {
          "stop_id": "125th_Street",
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
  - `route_id`: Route name (e.g., "Hudson", "Harlem", "New Haven")
  - `vehicle_id`: Vehicle identifier
  - `current_stop`: Current or next upcoming stop ID
  - `next_stop`: Stop after current stop
  - `eta`: Estimated time of arrival at current stop (ISO 8601 format)
  - `track`: Track number at current stop
  - `status`: Train status (e.g., "On Time", "Delayed")
  - `stops`: Array of all upcoming stops with times and details

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
    "/trains": "Get real-time train information (supports ?city=mnr&limit=20)"
  },
  "usage_examples": {
    "get_trains": "/trains?city=mnr&limit=20",
    "health_check": "/health"
  }
}
```

## Use Cases

### Arduino/Embedded Systems
The simple JSON format is easy to parse in C++ using libraries like ArduinoJson:
```cpp
// Arduino example
HTTPClient http;
http.begin("http://your-server:5000/trains?limit=5");
int httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON and display on LCD/OLED
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
├── update_gtfs.py             # GTFS data update utility
├── mnr_gtfs_demo.py           # Demo script showing GTFS-RT usage
├── run.py                     # Legacy entry point
├── src/
│   ├── main.py               # Legacy main module
│   ├── mta_gtfs_client.py    # MTA GTFS-RT API client
│   ├── gtfs_downloader.py    # GTFS static data downloader
│   ├── gtfs_realtime/        # GTFS-RT protobuf definitions
│   │   ├── mta_railroad_pb2.py
│   │   └── com/google/transit/realtime/
│   │       └── gtfs_realtime_pb2.py
│   └── shared/
│       └── settings.py       # Application settings
├── tests/                    # Unit tests
│   ├── test_web_server.py
│   ├── test_mta_gtfs_client.py
│   ├── test_gtfs_downloader.py
│   └── test_gtfs_integration.py
├── gtfs/                     # GTFS static data
│   └── metro-north-railroad/
│       └── gtfsmnr/         # Downloaded GTFS files
├── proto/                    # Protobuf definition files
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── QUICKSTART.md            # Quick start guide
```

## Technical Details

### How It Works

1. **Updates Static Data**: On startup, automatically downloads the latest GTFS static schedule data (if needed)
2. **Fetches Real-Time Data**: The service fetches real-time data from MTA's GTFS-RT feed (binary protobuf format)
3. **Parses Protobuf**: Uses Google's protobuf library to parse the binary data
4. **Extracts Information**: Pulls out train trip updates, stop times, and MTA-specific extensions (track numbers, train status)
5. **Converts to JSON**: Transforms the complex protobuf structure into simple, flat JSON
6. **Serves via REST API**: Provides a Flask-based HTTP server with easy-to-use endpoints

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
