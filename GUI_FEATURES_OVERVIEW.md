# MNR Real-Time Service Manager - GUI Features Overview

## GUI Tabs Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  MNR Real-Time Service Manager v1.1.0                           │
├─────────────────────────────────────────────────────────────────┤
│  [Server] [Logs] [Train Data] [Stations] [Routes]              │
│  [Vehicle Positions] [Alerts] [Travel Assistance] [API Info]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [SELECTED TAB CONTENT AREA]                                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Tab Features Matrix

### 1. Server Tab ⚙️
**Purpose**: Control and configure the web server

**Features**:
- Server status display
- Startup phase progress bar
- Control buttons: Start | Stop | Restart
- Configuration:
  - Host (default: 0.0.0.0)
  - Port (default: 5000)
  - API Key (optional, password field)
  - Debug mode checkbox
  - Skip GTFS check option
- GTFS Management:
  - Last download info
  - Update GTFS button (rate-limited)
  - Force Update button

**API Endpoints Used**: `/health` (internal)

---

### 2. Logs Tab 📋
**Purpose**: Monitor server output and errors

**Features**:
- Real-time log display
- Auto-scroll option
- Log level indicators [INFO] [WARNING] [ERROR]
- Control buttons:
  - Clear Logs
  - Save Logs (to file)
- Timestamps on all messages

**API Endpoints Used**: None (local output capture)

---

### 3. Train Data Tab 🚂 ⭐ ENHANCED
**Purpose**: View real-time train information

**Features**:
- 7-column table:
  - Trip ID / Headsign
  - Route
  - Current Stop
  - Next Stop
  - ETA
  - Track
  - Status (color-coded)
- **NEW** Filter Controls:
  - Limit: 1-100 trains (default: 20)
  - Route filter (e.g., "1", "Hudson")
  - Origin station filter (station ID)
  - Destination station filter (station ID)
  - Clear Filters button
- Auto-refresh option (30s interval)
- Status label shows active filters
- Sortable columns
- Enriched data (stop names, route names, headsigns)

**API Endpoint**: `GET /trains`
**Parameters**: limit, route, origin_station, destination_station

---

### 4. Stations Tab 🚉
**Purpose**: View all Metro-North stations

**Features**:
- 6-column table:
  - Stop ID
  - Stop Name
  - Stop Code
  - Latitude
  - Longitude
  - Wheelchair Boarding
- Refresh button
- Status label with timestamp and total count
- Sortable columns
- Alternating row colors

**API Endpoint**: `GET /stations`
**Parameters**: None

---

### 5. Routes Tab 🛤️
**Purpose**: View all Metro-North routes

**Features**:
- 5-column table:
  - Route ID
  - Route Name
  - Short Name
  - Color (with visual preview)
  - Text Color (with visual preview)
- Refresh button
- Status label with timestamp and total count
- Visual color display in cells
- Sortable columns
- Alternating row colors

**API Endpoint**: `GET /routes`
**Parameters**: None

---

### 6. Vehicle Positions Tab 📍 ⭐ NEW
**Purpose**: Track real-time vehicle locations

**Features**:
- 9-column table:
  - Vehicle ID
  - Trip ID
  - Route (enriched with name)
  - Latitude
  - Longitude
  - Bearing
  - Speed
  - Stop ID (enriched with name)
  - Status
- **NEW** Filter Controls:
  - Limit: 1-100 vehicles (default: 20)
  - Route filter
  - Trip ID filter
  - Refresh button
- Status label shows active filters
- Auto-resizing columns
- Enriched data from GTFS

**API Endpoint**: `GET /vehicle-positions`
**Parameters**: limit, route, trip_id

---

### 7. Alerts Tab ⚠️ ⭐ NEW
**Purpose**: Monitor service alerts and disruptions

**Features**:
- 5-column table:
  - Alert ID
  - Header Text
  - Description (with tooltip)
  - Effect (color-coded by severity)
  - Informed Entities (routes/stops affected)
- **NEW** Filter Controls:
  - Route filter
  - Stop filter
  - Refresh button
- **Color Coding**:
  - 🔴 Red: SIGNIFICANT_DELAYS, REDUCED_SERVICE
  - 🟡 Yellow: DETOUR
  - 🔵 Blue: MODIFIED_SERVICE
- Tooltips for long text
- Status label shows active filters
- Enriched entity names

**API Endpoint**: `GET /alerts`
**Parameters**: route, stop

---

### 8. Travel Assistance Tab 🧭 ⭐ ENHANCED
**Purpose**: Travel planning and location-based services

**Features**:
- **NEW** Parameter Controls:
  - Destination station ID
  - Route filter
  - Clear Filters button
  - Refresh All button
- **Configuration Guidance**:
  - Info label explaining travel_assist.yml requirement
  - Link to example configuration
- **Four Information Sections**:
  1. **Network Location**
     - Current IP-based location
     - Cached location data
  2. **Distance to Station**
     - Walking distance
     - Estimated walking time
     - Route information (if ORS configured)
  3. **Next Train Recommendation** ⭐ Uses Parameters
     - Recommended train
     - Other train options
     - Formatted summary
     - Can filter by destination/route
  4. **Arduino Device**
     - Detected device information
     - Device IP and port
     - Confidence level

