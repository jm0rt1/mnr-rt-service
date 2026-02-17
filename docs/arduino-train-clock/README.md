# Metro-North Railroad Train Clock - Arduino Example

This is an example Arduino project that demonstrates how to fetch and display real-time Metro-North Railroad train information using an Arduino Nano ESP32 board. The device connects to a WiFi network and periodically fetches train data from a web service, displaying upcoming trains on the serial monitor.

## Hardware Requirements

- **Arduino Nano ESP32** - ESP32-based development board with WiFi
- USB cable for programming and power
- Computer with USB port

### Optional Hardware (Future Enhancements)
- LCD display (e.g., 16x2 or 20x4 I2C LCD)
- OLED display (e.g., SSD1306)
- LED indicators for train status

## Software Requirements

### Required Tools
1. **PlatformIO** - Recommended IDE for this project
   - Install as VS Code extension: [PlatformIO IDE](https://platformio.org/install/ide?install=vscode)
   - Or use PlatformIO CLI

2. **USB Driver** - For Arduino Nano ESP32
   - Usually auto-detected on modern systems
   - If needed: [CP210x USB to UART Bridge Driver](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

### Dependencies
The following libraries are automatically installed by PlatformIO:
- `ArduinoJson` (v6.21.3+) - JSON parsing
- `WiFi` - WiFi connectivity (built-in for ESP32)
- `HTTPClient` - HTTP requests (built-in for ESP32)

## Setup Instructions

### 1. Clone or Download This Project

If you're viewing this in the `mnr-rt-service` repository:
```bash
cd docs/arduino-train-clock
```

### 2. Configure WiFi and API Settings

1. Copy the configuration template:
   ```bash
   cp include/config.example.h include/config.h
   ```

2. Edit `include/config.h` with your settings:
   ```cpp
   #define WIFI_SSID "YourWiFiNetwork"
   #define WIFI_PASSWORD "YourWiFiPassword"
   #define API_ENDPOINT "http://192.168.1.100:5000/trains?limit=5"
   ```
   
   **Note:** The real MNR RT Service API uses `/trains` (not `/api/trains`). 
   Use `?limit=5` to get just the next 5 trains.

3. **Important**: The `config.h` file is ignored by git to protect your credentials.

### 3. Setup the Web Service

This Arduino example expects a web service that provides train data in JSON format. You have two options:

#### Option A: Use a Local Mock Server (For Testing)

Create a simple Flask server for testing:

```python
# mock_train_server.py
from flask import Flask, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/trains')  # Note: Real API uses /trains not /api/trains
def get_trains():
    # Mock data matching the real MNR RT Service API format
    now = datetime.now()
    response = {
        "timestamp": now.isoformat(),
        "city": "mnr",
        "total_trains": 2,
        "trains": [
            {
                "trip_id": "1234567",
                "route_id": "1",
                "route_name": "Hudson",
                "trip_headsign": "Poughkeepsie",
                "current_stop_name": "Yonkers",
                "next_stop_name": "Ludlow",
                "track": "5",
                "eta": (now + timedelta(minutes=5)).isoformat(),
                "status": "On Time",
                "delay": 0
            },
            {
                "trip_id": "1234568",
                "route_id": "2",
                "route_name": "Harlem",
                "trip_headsign": "Wassaic",
                "current_stop_name": "125th Street",
                "next_stop_name": "Fordham",
                "track": "7",
                "eta": (now + timedelta(minutes=12)).isoformat(),
                "status": "Delayed",
                "delay": 180
            }
        ]
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

Run it:
```bash
pip install flask
python mock_train_server.py
```

#### Option B: Use Real MNR GTFS-RT Service (Recommended)

Use the actual MNR Real-Time Service from this repository:

1. Start the web server (from repository root):
   ```bash
   python web_server.py --port 5000
   ```

2. Configure your Arduino to use the real endpoint in `include/config.h`:
   ```cpp
   #define API_ENDPOINT "http://192.168.1.100:5000/trains?limit=5"
   ```
   Replace `192.168.1.100` with your server's IP address.

3. The real service returns enriched data from MTA GTFS-RT feeds in this format:
   ```json
   {
     "timestamp": "2026-02-17T12:30:00",
     "city": "mnr",
     "total_trains": 5,
     "trains": [
       {
         "trip_id": "12345",
         "route_name": "Hudson",
         "trip_headsign": "Poughkeepsie",
         "current_stop_name": "Grand Central",
         "next_stop_name": "Harlem-125 St",
         "eta": "2026-02-17T12:45:00",
         "track": "42",
         "status": "On Time"
       }
     ]
   }
   ```

### 4. Build and Upload

Using PlatformIO in VS Code:
1. Open the `arduino-train-clock` folder in VS Code
2. PlatformIO should auto-detect the project
3. Click the "Build" button (checkmark icon) in the status bar
4. Connect your Arduino Nano ESP32 via USB
5. Click the "Upload" button (arrow icon) in the status bar

Using PlatformIO CLI:
```bash
# Build the project
pio run

# Upload to board
pio run -t upload

# Open serial monitor
pio device monitor
```

### 5. Monitor Output

Open the serial monitor at 115200 baud to see:
- WiFi connection status
- Train data updates every 30 seconds
- Formatted train information display

## Expected API Response Format

The web service should return JSON in this format:

```json
{
  "trains": [
    {
      "trip_id": "1234567",
      "route": "Hudson Line",
      "destination": "Grand Central Terminal",
      "track": "5",
      "arrival_time": "14:30:00",
      "status": "On Time",
      "delay_seconds": 0
    },
    {
      "trip_id": "1234568",
      "route": "Harlem Line",
      "destination": "White Plains",
      "track": "TBD",
      "arrival_time": "14:45:00",
      "status": "Delayed",
      "delay_seconds": 300
    }
  ]
}
```

### Field Descriptions
- `trip_id` - Unique identifier for the trip
- `route` - Train line/route name
- `destination` - Final destination station
- `track` - Platform/track number (or "TBD" if not yet assigned)
- `arrival_time` - Scheduled arrival time (HH:MM:SS format)
- `status` - Current status (e.g., "On Time", "Delayed", "Cancelled")
- `delay_seconds` - Delay in seconds (0 if on time)

## Serial Monitor Output Example

```
=================================
Metro-North Railroad Train Clock
=================================

Connecting to WiFi network: MyHomeNetwork
........
WiFi connected!
IP Address: 192.168.1.150
Signal Strength (RSSI): -45 dBm

--- Fetching Train Data ---
Endpoint: http://192.168.1.100:5000/api/trains
HTTP Response Code: 200

╔═══════════════════════════════════════════════════════════╗
║           METRO-NORTH RAILROAD - UPCOMING TRAINS          ║
╚═══════════════════════════════════════════════════════════╝

┌───────────────────────────────────────────────────────────┐
│ Train #1 - Hudson Line                                    │
├───────────────────────────────────────────────────────────┤
│ → Destination:  Grand Central Terminal                   │
│   Track:        5                                         │
│   Arrival:      14:30:00                                  │
│   Status:       On Time                                   │
└───────────────────────────────────────────────────────────┘

Total trains: 1
Last updated: 45 seconds since boot
```

## Configuration Options

### Modify Update Interval

In `src/main.cpp`, change the update interval (default: 30 seconds):
```cpp
const unsigned long UPDATE_INTERVAL = 30000; // 30 seconds
```

### Add HTTP Authentication

If your API requires authentication, modify the `fetchTrainData()` function:
```cpp
// Add API key header
http.addHeader("X-API-Key", API_KEY);
// Or basic auth
http.setAuthorization("username", "password");
```

## Troubleshooting

### WiFi Connection Issues
- Verify SSID and password in `config.h`
- Check that 2.4GHz WiFi is enabled (ESP32 doesn't support 5GHz)
- Ensure the board is within range of your router

### HTTP Request Failures
- Verify the API endpoint URL is correct
- Check that the web server is running and accessible
- Use `curl` to test the endpoint from your computer
- Ensure Arduino and server are on the same network (or server is publicly accessible)

### JSON Parsing Errors
- Verify the API returns valid JSON
- Check the response format matches expected structure
- Increase ArduinoJson buffer size if needed (in main.cpp)

### Upload Issues
- Select correct USB port in PlatformIO
- Install USB drivers for your operating system
- Try pressing the reset button during upload

## Future Enhancements

Possible improvements for this project:

1. **LCD/OLED Display**
   - Add support for physical displays
   - Show multiple trains at once
   - Rotate through train list

2. **LED Indicators**
   - Green LED: On time trains
   - Yellow LED: Delayed trains
   - Red LED: Connection errors

3. **Web Configuration**
   - WiFi Manager for easy setup
   - Web interface to configure settings
   - OTA (Over-The-Air) firmware updates

4. **Audio Alerts**
   - Buzzer for train arrival warnings
   - Different tones for different statuses

5. **Real-Time Clock**
   - Add RTC module for accurate timekeeping
   - Display countdown to arrival

6. **Multi-Station Support**
   - Configure multiple stations to monitor
   - Switch between stations with buttons

## Project Structure

```
arduino-train-clock/
├── platformio.ini           # PlatformIO configuration
├── src/
│   └── main.cpp            # Main Arduino sketch
├── include/
│   ├── config.example.h    # Configuration template
│   └── config.h            # Your config (git-ignored)
├── lib/                    # Custom libraries (if any)
└── README.md              # This file
```

## Contributing

If you'd like to enhance this example:
1. Test your changes thoroughly
2. Update documentation
3. Submit a pull request to the main repository

## License

This example is part of the `mnr-rt-service` project. See the main repository for license information.

## Related Documentation

- [PlatformIO Documentation](https://docs.platformio.org/)
- [Arduino Nano ESP32 Guide](https://docs.arduino.cc/hardware/nano-esp32)
- [ArduinoJson Documentation](https://arduinojson.org/)
- [ESP32 WiFi Documentation](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/wifi.html)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review PlatformIO and Arduino ESP32 documentation
3. Open an issue in the main repository
