# MNR Real-Time Service Manager GUI

A comprehensive graphical user interface for managing the Metro-North Railroad real-time service.

## Features

### 1. Server Control
- **Start/Stop/Restart** the web server from the GUI
- **Real-time status monitoring** - see if the server is running or stopped
- **Configuration management** - easily configure all server parameters:
  - Host (default: 0.0.0.0)
  - Port (default: 5000)
  - MTA API Key (optional)
  - Debug mode toggle
  - GTFS update on startup toggle

### 2. GTFS Data Management
- **Automatic updates** - downloads GTFS data from the MTA feed
- **Rate limiting** - enforces maximum of 1 download per day
- **Manual update** - update GTFS data on demand
- **Force update** - bypass rate limiting when needed
- **Download status** - shows when data was last downloaded and when next download is allowed

### 3. Real-Time Train Data Visualization
- **Live train data table** showing:
  - Trip ID
  - Route
  - Current Stop
  - Next Stop
  - ETA (formatted for readability)
  - Track number
  - Status (color-coded: green for "On Time", red for delays)
- **Auto-refresh** - automatically update train data every 30 seconds
- **Manual refresh** - refresh data on demand
- **Configurable limit** - control how many trains to display (1-100)

### 4. Logs & Error Display
- **Real-time log monitoring** - see all server output and errors
- **Auto-scroll** - automatically scroll to latest log entries
- **Clear logs** - clear the log display
- **Save logs** - export logs to a text file
- **Timestamped entries** - all log entries include timestamp and severity level

### 5. Stations Viewer
- **View all stations** - browse complete list of Metro-North stations
- **Station details** - see station IDs, names, codes, and coordinates
- **Wheelchair accessibility** - check which stations are accessible
- **Refresh on demand** - update station list at any time

### 6. Routes Viewer
- **View all routes** - see all Metro-North lines and routes
- **Visual colors** - route colors displayed with background
- **Route details** - route IDs, names, and identifiers
- **Refresh on demand** - update route list at any time

### 7. Travel Assistance (if configured)
- **Network location** - see current network location detection
- **Distance calculation** - view walking distance to station
- **Next train recommendation** - get optimal train suggestions
- **Arduino device discovery** - find Arduino devices on network
- **Refresh on demand** - update all travel data at once

### 8. API Information
- **View API metadata** - see all available endpoints
- **Usage examples** - get example API calls
- **Feature flags** - see which features are enabled
- **Documentation** - built-in API reference

For detailed information about viewing all API endpoints in the GUI, see [GUI All Endpoints Documentation](GUI_ALL_ENDPOINTS.md).

## Installation

### Prerequisites

All dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

This includes:
- Flask (web server)
- PySide6 (GUI framework)
- requests (HTTP client)
- protobuf (GTFS-RT data parsing)

### Generating UI Files

The UI is designed using Qt Designer and stored in `resources/main_window.ui`. To regenerate the Python UI file:

```bash
./generate_ui.sh
```

Or manually:

```bash
pyside6-uic ./resources/main_window.ui -o src/gui/views/generated/main_window.py
```

## Usage

### Starting the GUI

Simply run:

```bash
python gui_app.py
```

Or make it executable and run directly:

```bash
chmod +x gui_app.py
./gui_app.py
```

### Using the GUI

#### Server Tab (Server Control)

1. **Configure server settings**:
   - Set the host (default: 0.0.0.0 for all interfaces)
   - Set the port (default: 5000)
   - Optionally add your MTA API key
   - Enable debug mode if needed
   - Toggle GTFS updates on startup

2. **Start the server**:
   - Click "Start Server"
   - Watch the logs tab for server output
   - Server status will change to "Running" (green)

3. **Stop or restart**:
   - Use "Stop Server" to shut down
   - Use "Restart Server" to apply configuration changes

4. **Manage GTFS data**:
   - Click "Update GTFS Data Now" to download latest data (respects 24-hour rate limit)
   - Click "Force Update" to bypass rate limiting
   - View last download time and next allowed download

#### Logs & Errors Tab

- View all server logs in real-time
- Logs include timestamps and severity levels (INFO, WARNING, ERROR)
- Use "Clear Logs" to clear the display
- Use "Save Logs" to export to a file
- Toggle "Auto-scroll" to automatically show latest entries

#### Train Data Visualization Tab

1. **Ensure server is running** (start it from Server Control tab)