**API Endpoints**: 
- `GET /travel/location`
- `GET /travel/distance`
- `GET /travel/next-train` (parameters: destination, route)
- `GET /travel/arduino-device`

---

### 9. API Information Tab ℹ️
**Purpose**: View API documentation and metadata

**Features**:
- Formatted JSON display
- Service description
- Complete endpoint list
- Usage examples
- Feature flags
- API version information
- Refresh button
- Status label with timestamp
- Scrollable text area

**API Endpoint**: `GET /`
**Parameters**: None

---

## Parameter Input Summary

| Tab | Parameters Available | Type |
|-----|---------------------|------|
| Train Data | limit, route, origin_station, destination_station | Filters |
| Stations | None | N/A |
| Routes | None | N/A |
| Vehicle Positions | limit, route, trip_id | Filters |
| Alerts | route, stop | Filters |
| Travel Assistance | destination, route | Parameters |
| API Information | None | N/A |

**Total**: 9 parameter inputs across 3 tabs

---

## Error Handling

All tabs include comprehensive error handling:

- 🚫 **Server Not Running**: Clear message, refresh disabled
- ⏱️ **Timeout**: 10-second timeout with appropriate message
- 🔌 **Connection Error**: Detects when server is unreachable
- ❌ **HTTP Errors**: Displays error codes and messages
- ⚙️ **Not Configured** (Travel only): Shows configuration guidance

---

## Color Coding

### Train Data - Status Column
- 🟢 Green: "On Time"
- 🔴 Red: "Delay"

### Alerts - Effect Column
- 🔴 Red: SIGNIFICANT_DELAYS, REDUCED_SERVICE
- 🟡 Yellow: DETOUR
- 🔵 Blue: MODIFIED_SERVICE

### Routes - Color Columns
- Shows actual route colors with colored backgrounds

---

## Keyboard Shortcuts

- **Ctrl+Q** or **Alt+F4**: Exit application
- **Enter** (in filter fields): Auto-trigger refresh (future enhancement)

---

## User Workflow Examples

### Workflow 1: Monitor Specific Route
1. Open GUI
2. Go to Train Data tab
3. Enter route in Route filter (e.g., "Hudson")
4. Click Refresh
5. Enable Auto Refresh for continuous monitoring

### Workflow 2: Check for Service Disruptions
1. Go to Alerts tab
2. Optionally filter by route or stop
3. Click Refresh
4. Review color-coded alerts
5. Hover over descriptions for full details

### Workflow 3: Track Specific Train
1. Go to Vehicle Positions tab
2. Enter Trip ID in filter
3. Click Refresh
4. View real-time location data

### Workflow 4: Plan Next Departure
1. Configure config/travel_assist.yml (one-time)
2. Go to Travel Assistance tab
3. Optionally enter destination station
4. Click Refresh All
5. Review Next Train Recommendation section

---

## System Requirements

**Python**: 3.8+
**Dependencies**:
- PySide6 >= 6.5.0
- requests >= 2.28.0
- Flask >= 3.0.0
- Other dependencies in requirements.txt

**Operating System**: 
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+)

**Display**: GUI requires graphical environment (not headless)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Configure travel assistance
cp config/travel_assist.example.yml config/travel_assist.yml
# Edit travel_assist.yml with your settings

# 3. Run GUI
python3 run_gui.py

# 4. In GUI:
#    - Configure server settings (host, port, API key)
#    - Click "Start" to launch server
#    - Use tabs to explore different endpoints
#    - Apply filters as needed
```

---

## Troubleshooting

**GUI won't start**:
- Check PySide6 is installed: `python3 -c "import PySide6"`
- Check display environment (DISPLAY variable on Linux)

**Server won't start from GUI**:
- Check port is not in use
- Check API key is valid (if provided)
- Review Logs tab for error messages

**No train data appears**:
- Verify server is running (check Server tab status)
- Check internet connection for MTA GTFS-RT feed
- Review Logs tab for API errors

**Travel assistance not working**:
- Create config/travel_assist.yml from example
- Configure home station ID and coordinates
- Provide API keys if using advanced features

---

## Future Enhancement Ideas

- [ ] Auto-refresh for all tabs
- [ ] Export data to CSV
- [ ] Graphical route map visualization
- [ ] Historical data charting
- [ ] Custom alert notifications
- [ ] Favorite station/route quick filters
- [ ] Dark mode theme
- [ ] Multi-language support
- [ ] System tray integration

---

## Version Information

**Current Version**: 1.1.0
**Release Date**: 2025-11-10
**Previous Version**: 1.0.0

**What's New in 1.1.0**:
- ✨ Added Vehicle Positions tab
- ✨ Added Alerts tab
- ✨ Enhanced Train Data tab with filters
- ✨ Enhanced Travel Assistance tab with parameters
- 🐛 Fixed hostLineEdit AttributeError
- 📊 100% API endpoint coverage
- 🎨 Improved UI/UX with color coding
- 📚 Comprehensive documentation

---

## Support & Feedback

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check existing documentation
- Review server logs for errors
- Consult travel_assist.example.yml for configuration

---

**Made with ❤️ for Metro-North Railroad enthusiasts and developers**
