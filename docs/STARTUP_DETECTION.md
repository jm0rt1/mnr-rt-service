# Server Startup Detection and Progress Tracking

This document describes the server startup detection and progress tracking features implemented for the MNR Real-Time Service Manager GUI.

## Overview

The GUI now provides real-time feedback about the server startup process, including:

1. **Visual progress bar** showing startup completion percentage
2. **Startup phase display** showing the current phase (e.g., "Loading GTFS data...")
3. **Time estimation** for remaining startup time
4. **Health check verification** ensuring the server is actually responding before marking it as "Running"
5. **Enhanced logging** throughout the startup process

## Startup Phases

The server startup process is divided into the following phases:

| Phase | Progress | Description |
|-------|----------|-------------|
| INITIALIZING | 0% | Server process starting |
| GTFS_CHECK | 20% | Checking if GTFS data needs update |
| GTFS_DOWNLOAD | 30% | Downloading GTFS data (if needed) |
| GTFS_CHECK_COMPLETE | 40% | GTFS check done |
| GTFS_CHECK_SKIPPED | 40% | GTFS check skipped (if --skip-gtfs-update used) |
| CLIENT_INIT | 60% | Initializing MTA GTFS real-time client |
| GTFS_LOAD | 75% | Loading GTFS static data into memory |
| SERVER_START | 90% | Starting Flask HTTP server |
| READY | 100% | Server ready, performing health check |

## How It Works

### 1. Web Server Changes (`web_server.py`)

The web server now outputs structured log messages with phase markers:

```python
print("STARTUP_PHASE: INITIALIZING")
print("Initializing MNR Real-Time Relay Server...")
# ... initialization code ...
print("STARTUP_PHASE: CLIENT_INIT")
print("Initializing GTFS real-time client...")
# ... more phases ...
print("STARTUP_PHASE: READY")
print("✓ Server is ready and accepting connections")
```

These markers are designed to be easily parseable while remaining human-readable.

### 2. GUI Detection (`ServerThread` in `main_window_controller.py`)

The `ServerThread` class reads the server output line by line and detects phase markers:

```python
for line in iter(self.process.stdout.readline, ''):
    if line:
        stripped_line = line.rstrip()
        self.output_ready.emit(stripped_line)
        # Detect startup phase markers
        if "STARTUP_PHASE:" in stripped_line:
            phase = stripped_line.split("STARTUP_PHASE:")[-1].strip()
            self.startup_phase.emit(phase)
```

### 3. Progress Tracking (`MainWindowController`)

The main controller maintains a mapping of phases to progress percentages:

```python
self.startup_phases = {
    'INITIALIZING': {'order': 0, 'display': 'Initializing...', 'progress': 0},
    'GTFS_CHECK': {'order': 1, 'display': 'Checking GTFS data...', 'progress': 20},
    # ... more phases ...
    'READY': {'order': 7, 'display': 'Ready', 'progress': 100}
}
```

When a phase is detected, the controller:
- Updates the progress bar to the corresponding percentage
- Updates the phase label with a user-friendly description
- Tracks timing to estimate remaining startup time
- Shows estimated remaining time in the progress bar (e.g., "75% (~3s remaining)")

### 4. Health Check Verification

When the server reports it's ready (`READY` phase), the GUI doesn't immediately mark it as "Running". Instead, it:

1. Starts a health check timer that runs every 500ms
2. Attempts to connect to the server's `/health` endpoint
3. Only marks the server as "Running" after receiving a successful health response
4. Times out after 20 attempts (10 seconds) if the server doesn't respond

This ensures the GUI accurately reflects the server's actual state.

## UI Changes

### New UI Elements

The Server Control section now includes:

1. **Startup Phase Label**: Shows the current phase name (e.g., "Loading GTFS data...")
2. **Progress Bar**: Visual representation of startup progress with percentage and time estimate

```
Server Status: Starting...
Startup Phase: Loading GTFS data...
[████████████████░░░░] 75% (~3s remaining)
```

When the server is not starting or has finished starting, the progress bar is hidden.

### Status Colors

The server status label uses colors to indicate state:
- **Orange**: "Starting..." (server is starting up)
- **Green**: "Running" (server is running and verified via health check)
- **Red**: "Stopped" (server is not running)

## Example Startup Sequence

Here's what a typical startup looks like in the GUI:

```
1. User clicks "Start Server"
   Status: "Starting..." (orange)
   Phase: "Initializing..."
   Progress: [░░░░░░░░░░░░░░░░░░░░] 0%

2. Server initializes
   Status: "Starting..." (orange)
   Phase: "Checking GTFS data..."
   Progress: [████░░░░░░░░░░░░░░░░] 20%

3. GTFS check completes (skipped or complete)
   Status: "Starting..." (orange)
   Phase: "GTFS check complete"
   Progress: [████████░░░░░░░░░░░░] 40%

4. Client initializes
   Status: "Starting..." (orange)
   Phase: "Initializing client..."
   Progress: [████████████░░░░░░░░] 60%

5. GTFS data loads
   Status: "Starting..." (orange)
   Phase: "Loading GTFS data..."
   Progress: [███████████████░░░░░] 75% (~2s remaining)

6. Server starts
   Status: "Starting..." (orange)
   Phase: "Starting server..."
   Progress: [██████████████████░░] 90% (~1s remaining)

7. Server reports ready
   Status: "Starting..." (orange)
   Phase: "Ready"
   Progress: [████████████████████] 100%
   (Health check in progress...)

8. Health check passes
   Status: "Running" (green)
   Phase: "Running"
   Progress bar hidden
```

## Benefits

1. **User Feedback**: Users know exactly what's happening during startup
2. **Problem Diagnosis**: If startup fails, users can see which phase failed
3. **Time Awareness**: Users get an estimate of how long startup will take
4. **Accurate Status**: Health check ensures status reflects reality
5. **Enhanced Logging**: All startup activities are logged for troubleshooting

## Testing

The implementation includes unit tests to verify:

1. All startup phases are present in server output
2. Phases appear in the correct order
3. GTFS_CHECK phase appears when not skipped
4. GUI code is syntactically valid

Run tests with:
```bash
python -m unittest tests.test_startup_phases
python tests/validate_gui.py
```

## Future Enhancements

Possible future improvements:

1. **More detailed progress**: Break down GTFS loading by component (routes, stops, trips)
2. **Historical timing**: Remember typical startup times to improve estimates
3. **Phase skipping detection**: Automatically adjust expectations based on configuration
4. **Error recovery**: Better handling of partial failures during startup
5. **Parallel loading**: Optimize startup by loading components in parallel

## Technical Notes

- The progress bar uses Qt's `QProgressBar` widget
- Phase detection is performed by simple string matching in server output
- Time estimation uses a simple average of elapsed time per progress percentage
- Health checks use the existing `/health` endpoint with a 2-second timeout
- The implementation is backward compatible - old server versions without phase markers will still work, just without progress feedback
