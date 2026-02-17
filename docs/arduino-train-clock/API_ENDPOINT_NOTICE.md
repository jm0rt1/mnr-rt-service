# Arduino Integration - API Endpoint Notice

## ⚠️ Important Update: API Endpoint Change

**Date:** February 17, 2026  
**Affects:** All Arduino example code in this directory

### Summary

The Arduino examples in this directory were created before the main MNR Real-Time Service API was finalized. As a result, they reference `/api/trains` endpoints, but the **actual production API uses `/trains`** (without the `/api` prefix).

### What You Need to Know

#### Production API (Main Repository)
The web server in the root of this repository (`web_server.py`) uses these endpoints:

```
✅ CORRECT ENDPOINTS:
GET /trains           - Get train information
GET /stations         - Get all stations
GET /routes           - Get all routes
GET /vehicle-positions - Get vehicle locations
GET /alerts           - Get service alerts
```

#### Mock/Example Servers (This Directory)
The mock servers in this directory (`mock_train_server.py`, `example_web_server.py`) use:

```
📝 EXAMPLE ONLY:
GET /api/trains       - Mock endpoint (for testing)
```

### How to Use

#### Option 1: Use the Real Production API (Recommended)

1. Start the main web server from the repository root:
   ```bash
   cd /path/to/mnr-rt-service
   python web_server.py --port 5000
   ```

2. Configure your Arduino with the correct endpoint in `include/config.h`:
   ```cpp
   #define API_ENDPOINT "http://192.168.1.100:5000/trains?limit=5"
   ```
   (Replace `192.168.1.100` with your server's actual IP address)

3. The Arduino code will need minor updates to parse the production API format. See [Migration Guide](#migration-guide) below.

#### Option 2: Use Mock Server for Testing

If you just want to test the Arduino code without setting up the full service:

1. Run the mock server from this directory:
   ```bash
   cd docs/arduino-train-clock
   python mock_train_server.py
   ```

2. Configure your Arduino to use the mock endpoint:
   ```cpp
   #define API_ENDPOINT "http://192.168.1.100:5000/api/trains"
   ```

**Note:** Mock servers are for testing only and do not provide real train data.

### Migration Guide

#### API Response Format Differences

**Mock Server Response:**
```json
{
  "trains": [
    {
      "trip_id": "12345",
      "route": "Hudson Line",
      "destination": "Grand Central",
      "track": "5",
      "arrival_time": "12:45:00",
      "status": "On Time"
    }
  ]
}
```

**Production API Response:**
```json
{
  "timestamp": "2026-02-17T12:30:00",
  "city": "mnr",
  "total_trains": 20,
  "trains": [
    {
      "trip_id": "12345",
      "route_id": "1",
      "route_name": "Hudson",
      "route_color": "009B3A",
      "trip_headsign": "Poughkeepsie",
      "current_stop_name": "Grand Central",
      "next_stop_name": "Harlem-125 St",
      "eta": "2026-02-17T12:45:00",
      "track": "42",
      "status": "On Time",
      "delay": 0
    }
  ]
}
```

#### Arduino Code Changes

Update your Arduino parsing code to handle the production format:

**Before (Mock Format):**
```cpp
const char* route = train["route"];
const char* destination = train["destination"];
const char* arrivalTime = train["arrival_time"];
```

**After (Production Format):**
```cpp
const char* routeName = train["route_name"];        // "Hudson"
const char* destination = train["trip_headsign"];    // "Poughkeepsie"
const char* eta = train["eta"];                      // ISO timestamp
int delay = train["delay"];                          // Delay in seconds
```

### Quick Reference

| What You're Doing | Endpoint to Use | Server to Start |
|-------------------|-----------------|-----------------|
| Real train data | `/trains` | `python web_server.py` (from root) |
| Testing Arduino code | `/api/trains` | `python mock_train_server.py` (from this dir) |
| Learning/Examples | Either | Either |

### Files Affected

Files in this directory that reference `/api/trains`:
- `mock_train_server.py` - Mock server with `/api/trains`
- `example_web_server.py` - Example server with `/api/trains`
- `QUICKSTART.md` - Quick start guide
- `TROUBLESHOOTING.md` - Troubleshooting steps
- `include/config.example.h` - Configuration example
- `ARCHITECTURE.md` - Architecture diagrams

**Action Required:** When using these examples, remember to adjust endpoints based on whether you're using mock or production servers.

### Future Plans

We plan to:
1. Update all Arduino example code to work with both formats
2. Create an Arduino library that abstracts the API differences
3. Add automatic endpoint detection
4. Provide backward compatibility layer

### Questions?

- Check the main [README.md](../../README.md) for production API documentation
- See [docs/API_ENHANCEMENTS.md](../API_ENHANCEMENTS.md) for API details
- Review production endpoints at `http://your-server:5000/` (API info page)

---

**Last Updated:** February 17, 2026  
**Status:** Documentation in progress
