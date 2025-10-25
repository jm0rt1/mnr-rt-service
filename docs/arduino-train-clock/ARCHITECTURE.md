# System Architecture

## Overview

This document describes the architecture of the Arduino Train Clock system and how it integrates with the Metro-North Railroad GTFS-RT service.

## System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    MTA GTFS-RT API Service                      │
│         https://api-endpoint.mta.info/Dataservice/...           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ GTFS-RT Feed
                             │ (Protobuf)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Web Server / API Gateway                           │
│                 (Python Flask/FastAPI)                          │
│                                                                 │
│  Components:                                                    │
│  - Fetches GTFS-RT feed from MTA                               │
│  - Parses protobuf data                                        │
│  - Transforms to JSON format                                   │
│  - Serves via HTTP REST API                                    │
│                                                                 │
│  Endpoint: http://your-server:5000/api/trains                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ JSON over HTTP
                             │ (WiFi)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Arduino Nano ESP32                             │
│                                                                 │
│  Components:                                                    │
│  - ESP32 WiFi module                                           │
│  - HTTP Client                                                 │
│  - JSON Parser (ArduinoJson)                                   │
│  - Display Logic                                               │
│                                                                 │
│  Outputs:                                                       │
│  - Serial Monitor (USB)                                        │
│  - [Future] LCD/OLED Display                                   │
│  - [Future] LED Indicators                                     │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. GTFS-RT Feed Acquisition
```
MTA API → Web Server
- Protocol: HTTPS
- Format: GTFS-RT (Protobuf)
- Frequency: Real-time updates
- Content: Trip updates, vehicle positions, service alerts
```

### 2. Data Processing
```
Web Server Processing:
1. Fetch GTFS-RT feed
2. Parse protobuf messages
3. Extract relevant train information:
   - Trip ID
   - Route name
   - Destination
   - Track number
   - Arrival time
   - Status
   - Delays
4. Transform to JSON format
5. Cache (optional)
6. Serve via REST API
```

### 3. Arduino Data Retrieval
```
Arduino → Web Server
- Protocol: HTTP
- Format: JSON
- Frequency: Every 30 seconds (configurable)
- Method: GET request

Request:
GET /api/trains HTTP/1.1
Host: your-server:5000
Accept: application/json

Response:
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
    }
  ]
}
```

### 4. Display Rendering
```
Arduino Processing:
1. Parse JSON response
2. Format data for display
3. Output to serial monitor
4. [Future] Display on LCD/OLED
5. Wait for next update interval
```

## Network Architecture

### Production Setup
```
Internet
   │
   └─── MTA GTFS-RT API (Cloud)
           │
           │ (HTTPS)
           │
   ┌───────▼────────┐
   │  Web Server    │ (Your server, VPS, or local)
   │  - Port 5000   │
   │  - REST API    │
   └───────┬────────┘
           │
           │ (HTTP/WiFi)
           │
   ┌───────▼────────┐
   │ Local Network  │
   │  (2.4GHz WiFi) │
   └───────┬────────┘
           │
   ┌───────▼────────┐
   │  Arduino Nano  │
   │  ESP32         │
   └────────────────┘
```

### Development/Testing Setup
```
┌─────────────────────────────────────┐
│      Developer Computer             │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Mock Server (Python/Flask)  │  │
│  │  Port: 5000                  │  │
│  │  Returns dummy train data    │  │
│  └──────────┬───────────────────┘  │
│             │                       │
│             │ (HTTP/WiFi)           │
└─────────────┼───────────────────────┘
              │
      ┌───────▼────────┐
      │ Arduino Nano   │
      │ ESP32          │
      │ (USB for logs) │
      └────────────────┘
```

## Hardware Specifications

### Arduino Nano ESP32
- **Microcontroller**: ESP32-S3
- **WiFi**: 802.11 b/g/n (2.4GHz)
- **Flash**: 16MB
- **RAM**: 512KB SRAM
- **USB**: USB-C (programming & power)
- **Operating Voltage**: 3.3V
- **GPIO Pins**: 14 digital, 8 analog

### Power Requirements
- **USB Power**: 5V via USB-C
- **Current Draw**: ~80-170mA (WiFi active)
- **Sleep Mode**: <5mA (future optimization)

### Communication
- **WiFi**: WPA2/WPA3 support
- **HTTP Client**: Built-in ESP32 library
- **Serial**: 115200 baud (USB CDC)

## Software Stack

### Arduino Firmware
```
┌─────────────────────────────┐
│   Application Layer         │
│   - main.cpp                │
│   - Display formatting      │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Libraries                 │
│   - ArduinoJson             │
│   - WiFi (ESP32)            │
│   - HTTPClient (ESP32)      │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Arduino Framework         │
│   - ESP32 HAL               │
│   - FreeRTOS                │
└─────────────────────────────┘
```

### Web Server (Assumed/Example)
```
┌─────────────────────────────┐
│   API Layer                 │
│   - Flask/FastAPI routes    │
│   - JSON serialization      │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Business Logic            │
│   - GTFS-RT parser          │
│   - Data transformation     │
│   - Caching (optional)      │
└─────────────┬───────────────┘
              │
┌─────────────▼───────────────┐
│   Data Access               │
│   - MTA API client          │
│   - Protobuf decoder        │
└─────────────────────────────┘
```

## Security Considerations

### WiFi Security
- Use WPA2/WPA3 encryption
- Store credentials securely (not in version control)
- Consider WiFi Manager for easier setup

### API Security
- Use HTTPS for production (not HTTP)
- Consider API key authentication
- Rate limiting on server side

### Data Privacy
- No personal data stored on Arduino
- Public transit data only
- Network traffic is station/train information

## Performance Characteristics

### Update Frequency
- **Default**: 30 seconds
- **Minimum recommended**: 15 seconds (avoid MTA rate limits)
- **Maximum**: 300 seconds (5 minutes)

### Network Latency
- **WiFi connection**: 2-5 seconds
- **HTTP request**: 200-1000ms
- **JSON parsing**: 50-200ms
- **Display update**: <100ms

### Memory Usage
- **Program**: ~200KB flash
- **JSON buffer**: 4-8KB RAM
- **WiFi stack**: ~60KB RAM
- **Free RAM**: ~200KB+

## Extension Points

### Future Hardware Additions
1. **LCD Display (I2C)**
   - 16x2 or 20x4 character display
   - Pins: SDA (GPIO21), SCL (GPIO22)
   
2. **OLED Display (I2C/SPI)**
   - 128x64 or larger
   - Graphics capability
   
3. **RGB LED Status**
   - Green: On time
   - Yellow: Delayed
   - Red: Error
   
4. **Buttons**
   - Cycle through stations
   - Refresh data
   - Configure settings

### Future Software Features
1. **Multi-Station Support**
   - Monitor multiple stations
   - User-configurable list

2. **Web Configuration**
   - WiFi Manager
   - Web UI for settings
   - OTA updates

3. **Alert System**
   - Buzzer for arrival warnings
   - Customizable alerts

4. **Data Logging**
   - SD card storage
   - Historical analysis

## References

- [GTFS-RT Specification](https://gtfs.org/realtime/)
- [MTA Developer Resources](https://new.mta.info/developers)
- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [ArduinoJson Library](https://arduinojson.org/)
- [PlatformIO Documentation](https://docs.platformio.org/)
