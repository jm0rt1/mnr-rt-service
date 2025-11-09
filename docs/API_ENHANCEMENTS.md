# API Enhancements for Arduino Train Information Display

## Overview

This document describes the new API endpoints and filtering capabilities added to support Arduino-based train information displays.

## Problem Statement

The original API provided basic train information but lacked the filtering capabilities needed for Arduino projects. Users needed to:

1. Discover available stations and routes
2. Filter trains by specific stations (origin and destination)
3. Filter trains by time range
4. Get detailed information about specific trains
5. Support interactive user selection on Arduino devices

## Solution

We added four major enhancements to the API:

### 1. New `/stations` Endpoint

**Purpose:** Provides a list of all available stations for user selection and filtering.

**Usage:**
```bash
GET /stations
```

**Response:**
```json
{
  "timestamp": "2025-11-09T18:51:39+00:00",
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
    // ... 112 more stations
  ]
}
```

**Arduino Use Case:**
- Display station list on LCD/OLED for user to scroll through
- Let user select home station using buttons
- Use station ID for subsequent train queries

### 2. New `/routes` Endpoint

**Purpose:** Provides a list of all available routes/lines with colors and names.

**Usage:**
```bash
GET /routes
```

**Response:**
```json
{
  "timestamp": "2025-11-09T18:51:39+00:00",
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
    // ... 4 more routes
  ]
}
```

**Arduino Use Case:**
- Display route colors on RGB LEDs
- Let user filter by specific line
- Use route names in display output

### 3. New `/train/<trip_id>` Endpoint

**Purpose:** Get detailed real-time information about a specific train.

**Usage:**
```bash
GET /train/1234567
```

**Response:**
```json
{
  "timestamp": "2025-11-09T18:51:39+00:00",
  "train": {
    "trip_id": "1234567",
    "route_id": "1",
    "route_name": "Hudson",
    "route_color": "009B3A",
    "trip_headsign": "Poughkeepsie",
    "direction_id": "0",
    "vehicle_id": "MNR_789",
    "current_stop": "1",
    "current_stop_name": "Grand Central Terminal",
    "next_stop": "4",
    "next_stop_name": "Harlem-125 St",
    "eta": "2025-11-09T14:45:00+00:00",
    "track": "42",
    "status": "On Time",
    "stops": [
      {
        "stop_id": "1",
        "stop_name": "Grand Central Terminal",
        "arrival_time": "2025-11-09T14:30:00+00:00",
        "departure_time": "2025-11-09T14:32:00+00:00",
        "track": "42",
        "status": "On Time"
      },
      {
        "stop_id": "4",
        "stop_name": "Harlem-125 St",
        "arrival_time": "2025-11-09T14:45:00+00:00",
        "departure_time": "2025-11-09T14:46:00+00:00",
        "track": "42",
        "status": "On Time"
      }
      // ... more stops
    ]
  }
}
```

**Arduino Use Case:**
- Monitor a specific train's progress in real-time
- Display all upcoming stops
- Show current status and track information
- Calculate time until arrival at user's station

### 4. Enhanced `/trains` Endpoint with Filtering

**Purpose:** Filter trains by multiple criteria for precise train selection.

**New Query Parameters:**
- `origin_station` - Filter trains passing through this station (station ID)
- `destination_station` - Filter trains going to this destination (station ID)
- `route` - Filter by route/line ID
- `time_from` - Filter trains arriving after this time (HH:MM format)
- `time_to` - Filter trains arriving before this time (HH:MM format)

**Usage Examples:**

```bash
# Filter by origin station (e.g., Grand Central)
GET /trains?origin_station=1&limit=10

# Filter by route (e.g., Hudson Line)
GET /trains?route=1&limit=10

# Filter by time range (between 2 PM and 4 PM)
GET /trains?time_from=14:00&time_to=16:00&limit=10

# Combine filters (Hudson Line from Grand Central, 2-4 PM)
GET /trains?origin_station=1&route=1&time_from=14:00&time_to=16:00&limit=5

# Filter by origin and destination
GET /trains?origin_station=1&destination_station=46&limit=10
```

**Response:**
```json
{
  "timestamp": "2025-11-09T18:51:39+00:00",
  "city": "mnr",
  "total_trains": 5,
  "filters_applied": {
    "origin_station": "1",
    "destination_station": null,
    "route": "1",
    "time_from": "14:00",
    "time_to": "16:00"
  },
  "trains": [
    // ... filtered train list
  ]
}
```

**Arduino Use Case:**
- Show only trains relevant to user's commute
- Filter by selected home and destination stations
- Show trains arriving within user's time window
- Reduce data transfer and parsing overhead

## Complete Arduino Workflow Example

Here's how an Arduino project can use all these features together:

### Step 1: Initialization - Fetch Available Options

```cpp
// Fetch stations list
HTTPClient http;
http.begin("http://your-server:5000/stations");
int httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON and store stations in memory
  // Display station list on LCD for user selection
}

// Fetch routes list
http.begin("http://your-server:5000/routes");
httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON and store routes in memory
  // Can use route colors for LED indicators
}
```

### Step 2: User Configuration

```cpp
// User scrolls through stations using buttons
// Select home station (e.g., Grand Central = stop_id "1")
String homeStation = "1";

// User selects destination (e.g., Beacon = stop_id "46")
String destStation = "46";

// User sets time window (e.g., 2 PM to 4 PM)
String timeFrom = "14:00";
String timeTo = "16:00";
```

### Step 3: Query Filtered Trains

```cpp
// Build query URL with filters
String url = "http://your-server:5000/trains?";
url += "origin_station=" + homeStation;
url += "&destination_station=" + destStation;
url += "&time_from=" + timeFrom;
url += "&time_to=" + timeTo;
url += "&limit=5";

http.begin(url);
httpCode = http.GET();
if (httpCode == 200) {
  String payload = http.getString();
  // Parse JSON with ArduinoJson
  // Display matching trains on LCD/OLED:
  //   Train 1: Hudson Line to Poughkeepsie - Track 42 - ETA 14:45 - On Time
  //   Train 2: Hudson Line to Poughkeepsie - Track 41 - ETA 15:15 - On Time
  // etc.
}
```

### Step 4: Monitor Specific Train

```cpp
// User selects train #1 from the list
String selectedTripId = "1234567";

// Continuously query for updates (e.g., every 30 seconds)
while (true) {
  http.begin("http://your-server:5000/train/" + selectedTripId);
  httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    // Parse JSON
    // Display:
    //   Current Stop: Grand Central Terminal
    //   Next Stop: Harlem-125 St (ETA 14:45)
    //   Track: 42
    //   Status: On Time
    //   
    //   Upcoming Stops:
    //   - Harlem-125 St (14:45)
    //   - Yankees-E 153 St (14:52)
    //   - Morris Heights (14:58)
    //   ... etc.
  }
  delay(30000); // Wait 30 seconds before next update
}
```

## Implementation Details

### Filtering Logic

The filtering is implemented using three helper functions:

1. **`_train_passes_through_station(train_info, station_id)`**
   - Checks if train's current_stop, next_stop, or any stop in stops list matches the station
   - Used for `origin_station` parameter

2. **`_train_goes_to_destination(train_info, station_id)`**
   - Checks if the last stop in the train's stops list matches the station
   - Used for `destination_station` parameter

3. **`_train_in_time_range(train_info, time_from, time_to)`**
   - Parses the train's ETA and checks if it falls within the specified time range
   - Handles partial ranges (only time_from or only time_to)
   - Used for `time_from` and `time_to` parameters

All filters can be combined. The filtering happens after fetching the real-time data from MTA, ensuring the most up-to-date information.

### Performance Considerations

- Filtering is done in-memory after fetching from MTA API
- Limit parameter is applied after filtering to ensure you get the requested number of matching trains
- Station and route lists are cached by GTFSStaticReader for fast lookups
- Consider caching responses on Arduino side to reduce API calls

### Error Handling

The API provides helpful error messages:
- 503 if GTFS data is not available (stations/routes endpoints)
- 404 if specific train not found (train details endpoint)
- 400 if invalid parameters provided
- 503 if MTA API is unavailable

## Benefits for Arduino Projects

1. **Discovery** - No need to hardcode station IDs or route IDs
2. **Flexibility** - Users can configure their home station and preferences
3. **Precision** - Filter trains to only show relevant ones
4. **Efficiency** - Reduce data transfer by filtering on server side
5. **Real-time** - Monitor specific trains with detailed stop information
6. **User-friendly** - Progressive workflow from discovery to monitoring

## Testing

All new endpoints and filtering logic have comprehensive test coverage:

- 8 tests for new endpoints (stations, routes, train details)
- 14 tests for filtering logic and helper functions
- Integration tests verify end-to-end functionality
- All 68 tests pass with no security vulnerabilities

## Backward Compatibility

All changes are backward compatible:
- Existing `/trains` endpoint works without any filters
- New parameters are optional
- Response format is extended, not changed
- No breaking changes to existing clients

## Future Enhancements

Potential future improvements:
1. Add `/train/<trip_id>/alerts` endpoint for service alerts
2. Add pagination for stations/routes lists
3. Add search/autocomplete for station names
4. Add geolocation-based station filtering
5. Add WebSocket support for real-time updates
6. Add caching headers for better client-side caching
