# GUI Support for All API Endpoints

This document describes the GUI enhancements that allow viewing data from all API endpoints.

## Overview

The MNR Real-Time Service Manager GUI has been enhanced to display data from all available API endpoints, not just the train data. This provides a complete interface for exploring all the features of the MNR Real-Time Service API.

## New Tabs

Four new tabs have been added to the GUI:

### 1. Stations Tab

**Purpose**: View all available Metro-North stations with detailed information.

**Endpoint**: `GET /stations`

**Features**:
- Table display showing all stations
- Columns: Stop ID, Stop Name, Stop Code, Latitude, Longitude, Wheelchair Boarding
- Refresh button to fetch latest station data
- Status label showing last update time and total station count
- Automatic column resizing for optimal viewing

**Usage**:
1. Start the server from the Server Control tab
2. Navigate to the Stations tab
3. Click "Refresh Stations" to load all station data
4. Browse the table to find station information
5. Use this data to identify station IDs for filtering trains

### 2. Routes Tab

**Purpose**: View all available Metro-North routes/lines with visual colors.

**Endpoint**: `GET /routes`

**Features**:
- Table display showing all routes
- Columns: Route ID, Route Name, Short Name, Color, Text Color
- Visual color representation with colored backgrounds
- Refresh button to fetch latest route data
- Status label showing last update time and total route count
- Alternating row colors for better readability

**Usage**:
1. Start the server from the Server Control tab
2. Navigate to the Routes tab
3. Click "Refresh Routes" to load all route data
4. View route colors and identifiers
5. Use route IDs for filtering trains by line

### 3. Travel Assistance Tab

**Purpose**: Access all travel assistance features for intelligent trip planning.

**Endpoints**: 
- `GET /travel/location` - Network location detection
- `GET /travel/distance` - Walking distance to station
- `GET /travel/next-train` - Optimal train recommendation
- `GET /travel/arduino-device` - Arduino device discovery

**Features**:
- Four separate sections for different travel features
- JSON display of all travel data
- Graceful handling when travel assistance is not configured
- Single refresh button to update all travel data
- Status label showing last update time

**Sections**:
1. **Network Location**: Shows current network location detection results
2. **Distance to Station**: Displays calculated walking distance and time
3. **Next Train Recommendation**: Shows optimal train to catch with timing
4. **Arduino Device**: Displays discovered Arduino devices on network

**Usage**:
1. Configure travel assistance (see `config/travel_assist.yml`)
2. Start the server from the Server Control tab
3. Navigate to the Travel Assistance tab
4. Click "Refresh All Travel Data" to load all information
5. View network location, distances, and train recommendations

**Note**: If travel assistance is not configured, the sections will display appropriate messages indicating the feature is not available.

### 4. API Information Tab

**Purpose**: View comprehensive API documentation and metadata.

**Endpoint**: `GET /`

**Features**:
- Full JSON display of API information
- Shows all available endpoints
- Displays usage examples
- Shows enabled feature flags
- Formatted JSON for easy reading
- Refresh button to fetch latest API info
- Status label showing last update time

**Usage**:
1. Start the server from the Server Control tab
2. Navigate to the API Information tab
3. Click "Refresh API Info" to load API metadata
4. Review available endpoints and their descriptions
5. Use this as a reference for API usage

## Error Handling

All new tabs include comprehensive error handling:

### Server Not Running
If the server is not running when you try to refresh data:
- A warning message is logged
- The status label shows "Server is not running"
- No API calls are made

### Connection Errors
If the API is unreachable:
- An error message is logged
- The status label shows "Connection error"
- User-friendly error messages are displayed

### Request Timeouts
If requests take too long:
- A timeout error is logged
- The status label shows "Request timed out"
- The timeout is set to 10 seconds for all endpoints

### Feature Not Configured
For travel assistance endpoints:
- If not configured, displays "Not configured" message
- Shows the error message from the API
- Does not fail the entire refresh operation

## Technical Implementation

### Architecture

The new functionality is implemented entirely in the GUI controller (`src/gui/controllers/main_window_controller.py`) using programmatic tab creation:

1. **`_setup_additional_tabs()`**: Creates all new tabs and their UI elements
2. **`refresh_stations_data()`**: Fetches and displays station data
3. **`refresh_routes_data()`**: Fetches and displays route data
4. **`refresh_travel_data()`**: Fetches and displays all travel data
5. **`refresh_api_info()`**: Fetches and displays API information

### UI Elements

Each tab consists of:
- **Control Layout**: Contains refresh button and status label
- **Display Widget**: Table or text display for the data
- **Error Handling**: Catches and displays errors appropriately

### Data Flow

```
User clicks refresh button
    ↓
Controller checks if server is running
    ↓
Controller makes HTTP request to API endpoint
    ↓
API returns JSON response
    ↓
Controller parses JSON
    ↓
Controller updates UI elements (table/text)
    ↓
Controller updates status label
    ↓
Controller logs action
```

## Testing

### Automated Tests

New tests have been added in `tests/test_gui_endpoints.py`:
- Verify all endpoint methods exist
- Check UI elements are created
- Validate tabs are added correctly
- Confirm correct endpoint URLs are used
- Ensure proper imports

Run tests with:
```bash
python -m unittest tests.test_gui_endpoints -v
```

### GUI Validation

The existing GUI validation script validates the new code:
```bash
python tests/validate_gui.py
```

### Manual Testing

To manually test the new features:

1. Start the GUI:
   ```bash
   python gui_app.py
   ```

2. Start the server from the Server Control tab

3. Test each new tab:
   - Click refresh button
   - Verify data loads correctly
   - Check error handling (stop server and try refresh)
   - Verify status labels update

## Compatibility

- **Python Version**: 3.7+
- **PySide6**: 6.5.0+
- **Flask**: 3.0.0+
- **All existing GUI features**: Fully compatible

## Future Enhancements

Possible improvements for the future:

1. **Auto-refresh**: Add auto-refresh option for stations and routes
2. **Search/Filter**: Add search functionality for stations and routes tables
3. **Export**: Add export buttons to save data to CSV/JSON
4. **Details View**: Add ability to click on a station/route for more details
5. **Travel History**: Track and display travel history
6. **Favorites**: Allow users to mark favorite stations/routes

## Related Documentation

- [GUI README](GUI_README.md) - Main GUI documentation
- [Travel Assistance](TRAVEL_ASSIST.md) - Travel assistance features
- [API Enhancements](API_ENHANCEMENTS.md) - API endpoint details
- Main [README](../README.md) - Project overview
