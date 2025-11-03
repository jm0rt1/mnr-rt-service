# MNR Real-Time Service Manager - GUI Screenshots & Visual Guide

This document provides a visual description of the GUI interface since screenshots cannot be captured in a headless environment.

## Main Window Layout

The main window is 1200x800 pixels and features a tabbed interface with three main sections:

### Tab 1: Server Control

```
┌─────────────────────────────────────────────────────────────┐
│ MNR Real-Time Service Manager                              │
├─────────────────────────────────────────────────────────────┤
│ [Server Control] [Logs & Errors] [Train Data Visualization] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Server Control                                                │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Server Status: [Stopped]                               │   │
│ │ [Start Server] [Stop Server] [Restart Server]          │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ Server Configuration                                          │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Host:         [0.0.0.0                              ] │   │
│ │ Port:         [5000  ▼]                               │   │
│ │ MTA API Key:  [********************] (password field)  │   │
│ │ Debug Mode:   ☐ Enable Debug Mode                     │   │
│ │ GTFS Update:  ☐ Skip GTFS update on startup           │   │
│ │               [Apply Configuration]                    │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
│ GTFS Data Management                                          │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Last Download: Never                                   │   │
│ │ [Update GTFS Data Now] [Force Update (Bypass Rate Limit)]│
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Server status indicator (green when running, red when stopped)
- Start/Stop/Restart buttons for server control
- Configuration fields for host, port, API key, debug mode
- GTFS data management with update status and manual update buttons

### Tab 2: Logs & Errors

```
┌─────────────────────────────────────────────────────────────┐
│ MNR Real-Time Service Manager                              │
├─────────────────────────────────────────────────────────────┤
│ [Server Control] [Logs & Errors] [Train Data Visualization] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ [Clear Logs] [Save Logs]                    ☑ Auto-scroll   │
│                                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ [2025-11-03 01:38:15] [INFO] GUI initialized           │   │
│ │ [2025-11-03 01:38:20] [INFO] Starting server...        │   │
│ │ [2025-11-03 01:38:21] [INFO] Server started on 0.0.0.0:5000│
│ │ [2025-11-03 01:38:21] [INFO] Checking for GTFS updates │   │
│ │ [2025-11-03 01:38:22] [INFO] GTFS data is up to date   │   │
│ │ [2025-11-03 01:38:30] [INFO] Fetched 20 trains         │   │
│ │                                                         │   │
│ │                                                         │   │
│ │                                                         │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Scrollable text area showing all server logs
- Clear Logs button to clear the display
- Save Logs button to export logs to a file
- Auto-scroll checkbox to automatically scroll to latest entries
- Color-coded log levels (INFO, WARNING, ERROR)
- Timestamps for all log entries

### Tab 3: Train Data Visualization

```
┌─────────────────────────────────────────────────────────────┐
│ MNR Real-Time Service Manager                              │
├─────────────────────────────────────────────────────────────┤
│ [Server Control] [Logs & Errors] [Train Data Visualization] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ Train Limit: [20 ▼] [Refresh Train Data]  ☐ Auto-refresh (30s)│
│ Last updated: 2025-11-03T01:38:30Z                           │
│                                                               │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Trip ID  │ Route  │ Current Stop │ Next Stop │ ETA    │...│
│ ├──────────┼────────┼──────────────┼───────────┼────────┤   │
│ │ 1234567  │ Hudson │ Grand Central│ 125th St  │ 14:45  │...│
│ │ 2345678  │ Harlem │ 125th Street │ Fordham   │ 14:50  │...│
│ │ 3456789  │ NewHaven│ Stamford    │ Norwalk   │ 15:00  │...│
│ │ 4567890  │ Hudson │ Tarrytown    │ Ossining  │ 15:15  │...│
│ │ 5678901  │ Harlem │ White Plains │ N.WhitePl │ 15:20  │...│
│ │          │        │              │           │        │   │
│ │          │        │              │           │        │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Table Columns:
┌──────────┬────────┬──────────────┬───────────┬──────┬───────┬─────────┐
│ Trip ID  │ Route  │ Current Stop │ Next Stop │ ETA  │ Track │ Status  │
└──────────┴────────┴──────────────┴───────────┴──────┴───────┴─────────┘
```

**Features:**
- Configurable train limit (1-100)
- Refresh button to manually update data
- Auto-refresh checkbox for automatic updates every 30 seconds
- Sortable table columns (click headers to sort)
- Color-coded status column:
  - Light green background for "On Time"
  - Light red background for "Delayed"
- Seven columns of train information:
  1. Trip ID
  2. Route
  3. Current Stop
  4. Next Stop
  5. ETA (formatted as HH:MM:SS)
  6. Track
  7. Status
- Alternating row colors for easy reading
- Select entire rows
- Timestamp showing when data was last updated

## Menu Bar

```
[File]  [Help]
  │       │
  ├─ Exit └─ About
```

**File Menu:**
- Exit: Close the application (prompts if server is running)

**Help Menu:**
- About: Shows information about the application

## Status Bar

The bottom of the window shows a status bar for additional information.

## Color Scheme

- **Server Status:**
  - Green text: Server running
  - Red text: Server stopped
  
- **Train Status:**
  - Light green (RGB 200, 255, 200): On Time
  - Light red (RGB 255, 200, 200): Delayed
  - White: Unknown/N/A

- **Buttons:**
  - Standard system button colors
  - Disabled buttons appear grayed out

## Window Title

"MNR Real-Time Service Manager"

## Application Workflow

### Starting the Server

1. Open the GUI (`python gui_app.py`)
2. Go to "Server Control" tab
3. Configure settings (optional)
4. Click "Start Server"
5. Watch status change to "Running" (green)
6. View logs in "Logs & Errors" tab

### Viewing Train Data

1. Ensure server is running
2. Go to "Train Data Visualization" tab
3. Click "Refresh Train Data"
4. View real-time train information in the table
5. Enable "Auto-refresh" for automatic updates

### Managing GTFS Data

1. Go to "Server Control" tab
2. Scroll to "GTFS Data Management" section
3. View last download time
4. Click "Update GTFS Data Now" to update (respects 24-hour limit)
5. Or click "Force Update" to bypass rate limiting

## Keyboard Shortcuts

While not explicitly defined in the code, Qt provides standard shortcuts:
- Ctrl+Q: Quit (via File menu)
- Alt+F: Open File menu
- Alt+H: Open Help menu

## Responsive Design

- Window can be resized
- Table columns automatically resize to content
- Logs text area expands with window
- Minimum window size: 1200x800

## Notes

- GUI requires PySide6 and a display server (X11, Wayland, etc.)
- On headless servers, use Xvfb for virtual display
- All server output is captured and displayed in the Logs tab
- Server runs as a separate process, allowing GUI to remain responsive
- Configuration changes require server restart to take effect

## Future Enhancements

Potential additions not yet implemented:
- Server log filters (show only errors, warnings, etc.)
- Save/load configuration presets
- Export train data to CSV
- Graphs/charts for train status over time
- Notification system for delays
- Multi-server support