2. **Configure data display**:
   - Set train limit (1-100 trains)
   - Click "Refresh Train Data" to fetch current data

3. **Enable auto-refresh** (optional):
   - Check "Auto-refresh (30s)" to automatically update every 30 seconds

4. **View train information**:
   - Table shows all active trains
   - Color coding: Green = On Time, Red = Delayed
   - Click column headers to sort
   - Select rows to view details

## Architecture

### Directory Structure

```
src/gui/
├── __init__.py
├── controllers/
│   ├── __init__.py
│   └── main_window_controller.py    # Main GUI logic
├── views/
│   ├── __init__.py
│   └── generated/
│       ├── __init__.py
│       └── main_window.py            # Generated from .ui file
└── models/
    └── __init__.py

resources/
└── main_window.ui                    # Qt Designer UI file
```

### Key Components

1. **main_window_controller.py**: Contains the `MainWindowController` class that handles all GUI logic:
   - Server process management via `ServerThread`
   - Configuration management
   - GTFS data updates
   - Log display and management
   - Train data fetching and visualization

2. **main_window.ui**: Qt Designer file defining the UI layout (3 tabs, buttons, inputs, table, etc.)

3. **gui_app.py**: Entry point that creates the Qt application and shows the main window

### How It Works

#### Server Control

The GUI runs the web server as a separate process using `subprocess.Popen`. This allows:
- Server to run independently
- Capture stdout/stderr for log display
- Graceful shutdown with terminate/kill
- Server restarts without restarting GUI

#### GTFS Management

Uses the existing `GTFSDownloader` class from `src/gtfs_downloader.py`:
- Downloads from https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip
- Extracts to `gtfs/metro-north-railroad/gtfsmnr/`
- Enforces 24-hour rate limiting
- Tracks download history in `.last_download` file

#### Train Data Visualization

Fetches data from the running web server via HTTP:
- Calls `http://localhost:{port}/trains?limit={limit}`
- Parses JSON response
- Populates QTableWidget with train information
- Color-codes status for easy visualization
- Supports auto-refresh on a timer

## Configuration Options

All configurable server options are exposed in the GUI:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| Host | String | 0.0.0.0 | Host to bind server to |
| Port | Integer | 5000 | Port to run server on |
| MTA API Key | String | None | Optional API key for MTA |
| Debug Mode | Boolean | False | Enable Flask debug mode |
| Skip GTFS Update | Boolean | False | Skip GTFS update on startup |
| Train Limit | Integer | 20 | Number of trains to display |
| Auto-refresh | Boolean | False | Auto-refresh train data every 30s |

## Error Handling

The GUI provides comprehensive error handling:

- **Server errors**: Displayed in logs with ERROR level
- **Connection errors**: Shown when server is not reachable
- **GTFS download errors**: Displayed with error dialogs and logged
- **Rate limit errors**: User-friendly messages with time until next allowed download
- **Unexpected errors**: Caught and logged with full stack traces

## Troubleshooting

### GUI won't start

- Ensure PySide6 is installed: `pip install PySide6`
- Check that you have a display server (X11, Wayland, etc.)
- On headless servers, use Xvfb or similar virtual display

### Server won't start from GUI

- Check logs tab for error messages
- Ensure port is not already in use
- Verify Python and dependencies are available
- Try running `python web_server.py` manually to diagnose

### Train data not refreshing

- Ensure server is running (check status in Server Control tab)
- Verify server is accessible at the configured port
- Check firewall settings
- Review logs for connection errors

### GTFS update fails

- Check internet connection
- Verify URL is accessible: https://rrgtfsfeeds.s3.amazonaws.com/gtfsmnr.zip
- Check disk space in `gtfs/metro-north-railroad/` directory
- Review error message in dialog and logs

## Development

### Modifying the UI

1. Open `resources/main_window.ui` in Qt Designer
2. Make your changes
3. Save the file
4. Regenerate Python code: `./generate_ui.sh`
5. Test changes by running `gui_app.py`

### Adding Features

To add new features:

1. Add UI elements in Qt Designer (`resources/main_window.ui`)
2. Regenerate Python UI code
3. Add signal connections in `MainWindowController._connect_signals()`
4. Implement handler methods in `MainWindowController`
5. Test thoroughly

### Testing

While the GUI requires a display server to run, you can validate:

- Code imports correctly
- Logic is sound (unit tests for controller methods)
- UI generation works (`./generate_ui.sh`)
- Dependencies are installed

## License

Same as parent project.
