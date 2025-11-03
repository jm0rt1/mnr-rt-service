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
    QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem
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
                    self.output_ready.emit(line.rstrip())
                    
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
        
        # Create and start server thread
        self.server_thread = ServerThread(host, port, api_key, debug, skip_gtfs)
        self.server_thread.output_ready.connect(self.log_message)
        self.server_thread.error_ready.connect(lambda msg: self.log_message(msg, "ERROR"))
        self.server_thread.finished.connect(self.on_server_finished)
        self.server_thread.start()
        
        # Update UI
        self.ui.serverStatusValue.setText("Running")
        self.ui.serverStatusValue.setStyleSheet("color: green; font-weight: bold;")
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.restartButton.setEnabled(True)
        
        self.log_message(f"Server started successfully on {host}:{port}", "INFO")
    
    def stop_server(self):
        """Stop the web server"""
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Server is not running", "WARNING")
            return
        
        self.log_message("Stopping server...", "INFO")
        self.server_thread.stop()
        self.server_thread.wait()
        
        # Update UI
        self.ui.serverStatusValue.setText("Stopped")
        self.ui.serverStatusValue.setStyleSheet("color: red; font-weight: bold;")
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
        if exit_code != 0:
            self.log_message(f"Server exited with code {exit_code}", "ERROR")
        else:
            self.log_message("Server exited normally", "INFO")
        
        # Update UI
        self.ui.serverStatusValue.setText("Stopped")
        self.ui.serverStatusValue.setStyleSheet("color: red; font-weight: bold;")
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
        
        # Check if server is running
        if not self.server_thread or not self.server_thread.isRunning():
            self.log_message("Cannot fetch train data: Server is not running", "WARNING")
            return
        
        try:
            # Fetch data from the API
            url = f"http://localhost:{port}/trains?limit={limit}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Update the table
            self.update_train_table(data['trains'])
            
            # Update status label
            timestamp = data.get('timestamp', 'Unknown')
            self.ui.dataStatusLabel.setText(f"Last updated: {timestamp}")
            
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
            route_display = train.get('route_name') or train.get('route_id', 'N/A')
            table.setItem(row, 1, QTableWidgetItem(route_display))
            
            # Current Stop - show stop name if available, otherwise stop ID
            current_stop_display = train.get('current_stop_name') or train.get('current_stop', 'N/A')
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
            "<li>Real-time train data visualization</li>"
            "<li>Log monitoring</li>"
            "</ul>"
            "<p>Version 1.0.0</p>"
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
