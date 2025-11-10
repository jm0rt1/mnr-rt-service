"""
Main Window Controller

Handles all the logic for the main window GUI, including:
- Server control (start/stop/restart)
- Configuration management
- GTFS data updates
- Log display
- Train data visualization
"""

import sys
import subprocess
import logging
import json
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, 
    QHeaderView, QTextEdit, QGroupBox
)
from PySide6.QtCore import QTimer, QThread, Signal, Qt
from PySide6.QtGui import QColor
import requests

from src.gui.views.generated.main_window import Ui_MainWindow
from src.gtfs_downloader import GTFSDownloader
from src.shared.settings import GlobalSettings


logger = logging.getLogger(__name__)


class ServerThread(QThread):
    """Thread for running the web server process"""
    
    output_ready = Signal(str)
    error_ready = Signal(str)
    finished = Signal(int)
    startup_phase = Signal(str)  # Signal for startup phase updates
    
    def __init__(self, host, port, api_key, debug, skip_gtfs):
        super().__init__()
        self.host = host
        self.port = port
        self.api_key = api_key
        self.debug = debug
        self.skip_gtfs = skip_gtfs
        self.process = None
        
    def run(self):
        """Run the web server process"""
        # Find web_server.py in the project root
        project_root = Path(__file__).parent.parent.parent.parent
        web_server_path = project_root / "web_server.py"
        
        if not web_server_path.exists():
            # Try current working directory as fallback
            web_server_path = Path.cwd() / "web_server.py"
            if not web_server_path.exists():
                self.error_ready.emit("Cannot find web_server.py. Please run from project root.")
                self.finished.emit(-1)
                return
        
        cmd = [sys.executable, str(web_server_path), "--host", self.host, "--port", str(self.port)]
        
        if self.api_key:
            cmd.extend(["--api-key", self.api_key])
        if self.debug:
            cmd.append("--debug")
        if self.skip_gtfs:
            cmd.append("--skip-gtfs-update")
            
        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    stripped_line = line.rstrip()
                    self.output_ready.emit(stripped_line)
                    # Detect startup phase markers
                    if "STARTUP_PHASE:" in stripped_line:
                        phase = stripped_line.split("STARTUP_PHASE:")[-1].strip()
                        self.startup_phase.emit(phase)
                    
            exit_code = self.process.wait()
            self.finished.emit(exit_code)
            
        except Exception as e:
            self.error_ready.emit(f"Failed to start server: {str(e)}")
            self.finished.emit(-1)
    
    def stop(self):
        """Stop the server process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class MainWindowController(QMainWindow):
    """Main window controller for the MNR Real-Time Service Manager"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialize state
        self.server_thread = None
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.refresh_train_data)
        
        # Startup tracking
        self.startup_phases = {
            'INITIALIZING': {'order': 0, 'display': 'Initializing...', 'progress': 0},
            'GTFS_CHECK': {'order': 1, 'display': 'Checking GTFS data...', 'progress': 20},
            'GTFS_DOWNLOAD': {'order': 2, 'display': 'Downloading GTFS data...', 'progress': 30},
            'GTFS_CHECK_COMPLETE': {'order': 3, 'display': 'GTFS check complete', 'progress': 40},
            'GTFS_CHECK_SKIPPED': {'order': 3, 'display': 'GTFS check skipped', 'progress': 40},
            'CLIENT_INIT': {'order': 4, 'display': 'Initializing client...', 'progress': 60},
            'GTFS_LOAD': {'order': 5, 'display': 'Loading GTFS data...', 'progress': 75},
            'SERVER_START': {'order': 6, 'display': 'Starting server...', 'progress': 90},
            'READY': {'order': 7, 'display': 'Ready', 'progress': 100}
        }
        self.current_startup_phase = None
        self.startup_start_time = None
        self.phase_times = {}  # Track time spent in each phase
        
        # Health check timer
        self.health_check_timer = QTimer(self)
        self.health_check_timer.timeout.connect(self.check_server_health)
        self.health_check_attempts = 0
        self.max_health_check_attempts = 20
        
        # Connect signals
        self._connect_signals()
        
        # Initialize GTFS downloader
        self.gtfs_downloader = GTFSDownloader(
            gtfs_url=GlobalSettings.GTFSDownloadSettings.GTFS_FEED_URL,
            output_dir=GlobalSettings.GTFS_MNR_DATA_DIR,
            min_download_interval=GlobalSettings.GTFSDownloadSettings.MIN_DOWNLOAD_INTERVAL
        )
        
        # Update GTFS info
        self.update_gtfs_info()
        
        # Add new tabs for all endpoints
        self._setup_additional_tabs()
        
        # Enhance the trains tab with additional filters
        self._enhance_trains_tab()
        
        # Log initial message
        self.log_message("GUI initialized. Ready to start server.", "INFO")
    
    def _connect_signals(self):
        """Connect all UI signals to their handlers"""
        # Server control buttons
        self.ui.startButton.clicked.connect(self.start_server)
        self.ui.stopButton.clicked.connect(self.stop_server)
        self.ui.restartButton.clicked.connect(self.restart_server)
        
        # Configuration
        self.ui.applyConfigButton.clicked.connect(self.apply_configuration)
        
        # GTFS management
        self.ui.updateGtfsButton.clicked.connect(self.update_gtfs_data)
        self.ui.forceUpdateGtfsButton.clicked.connect(self.force_update_gtfs_data)
        
        # Logs
        self.ui.clearLogsButton.clicked.connect(self.clear_logs)
        self.ui.saveLogsButton.clicked.connect(self.save_logs)
        
        # Train data
        self.ui.refreshDataButton.clicked.connect(self.refresh_train_data)
        self.ui.autoRefreshCheckBox.toggled.connect(self.toggle_auto_refresh)
        
        # Menu actions
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.show_about)
    
    def _setup_additional_tabs(self):
        """Setup additional tabs for viewing all API endpoints"""
        # Stations Tab
        self.stationsTab = QWidget()
        self.stationsTabLayout = QVBoxLayout(self.stationsTab)
        
        # Stations controls
        stationsControlLayout = QHBoxLayout()
        self.refreshStationsButton = QPushButton("Refresh Stations")
        self.refreshStationsButton.clicked.connect(self.refresh_stations_data)
        stationsControlLayout.addWidget(self.refreshStationsButton)
        stationsControlLayout.addStretch()
        self.stationsStatusLabel = QLabel("Click 'Refresh Stations' to load data")
        stationsControlLayout.addWidget(self.stationsStatusLabel)
        self.stationsTabLayout.addLayout(stationsControlLayout)
        
        # Stations table
        self.stationsTable = QTableWidget()
        self.stationsTable.setColumnCount(6)
        self.stationsTable.setHorizontalHeaderLabels([
            "Stop ID", "Stop Name", "Stop Code", "Latitude", "Longitude", "Wheelchair Boarding"
        ])
        self.stationsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stationsTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.stationsTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.stationsTable.setAlternatingRowColors(True)
        self.stationsTabLayout.addWidget(self.stationsTable)
        
        self.ui.tabWidget.addTab(self.stationsTab, "Stations")
        
        # Routes Tab
        self.routesTab = QWidget()
        self.routesTabLayout = QVBoxLayout(self.routesTab)
        
        # Routes controls
        routesControlLayout = QHBoxLayout()
        self.refreshRoutesButton = QPushButton("Refresh Routes")
        self.refreshRoutesButton.clicked.connect(self.refresh_routes_data)
        routesControlLayout.addWidget(self.refreshRoutesButton)
        routesControlLayout.addStretch()
        self.routesStatusLabel = QLabel("Click 'Refresh Routes' to load data")
        routesControlLayout.addWidget(self.routesStatusLabel)
        self.routesTabLayout.addLayout(routesControlLayout)
        
        # Routes table
        self.routesTable = QTableWidget()
        self.routesTable.setColumnCount(5)
        self.routesTable.setHorizontalHeaderLabels([
            "Route ID", "Route Name", "Short Name", "Color", "Text Color"
        ])
        self.routesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.routesTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.routesTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.routesTable.setAlternatingRowColors(True)
        self.routesTabLayout.addWidget(self.routesTable)
        
        self.ui.tabWidget.addTab(self.routesTab, "Routes")
        
        # Travel Assistance Tab
        self.travelTab = QWidget()
        self.travelTabLayout = QVBoxLayout(self.travelTab)
        
        # Travel controls
        travelControlLayout = QHBoxLayout()
        self.refreshTravelButton = QPushButton("Refresh All Travel Data")
        self.refreshTravelButton.clicked.connect(self.refresh_travel_data)
        travelControlLayout.addWidget(self.refreshTravelButton)
        travelControlLayout.addStretch()
        self.travelStatusLabel = QLabel("Click 'Refresh' to load travel assistance data")
        travelControlLayout.addWidget(self.travelStatusLabel)
        self.travelTabLayout.addLayout(travelControlLayout)
        
        # Travel data groups
        # Location
        locationGroup = QGroupBox("Network Location")
        locationLayout = QVBoxLayout()
        self.locationText = QTextEdit()
        self.locationText.setReadOnly(True)
        self.locationText.setMaximumHeight(100)
        locationLayout.addWidget(self.locationText)
        locationGroup.setLayout(locationLayout)
        self.travelTabLayout.addWidget(locationGroup)
        
        # Distance
        distanceGroup = QGroupBox("Distance to Station")
        distanceLayout = QVBoxLayout()
        self.distanceText = QTextEdit()
        self.distanceText.setReadOnly(True)
        self.distanceText.setMaximumHeight(100)
        distanceLayout.addWidget(self.distanceText)
        distanceGroup.setLayout(distanceLayout)
        self.travelTabLayout.addWidget(distanceGroup)
        
        # Next Train
        nextTrainGroup = QGroupBox("Next Train Recommendation")
        nextTrainLayout = QVBoxLayout()
        self.nextTrainText = QTextEdit()
        self.nextTrainText.setReadOnly(True)
        nextTrainLayout.addWidget(self.nextTrainText)
        nextTrainGroup.setLayout(nextTrainLayout)
        self.travelTabLayout.addWidget(nextTrainGroup)
        
        # Arduino Device
        arduinoGroup = QGroupBox("Arduino Device")
        arduinoLayout = QVBoxLayout()
        self.arduinoText = QTextEdit()
        self.arduinoText.setReadOnly(True)
        self.arduinoText.setMaximumHeight(80)
        arduinoLayout.addWidget(self.arduinoText)
        arduinoGroup.setLayout(arduinoLayout)
        self.travelTabLayout.addWidget(arduinoGroup)
        
        self.ui.tabWidget.addTab(self.travelTab, "Travel Assistance")
        
        # Vehicle Positions Tab
        self.vehiclePositionsTab = QWidget()
        self.vehiclePositionsTabLayout = QVBoxLayout(self.vehiclePositionsTab)
        
        # Vehicle positions controls
        vehiclePositionsControlLayout = QHBoxLayout()
        
        # Limit control
        limitLabel = QLabel("Limit:")
        vehiclePositionsControlLayout.addWidget(limitLabel)
        self.vehicleLimitSpinBox = QSpinBox()
        self.vehicleLimitSpinBox.setMinimum(1)
        self.vehicleLimitSpinBox.setMaximum(100)
        self.vehicleLimitSpinBox.setValue(20)
        vehiclePositionsControlLayout.addWidget(self.vehicleLimitSpinBox)
        
        # Route filter
        routeLabel = QLabel("Route:")
        vehiclePositionsControlLayout.addWidget(routeLabel)
        self.vehicleRouteEdit = QLineEdit()
        self.vehicleRouteEdit.setPlaceholderText("Optional route filter")
        self.vehicleRouteEdit.setMaximumWidth(150)
        vehiclePositionsControlLayout.addWidget(self.vehicleRouteEdit)
        
        # Trip ID filter
        tripIdLabel = QLabel("Trip ID:")
        vehiclePositionsControlLayout.addWidget(tripIdLabel)
        self.vehicleTripIdEdit = QLineEdit()
        self.vehicleTripIdEdit.setPlaceholderText("Optional trip ID filter")
        self.vehicleTripIdEdit.setMaximumWidth(150)
        vehiclePositionsControlLayout.addWidget(self.vehicleTripIdEdit)
        
        self.refreshVehiclePositionsButton = QPushButton("Refresh")
        self.refreshVehiclePositionsButton.clicked.connect(self.refresh_vehicle_positions_data)
        vehiclePositionsControlLayout.addWidget(self.refreshVehiclePositionsButton)
        vehiclePositionsControlLayout.addStretch()
        self.vehiclePositionsStatusLabel = QLabel("Click 'Refresh' to load vehicle positions")
        vehiclePositionsControlLayout.addWidget(self.vehiclePositionsStatusLabel)
        self.vehiclePositionsTabLayout.addLayout(vehiclePositionsControlLayout)
        
        # Vehicle positions table
        self.vehiclePositionsTable = QTableWidget()
        self.vehiclePositionsTable.setColumnCount(9)
        self.vehiclePositionsTable.setHorizontalHeaderLabels([
            "Vehicle ID", "Trip ID", "Route", "Latitude", "Longitude", 
            "Bearing", "Speed", "Stop ID", "Status"
        ])
        self.vehiclePositionsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vehiclePositionsTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.vehiclePositionsTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.vehiclePositionsTable.setAlternatingRowColors(True)
        self.vehiclePositionsTabLayout.addWidget(self.vehiclePositionsTable)
        
        self.ui.tabWidget.addTab(self.vehiclePositionsTab, "Vehicle Positions")
        
        # Alerts Tab
        self.alertsTab = QWidget()
        self.alertsTabLayout = QVBoxLayout(self.alertsTab)
        
        # Alerts controls
        alertsControlLayout = QHBoxLayout()
        
        # Route filter
        alertRouteLabel = QLabel("Route:")
        alertsControlLayout.addWidget(alertRouteLabel)
        self.alertRouteEdit = QLineEdit()
        self.alertRouteEdit.setPlaceholderText("Optional route filter")
        self.alertRouteEdit.setMaximumWidth(150)
        alertsControlLayout.addWidget(self.alertRouteEdit)
        
        # Stop filter
        alertStopLabel = QLabel("Stop:")
        alertsControlLayout.addWidget(alertStopLabel)
        self.alertStopEdit = QLineEdit()
        self.alertStopEdit.setPlaceholderText("Optional stop filter")
        self.alertStopEdit.setMaximumWidth(150)
        alertsControlLayout.addWidget(self.alertStopEdit)
        
        self.refreshAlertsButton = QPushButton("Refresh")
        self.refreshAlertsButton.clicked.connect(self.refresh_alerts_data)
        alertsControlLayout.addWidget(self.refreshAlertsButton)
        alertsControlLayout.addStretch()
        self.alertsStatusLabel = QLabel("Click 'Refresh' to load service alerts")
        alertsControlLayout.addWidget(self.alertsStatusLabel)
        self.alertsTabLayout.addLayout(alertsControlLayout)
        
        # Alerts table
        self.alertsTable = QTableWidget()
        self.alertsTable.setColumnCount(5)
        self.alertsTable.setHorizontalHeaderLabels([
            "Alert ID", "Header", "Description", "Effect", "Informed Entities"
        ])
        self.alertsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alertsTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alertsTable.setSelectionBehavior(QTableWidget.SelectRows)
        self.alertsTable.setAlternatingRowColors(True)
        self.alertsTable.verticalHeader().setVisible(True)
        self.alertsTabLayout.addWidget(self.alertsTable)
        
        self.ui.tabWidget.addTab(self.alertsTab, "Alerts")
        
        # API Info Tab
        self.apiInfoTab = QWidget()
        self.apiInfoTabLayout = QVBoxLayout(self.apiInfoTab)
        
        # API info controls
        apiInfoControlLayout = QHBoxLayout()
        self.refreshApiInfoButton = QPushButton("Refresh API Info")
        self.refreshApiInfoButton.clicked.connect(self.refresh_api_info)
        apiInfoControlLayout.addWidget(self.refreshApiInfoButton)
        apiInfoControlLayout.addStretch()
        self.apiInfoStatusLabel = QLabel("Click 'Refresh' to load API information")
        apiInfoControlLayout.addWidget(self.apiInfoStatusLabel)
        self.apiInfoTabLayout.addLayout(apiInfoControlLayout)
        
        # API info display
        self.apiInfoText = QTextEdit()
        self.apiInfoText.setReadOnly(True)
        self.apiInfoTabLayout.addWidget(self.apiInfoText)
        
        self.ui.tabWidget.addTab(self.apiInfoTab, "API Information")
    
    def _enhance_trains_tab(self):
        """Add additional filter controls to the trains/data tab"""
        # Create a filter controls group
        filtersGroup = QGroupBox("Filters (Optional)")
        filtersLayout = QHBoxLayout()
        
        # Route filter
        routeLabel = QLabel("Route:")
        filtersLayout.addWidget(routeLabel)
        self.trainRouteEdit = QLineEdit()
        self.trainRouteEdit.setPlaceholderText("e.g., 1, 2, Hudson")
        self.trainRouteEdit.setMaximumWidth(120)
        filtersLayout.addWidget(self.trainRouteEdit)
        
        # Origin station filter
        originLabel = QLabel("Origin:")
        filtersLayout.addWidget(originLabel)
        self.trainOriginEdit = QLineEdit()
        self.trainOriginEdit.setPlaceholderText("Station ID")
        self.trainOriginEdit.setMaximumWidth(120)
        filtersLayout.addWidget(self.trainOriginEdit)
        
        # Destination station filter
        destLabel = QLabel("Destination:")
        filtersLayout.addWidget(destLabel)
        self.trainDestEdit = QLineEdit()
        self.trainDestEdit.setPlaceholderText("Station ID")
        self.trainDestEdit.setMaximumWidth(120)
        filtersLayout.addWidget(self.trainDestEdit)
        
        # Clear filters button
        clearFiltersButton = QPushButton("Clear Filters")
        clearFiltersButton.clicked.connect(self.clear_train_filters)
        filtersLayout.addWidget(clearFiltersButton)
        
        filtersLayout.addStretch()
        filtersGroup.setLayout(filtersLayout)
        
        # Insert the filters group into the data tab layout
        # Insert after the first control row (limit/refresh) but before the status label
        self.ui.dataTab.layout().insertWidget(1, filtersGroup)
    
    def clear_train_filters(self):
        """Clear all train filter fields"""
        self.trainRouteEdit.clear()
        self.trainOriginEdit.clear()
        self.trainDestEdit.clear()
        self.log_message("Cleared train filters", "INFO")
    
    def log_message(self, message, level="INFO"):
        """Add a message to the log display"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Add to log widget
        self.ui.logsTextEdit.append(formatted_message)
        
        # Auto-scroll if enabled
        if self.ui.autoScrollCheckBox.isChecked():
            scrollbar = self.ui.logsTextEdit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def update_startup_phase(self, phase):
        """Update the startup phase display and progress bar"""
        if phase not in self.startup_phases:
            return
        
        phase_info = self.startup_phases[phase]
        self.current_startup_phase = phase
        
        # Update phase label
        self.ui.startupPhaseValue.setText(phase_info['display'])
        
        # Update progress bar
        self.ui.startupProgressBar.setValue(phase_info['progress'])
        
        # Track timing for estimation
        current_time = datetime.now()
        if self.startup_start_time:
            elapsed = (current_time - self.startup_start_time).total_seconds()
            self.phase_times[phase] = elapsed
            
            # Estimate remaining time for phases < 100%
            if phase_info['progress'] < 100:
                # Simple estimation: assume remaining phases take similar time
                avg_time_per_percent = elapsed / phase_info['progress'] if phase_info['progress'] > 0 else 0
                remaining_percent = 100 - phase_info['progress']
                estimated_remaining = avg_time_per_percent * remaining_percent
                # Cap the estimate to a maximum of 60 seconds to avoid unrealistic values
                estimated_remaining = min(estimated_remaining, 60)
                # Update progress bar format to show estimate
                if estimated_remaining >= 1:
                    self.ui.startupProgressBar.setFormat(f"%p% (~{estimated_remaining:.0f}s remaining)")
                else:
                    self.ui.startupProgressBar.setFormat("%p% (Almost done...)")
            else:
                self.ui.startupProgressBar.setFormat("%p%")
        
        # If server is ready, start health checks
        if phase == 'READY':
            self.log_message("Server reports ready, verifying health...", "INFO")
            self.health_check_attempts = 0
            self.health_check_timer.start(500)  # Check every 500ms
    
    def check_server_health(self):
        """Check if the server is actually responding to requests"""
        self.health_check_attempts += 1
        
        # Get the server host and port
        host = self.ui.hostEdit.text()
        if host == "0.0.0.0":
            host = "localhost"
        port = self.ui.portSpinBox.value()
        
        try:
            # Try to hit the health endpoint
            response = requests.get(f"http://{host}:{port}/health", timeout=2)
            
            if response.status_code == 200:
                # Server is healthy!
                self.health_check_timer.stop()
                self.on_server_ready()
                self.log_message("✓ Server health check passed - server is running", "INFO")
            else:
                self.log_message(f"Server responded with status {response.status_code}", "WARNING")
                if self.health_check_attempts >= self.max_health_check_attempts:
                    self.health_check_timer.stop()
                    self.log_message("Health check timeout - server may not be responding correctly", "WARNING")
                    self.on_server_ready()  # Continue anyway
                    
        except requests.ConnectionError:
            if self.health_check_attempts >= self.max_health_check_attempts:
                self.health_check_timer.stop()
                self.log_message("Health check timeout - could not connect to server", "WARNING")
                # Don't mark as ready since we couldn't connect
        except Exception as e:
            self.log_message(f"Health check error: {str(e)}", "WARNING")
            if self.health_check_attempts >= self.max_health_check_attempts:
                self.health_check_timer.stop()
    
    def on_server_ready(self):
        """Called when server is confirmed to be ready and responding"""
        # Update UI to show server is truly running
        self.ui.serverStatusValue.setText("Running")
        self.ui.serverStatusValue.setStyleSheet("color: green; font-weight: bold;")
        
        # Hide progress bar and show final status
        self.ui.startupProgressBar.setVisible(False)
        self.ui.startupPhaseValue.setText("Running")
        
        # Reset startup tracking
        self.startup_start_time = None
        self.current_startup_phase = None
    
    def start_server(self):
        """Start the web server"""
        if self.server_thread and self.server_thread.isRunning():
            self.log_message("Server is already running", "WARNING")
            return
        
        # Get configuration
        host = self.ui.hostEdit.text()
        port = self.ui.portSpinBox.value()
        api_key = self.ui.apiKeyEdit.text() or None
        debug = self.ui.debugCheckBox.isChecked()
        skip_gtfs = self.ui.skipGtfsCheckBox.isChecked()
        
        self.log_message(f"Starting server on {host}:{port}...", "INFO")
        
        # Initialize startup tracking
        self.startup_start_time = datetime.now()
        self.phase_times = {}
        
        # Show and reset progress bar
        self.ui.startupProgressBar.setVisible(True)
        self.ui.startupProgressBar.setValue(0)
        self.ui.startupProgressBar.setFormat("%p%")
        self.ui.startupPhaseValue.setText("Initializing...")
        
        # Create and start server thread
        self.server_thread = ServerThread(host, port, api_key, debug, skip_gtfs)
        self.server_thread.output_ready.connect(self.log_message)
        self.server_thread.error_ready.connect(lambda msg: self.log_message(msg, "ERROR"))
        self.server_thread.finished.connect(self.on_server_finished)
        self.server_thread.startup_phase.connect(self.update_startup_phase)
        self.server_thread.start()
        
        # Update UI to show starting
        self.ui.serverStatusValue.setText("Starting...")
        self.ui.serverStatusValue.setStyleSheet("color: orange; font-weight: bold;")
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.restartButton.setEnabled(True)
    
    def stop_server(self):
        """Stop the web server"""
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Server is not running", "WARNING")
            return
        
        self.log_message("Stopping server...", "INFO")
        
        # Stop health check timer if running
        if self.health_check_timer.isActive():
            self.health_check_timer.stop()
        
        self.server_thread.stop()
        self.server_thread.wait()
        
        # Update UI
        self.ui.serverStatusValue.setText("Stopped")
        self.ui.serverStatusValue.setStyleSheet("color: red; font-weight: bold;")
        self.ui.startupPhaseValue.setText("N/A")
        self.ui.startupProgressBar.setVisible(False)
        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.restartButton.setEnabled(False)
        
        self.log_message("Server stopped", "INFO")
    
    def restart_server(self):
        """Restart the web server"""
        self.log_message("Restarting server...", "INFO")
        self.stop_server()
        QTimer.singleShot(1000, self.start_server)  # Wait 1 second before restarting
    
    def on_server_finished(self, exit_code):
        """Handle server process finishing"""
        # Stop health check timer if running
        if self.health_check_timer.isActive():
            self.health_check_timer.stop()
        
        if exit_code != 0:
            self.log_message(f"Server exited with code {exit_code}", "ERROR")
        else:
            self.log_message("Server exited normally", "INFO")
        
        # Update UI
        self.ui.serverStatusValue.setText("Stopped")
        self.ui.serverStatusValue.setStyleSheet("color: red; font-weight: bold;")
        self.ui.startupPhaseValue.setText("N/A")
        self.ui.startupProgressBar.setVisible(False)
        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.restartButton.setEnabled(False)
    
    def apply_configuration(self):
        """Apply configuration changes"""
        self.log_message("Configuration updated", "INFO")
        QMessageBox.information(
            self,
            "Configuration Applied",
            "Configuration has been updated. Restart the server for changes to take effect."
        )
    
    def update_gtfs_info(self):
        """Update GTFS download information display"""
        info = self.gtfs_downloader.get_download_info()
        
        if info['last_download']:
            last_download_str = f"Last Download: {info['last_download']}"
            if 'next_download_allowed_in_hours' in info:
                last_download_str += f" (Next download in {info['next_download_allowed_in_hours']:.1f} hours)"
        else:
            last_download_str = "Last Download: Never"
        
        self.ui.gtfsInfoLabel.setText(last_download_str)
        
        # Enable/disable update button based on rate limit
        self.ui.updateGtfsButton.setEnabled(info['can_download_now'])
    
    def update_gtfs_data(self):
        """Update GTFS data (respecting rate limits)"""
        if not self.gtfs_downloader.should_download():
            info = self.gtfs_downloader.get_download_info()
            hours_remaining = info.get('next_download_allowed_in_hours', 0)
            QMessageBox.warning(
                self,
                "Rate Limit",
                f"GTFS data was recently updated. Next download allowed in {hours_remaining:.1f} hours.\n\n"
                "Use 'Force Update' to bypass rate limiting."
            )
            return
        
        self._perform_gtfs_update(force=False)
    
    def force_update_gtfs_data(self):
        """Force update GTFS data (bypass rate limits)"""
        reply = QMessageBox.question(
            self,
            "Force Update",
            "This will bypass the rate limit and download GTFS data immediately.\n\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._perform_gtfs_update(force=True)
    
    def _perform_gtfs_update(self, force=False):
        """Perform the actual GTFS update"""
        self.log_message("Downloading GTFS data...", "INFO")
        
        try:
            success = self.gtfs_downloader.download_and_extract(force=force)
            
            if success:
                self.log_message("GTFS data updated successfully", "INFO")
                QMessageBox.information(
                    self,
                    "Success",
                    "GTFS data has been updated successfully."
                )
            else:
                self.log_message("GTFS data update failed", "ERROR")
                QMessageBox.critical(
                    self,
                    "Error",
                    "Failed to update GTFS data. Check logs for details."
                )
        except Exception as e:
            self.log_message(f"GTFS update error: {str(e)}", "ERROR")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to update GTFS data:\n{str(e)}"
            )
        finally:
            self.update_gtfs_info()
    
    def clear_logs(self):
        """Clear the log display"""
        self.ui.logsTextEdit.clear()
        self.log_message("Logs cleared", "INFO")
    
    def save_logs(self):
        """Save logs to a file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Logs",
            f"mnr_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write(self.ui.logsTextEdit.toPlainText())
                self.log_message(f"Logs saved to {file_path}", "INFO")
                QMessageBox.information(self, "Success", f"Logs saved to:\n{file_path}")
            except Exception as e:
                self.log_message(f"Failed to save logs: {str(e)}", "ERROR")
                QMessageBox.critical(self, "Error", f"Failed to save logs:\n{str(e)}")
    
    def refresh_train_data(self):
        """Refresh train data from the API"""
        # Get the server port
        port = self.ui.portSpinBox.value()
        limit = self.ui.trainLimitSpinBox.value()
        
        # Get filter values if they exist
        route_filter = self.trainRouteEdit.text().strip() if hasattr(self, 'trainRouteEdit') else ""
        origin_filter = self.trainOriginEdit.text().strip() if hasattr(self, 'trainOriginEdit') else ""
        dest_filter = self.trainDestEdit.text().strip() if hasattr(self, 'trainDestEdit') else ""
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch train data: Server is not running", "WARNING")
            return
        
        try:
            # Build query parameters
            params = {'limit': limit}
            if route_filter:
                params['route'] = route_filter
            if origin_filter:
                params['origin_station'] = origin_filter
            if dest_filter:
                params['destination_station'] = dest_filter
            
            # Fetch data from the API
            url = f"http://localhost:{port}/trains"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Update the table
            self.update_train_table(data['trains'])
            
            # Update status label with filter info
            timestamp = data.get('timestamp', 'Unknown')
            filters_text = []
            if route_filter:
                filters_text.append(f"route={route_filter}")
            if origin_filter:
                filters_text.append(f"origin={origin_filter}")
            if dest_filter:
                filters_text.append(f"dest={dest_filter}")
            filters_str = f" ({', '.join(filters_text)})" if filters_text else ""
            self.ui.dataStatusLabel.setText(f"Last updated: {timestamp}{filters_str}")
            
            self.log_message(f"Fetched {len(data['trains'])} trains", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
        except requests.Timeout:
            self.log_message("Request timed out while fetching train data", "ERROR")
        except Exception as e:
            self.log_message(f"Failed to fetch train data: {str(e)}", "ERROR")
    
    def update_train_table(self, trains):
        """Update the train data table with fresh data"""
        table = self.ui.trainTableWidget
        
        # Clear existing data
        table.setRowCount(0)
        
        # Add new data
        for train in trains:
            row = table.rowCount()
            table.insertRow(row)
            
            # Trip ID - show headsign if available for better context
            trip_id = train.get('trip_id', 'N/A')
            trip_headsign = train.get('trip_headsign')
            if trip_headsign:
                trip_display = f"{trip_headsign} ({trip_id})"
            else:
                trip_display = trip_id
            table.setItem(row, 0, QTableWidgetItem(trip_display))
            
            # Route - show route name if available, otherwise route ID
            route_display = train.get('route_name') if train.get('route_name') is not None else train.get('route_id', 'N/A')
            table.setItem(row, 1, QTableWidgetItem(route_display))
            
            # Current Stop - show stop name if available, otherwise stop ID
            current_stop_display = train.get('current_stop_name') if train.get('current_stop_name') is not None else train.get('current_stop', 'N/A')
            table.setItem(row, 2, QTableWidgetItem(current_stop_display))
            
            # Next Stop - show stop name if available, otherwise stop ID
            next_stop_display = train.get('next_stop_name') if train.get('next_stop_name') is not None else train.get('next_stop', 'N/A')
            table.setItem(row, 3, QTableWidgetItem(next_stop_display))
            
            # ETA
            eta = train.get('eta', 'N/A')
            if eta and eta != 'N/A':
                # Format the datetime nicely
                try:
                    dt = datetime.fromisoformat(eta.replace('Z', '+00:00'))
                    eta = dt.strftime('%H:%M:%S')
                except (ValueError, AttributeError):
                    # Keep original value if parsing fails
                    pass
            table.setItem(row, 4, QTableWidgetItem(str(eta)))
            
            # Track
            table.setItem(row, 5, QTableWidgetItem(train.get('track', 'N/A')))
            
            # Status
            status = train.get('status', 'N/A')
            status_item = QTableWidgetItem(str(status))
            
            # Color code by status
            if status and 'On Time' in str(status):
                status_item.setBackground(QColor(200, 255, 200))  # Light green
            elif status and 'Delay' in str(status):
                status_item.setBackground(QColor(255, 200, 200))  # Light red
            
            table.setItem(row, 6, status_item)
        
        # Resize columns to content
        table.resizeColumnsToContents()
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh of train data"""
        if checked:
            self.auto_refresh_timer.start(30000)  # 30 seconds
            self.log_message("Auto-refresh enabled (30s interval)", "INFO")
            # Do an initial refresh
            self.refresh_train_data()
        else:
            self.auto_refresh_timer.stop()
            self.log_message("Auto-refresh disabled", "INFO")
    
    def refresh_stations_data(self):
        """Refresh stations data from the API"""
        port = self.ui.portSpinBox.value()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch stations data: Server is not running", "WARNING")
            self.stationsStatusLabel.setText("Server is not running")
            return
        
        try:
            # Fetch data from the API
            url = f"http://localhost:{port}/stations"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            stations = data.get('stations', [])
            
            # Update the table
            self.stationsTable.setRowCount(0)
            for station in stations:
                row = self.stationsTable.rowCount()
                self.stationsTable.insertRow(row)
                
                self.stationsTable.setItem(row, 0, QTableWidgetItem(station.get('stop_id', 'N/A')))
                self.stationsTable.setItem(row, 1, QTableWidgetItem(station.get('stop_name', 'N/A')))
                self.stationsTable.setItem(row, 2, QTableWidgetItem(station.get('stop_code', 'N/A')))
                self.stationsTable.setItem(row, 3, QTableWidgetItem(station.get('stop_lat', 'N/A')))
                self.stationsTable.setItem(row, 4, QTableWidgetItem(station.get('stop_lon', 'N/A')))
                self.stationsTable.setItem(row, 5, QTableWidgetItem(station.get('wheelchair_boarding', 'N/A')))
            
            # Update status label
            timestamp = data.get('timestamp', 'Unknown')
            self.stationsStatusLabel.setText(f"Last updated: {timestamp} - Total: {len(stations)} stations")
            self.log_message(f"Fetched {len(stations)} stations", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
            self.stationsStatusLabel.setText("Connection error")
        except requests.Timeout:
            self.log_message("Request timed out while fetching stations data", "ERROR")
            self.stationsStatusLabel.setText("Request timed out")
        except Exception as e:
            self.log_message(f"Failed to fetch stations data: {str(e)}", "ERROR")
            self.stationsStatusLabel.setText("Error fetching data")
    
    def refresh_routes_data(self):
        """Refresh routes data from the API"""
        port = self.ui.portSpinBox.value()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch routes data: Server is not running", "WARNING")
            self.routesStatusLabel.setText("Server is not running")
            return
        
        try:
            # Fetch data from the API
            url = f"http://localhost:{port}/routes"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            routes = data.get('routes', [])
            
            # Update the table
            self.routesTable.setRowCount(0)
            for route in routes:
                row = self.routesTable.rowCount()
                self.routesTable.insertRow(row)
                
                self.routesTable.setItem(row, 0, QTableWidgetItem(route.get('route_id', 'N/A')))
                route_name = route.get('route_long_name', route.get('route_short_name', 'N/A'))
                self.routesTable.setItem(row, 1, QTableWidgetItem(route_name))
                self.routesTable.setItem(row, 2, QTableWidgetItem(route.get('route_short_name', 'N/A')))
                
                # Color display with background
                color_hex = route.get('route_color', 'FFFFFF')
                color_item = QTableWidgetItem(f"#{color_hex}")
                try:
                    color_item.setBackground(QColor(f"#{color_hex}"))
                except:
                    pass
                self.routesTable.setItem(row, 3, color_item)
                
                # Text color
                text_color_hex = route.get('route_text_color', '000000')
                text_color_item = QTableWidgetItem(f"#{text_color_hex}")
                try:
                    text_color_item.setBackground(QColor(f"#{text_color_hex}"))
                except:
                    pass
                self.routesTable.setItem(row, 4, text_color_item)
            
            # Update status label
            timestamp = data.get('timestamp', 'Unknown')
            self.routesStatusLabel.setText(f"Last updated: {timestamp} - Total: {len(routes)} routes")
            self.log_message(f"Fetched {len(routes)} routes", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
            self.routesStatusLabel.setText("Connection error")
        except requests.Timeout:
            self.log_message("Request timed out while fetching routes data", "ERROR")
            self.routesStatusLabel.setText("Request timed out")
        except Exception as e:
            self.log_message(f"Failed to fetch routes data: {str(e)}", "ERROR")
            self.routesStatusLabel.setText("Error fetching data")
    
    def refresh_travel_data(self):
        """Refresh travel assistance data from all travel endpoints"""
        port = self.ui.portSpinBox.value()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch travel data: Server is not running", "WARNING")
            self.travelStatusLabel.setText("Server is not running")
            return
        
        try:
            # Fetch location data
            try:
                url = f"http://localhost:{port}/travel/location"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    location_text = json.dumps(data, indent=2)
                    self.locationText.setPlainText(location_text)
                elif response.status_code == 503:
                    data = response.json()
                    self.locationText.setPlainText(f"Not configured: {data.get('error', 'Unknown error')}")
                else:
                    self.locationText.setPlainText(f"Error: HTTP {response.status_code}")
            except Exception as e:
                self.locationText.setPlainText(f"Error: {str(e)}")
            
            # Fetch distance data
            try:
                url = f"http://localhost:{port}/travel/distance"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    distance_text = json.dumps(data, indent=2)
                    self.distanceText.setPlainText(distance_text)
                elif response.status_code == 503:
                    data = response.json()
                    self.distanceText.setPlainText(f"Not configured: {data.get('error', 'Unknown error')}")
                else:
                    self.distanceText.setPlainText(f"Error: HTTP {response.status_code}")
            except Exception as e:
                self.distanceText.setPlainText(f"Error: {str(e)}")
            
            # Fetch next train data
            try:
                url = f"http://localhost:{port}/travel/next-train"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    next_train_text = json.dumps(data, indent=2)
                    self.nextTrainText.setPlainText(next_train_text)
                elif response.status_code == 503:
                    data = response.json()
                    self.nextTrainText.setPlainText(f"Not configured: {data.get('error', 'Unknown error')}")
                else:
                    self.nextTrainText.setPlainText(f"Error: HTTP {response.status_code}")
            except Exception as e:
                self.nextTrainText.setPlainText(f"Error: {str(e)}")
            
            # Fetch Arduino device data
            try:
                url = f"http://localhost:{port}/travel/arduino-device"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    arduino_text = json.dumps(data, indent=2)
                    self.arduinoText.setPlainText(arduino_text)
                elif response.status_code == 503:
                    data = response.json()
                    self.arduinoText.setPlainText(f"Not configured: {data.get('error', 'Unknown error')}")
                else:
                    self.arduinoText.setPlainText(f"Error: HTTP {response.status_code}")
            except Exception as e:
                self.arduinoText.setPlainText(f"Error: {str(e)}")
            
            # Update status label
            self.travelStatusLabel.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_message("Fetched travel assistance data", "INFO")
            
        except Exception as e:
            self.log_message(f"Failed to fetch travel data: {str(e)}", "ERROR")
            self.travelStatusLabel.setText("Error fetching data")
    
    def refresh_api_info(self):
        """Refresh API information from the root endpoint"""
        port = self.ui.portSpinBox.value()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch API info: Server is not running", "WARNING")
            self.apiInfoStatusLabel.setText("Server is not running")
            return
        
        try:
            # Fetch data from the API
            url = f"http://localhost:{port}/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Format the data nicely
            api_info_text = json.dumps(data, indent=2)
            self.apiInfoText.setPlainText(api_info_text)
            
            # Update status label
            self.apiInfoStatusLabel.setText(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.log_message("Fetched API information", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
            self.apiInfoStatusLabel.setText("Connection error")
        except requests.Timeout:
            self.log_message("Request timed out while fetching API info", "ERROR")
            self.apiInfoStatusLabel.setText("Request timed out")
        except Exception as e:
            self.log_message(f"Failed to fetch API info: {str(e)}", "ERROR")
            self.apiInfoStatusLabel.setText("Error fetching data")
    
    def refresh_vehicle_positions_data(self):
        """Refresh vehicle positions data from the API"""
        port = self.ui.portSpinBox.value()
        limit = self.vehicleLimitSpinBox.value()
        route_filter = self.vehicleRouteEdit.text().strip()
        trip_id_filter = self.vehicleTripIdEdit.text().strip()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch vehicle positions: Server is not running", "WARNING")
            self.vehiclePositionsStatusLabel.setText("Server is not running")
            return
        
        try:
            # Build query parameters
            params = {'limit': limit}
            if route_filter:
                params['route'] = route_filter
            if trip_id_filter:
                params['trip_id'] = trip_id_filter
            
            # Fetch data from the API
            url = f"http://localhost:{port}/vehicle-positions"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            vehicles = data.get('vehicles', [])
            
            # Clear existing data
            self.vehiclePositionsTable.setRowCount(0)
            
            # Add new data
            for vehicle in vehicles:
                row = self.vehiclePositionsTable.rowCount()
                self.vehiclePositionsTable.insertRow(row)
                
                # Vehicle ID
                vehicle_id = vehicle.get('vehicle_id', 'N/A')
                self.vehiclePositionsTable.setItem(row, 0, QTableWidgetItem(str(vehicle_id)))
                
                # Trip ID
                trip_id = vehicle.get('trip_id', 'N/A')
                self.vehiclePositionsTable.setItem(row, 1, QTableWidgetItem(str(trip_id)))
                
                # Route - show route name if available
                route_display = vehicle.get('route_name') if vehicle.get('route_name') else vehicle.get('route_id', 'N/A')
                self.vehiclePositionsTable.setItem(row, 2, QTableWidgetItem(str(route_display)))
                
                # Latitude
                latitude = vehicle.get('latitude', 'N/A')
                self.vehiclePositionsTable.setItem(row, 3, QTableWidgetItem(str(latitude)))
                
                # Longitude
                longitude = vehicle.get('longitude', 'N/A')
                self.vehiclePositionsTable.setItem(row, 4, QTableWidgetItem(str(longitude)))
                
                # Bearing
                bearing = vehicle.get('bearing', 'N/A')
                self.vehiclePositionsTable.setItem(row, 5, QTableWidgetItem(str(bearing)))
                
                # Speed
                speed = vehicle.get('speed', 'N/A')
                self.vehiclePositionsTable.setItem(row, 6, QTableWidgetItem(str(speed)))
                
                # Stop ID - show stop name if available
                stop_display = vehicle.get('stop_name') if vehicle.get('stop_name') else vehicle.get('stop_id', 'N/A')
                self.vehiclePositionsTable.setItem(row, 7, QTableWidgetItem(str(stop_display)))
                
                # Status
                status = vehicle.get('current_status', 'N/A')
                self.vehiclePositionsTable.setItem(row, 8, QTableWidgetItem(str(status)))
            
            # Resize columns to content
            self.vehiclePositionsTable.resizeColumnsToContents()
            
            # Update status label
            timestamp = data.get('timestamp', 'Unknown')
            filters_text = []
            if route_filter:
                filters_text.append(f"route={route_filter}")
            if trip_id_filter:
                filters_text.append(f"trip_id={trip_id_filter}")
            filters_str = f" ({', '.join(filters_text)})" if filters_text else ""
            self.vehiclePositionsStatusLabel.setText(
                f"Last updated: {timestamp} - Total: {len(vehicles)} vehicles{filters_str}"
            )
            self.log_message(f"Fetched {len(vehicles)} vehicle positions", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
            self.vehiclePositionsStatusLabel.setText("Connection error")
        except requests.Timeout:
            self.log_message("Request timed out while fetching vehicle positions", "ERROR")
            self.vehiclePositionsStatusLabel.setText("Request timed out")
        except Exception as e:
            self.log_message(f"Failed to fetch vehicle positions: {str(e)}", "ERROR")
            self.vehiclePositionsStatusLabel.setText("Error fetching data")
    
    def refresh_alerts_data(self):
        """Refresh service alerts data from the API"""
        port = self.ui.portSpinBox.value()
        route_filter = self.alertRouteEdit.text().strip()
        stop_filter = self.alertStopEdit.text().strip()
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch alerts: Server is not running", "WARNING")
            self.alertsStatusLabel.setText("Server is not running")
            return
        
        try:
            # Build query parameters
            params = {}
            if route_filter:
                params['route'] = route_filter
            if stop_filter:
                params['stop'] = stop_filter
            
            # Fetch data from the API
            url = f"http://localhost:{port}/alerts"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('alerts', [])
            
            # Clear existing data
            self.alertsTable.setRowCount(0)
            
            # Add new data
            for alert in alerts:
                row = self.alertsTable.rowCount()
                self.alertsTable.insertRow(row)
                
                # Alert ID
                alert_id = alert.get('alert_id', 'N/A')
                self.alertsTable.setItem(row, 0, QTableWidgetItem(str(alert_id)))
                
                # Header text
                header_text = alert.get('header_text', 'N/A')
                self.alertsTable.setItem(row, 1, QTableWidgetItem(str(header_text)))
                
                # Description text
                description_text = alert.get('description_text', 'N/A')
                desc_item = QTableWidgetItem(str(description_text))
                desc_item.setToolTip(str(description_text))  # Show full text on hover
                self.alertsTable.setItem(row, 2, desc_item)
                
                # Effect
                effect = alert.get('effect', 'N/A')
                effect_item = QTableWidgetItem(str(effect))
                # Color code by effect
                if effect in ['SIGNIFICANT_DELAYS', 'REDUCED_SERVICE']:
                    effect_item.setBackground(QColor(255, 200, 200))  # Light red
                elif effect == 'DETOUR':
                    effect_item.setBackground(QColor(255, 255, 200))  # Light yellow
                elif effect == 'MODIFIED_SERVICE':
                    effect_item.setBackground(QColor(200, 220, 255))  # Light blue
                self.alertsTable.setItem(row, 3, effect_item)
                
                # Informed entities (routes/stops affected)
                informed_entities = alert.get('informed_entities', [])
                entities_text = []
                for entity in informed_entities:
                    if entity.get('route_id'):
                        route_name = entity.get('route_name', entity.get('route_id'))
                        entities_text.append(f"Route: {route_name}")
                    if entity.get('stop_id'):
                        stop_name = entity.get('stop_name', entity.get('stop_id'))
                        entities_text.append(f"Stop: {stop_name}")
                entities_str = '; '.join(entities_text) if entities_text else 'N/A'
                entities_item = QTableWidgetItem(entities_str)
                entities_item.setToolTip(entities_str)  # Show full text on hover
                self.alertsTable.setItem(row, 4, entities_item)
            
            # Resize columns to content
            self.alertsTable.resizeColumnsToContents()
            
            # Update status label
            timestamp = data.get('timestamp', 'Unknown')
            filters_text = []
            if route_filter:
                filters_text.append(f"route={route_filter}")
            if stop_filter:
                filters_text.append(f"stop={stop_filter}")
            filters_str = f" ({', '.join(filters_text)})" if filters_text else ""
            self.alertsStatusLabel.setText(
                f"Last updated: {timestamp} - Total: {len(alerts)} alerts{filters_str}"
            )
            self.log_message(f"Fetched {len(alerts)} alerts", "INFO")
            
        except requests.ConnectionError:
            self.log_message("Cannot connect to server. Is it running?", "ERROR")
            self.alertsStatusLabel.setText("Connection error")
        except requests.Timeout:
            self.log_message("Request timed out while fetching alerts", "ERROR")
            self.alertsStatusLabel.setText("Request timed out")
        except Exception as e:
            self.log_message(f"Failed to fetch alerts: {str(e)}", "ERROR")
            self.alertsStatusLabel.setText("Error fetching data")
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About MNR Real-Time Service Manager",
            "<h3>MNR Real-Time Service Manager</h3>"
            "<p>A GUI application for managing the Metro-North Railroad real-time service.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Server control and configuration</li>"
            "<li>GTFS data management</li>"
            "<li>Real-time train data visualization with filters</li>"
            "<li>Vehicle positions tracking with filters</li>"
            "<li>Service alerts monitoring with filters</li>"
            "<li>Stations and routes viewing</li>"
            "<li>Travel assistance (if configured)</li>"
            "<li>API information</li>"
            "<li>Log monitoring</li>"
            "</ul>"
            "<p>Version 1.1.0</p>"
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.server_thread and self.server_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Server Running",
                "The server is still running. Do you want to stop it and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.stop_server()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
