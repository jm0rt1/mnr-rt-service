import os
import sys
import json
from typing import Optional
from datetime import datetime
import requests
from PySide6.QtCore import Qt, QTimer, QProcess, QSize
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFileDialog, QMessageBox
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MNR Real-Time Service - Control Panel")
        self.resize(1100, 780)

        self.server_process: Optional[QProcess] = None
        self.server_running = False

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- Server Controls
        controls = QGroupBox("Web Server Controls")
        c_layout = QHBoxLayout()
        controls.setLayout(c_layout)

        self.host_edit = QLineEdit("0.0.0.0")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5000)
        self.api_key_edit = QLineEdit("")
        self.api_key_edit.setPlaceholderText("Optional MTA API Key")
        self.debug_check = QCheckBox("Debug")

        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.restart_btn = QPushButton("Restart")
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

        c_layout.addWidget(QLabel("Host:"))
        c_layout.addWidget(self.host_edit)
        c_layout.addWidget(QLabel("Port:"))
        c_layout.addWidget(self.port_spin)
        c_layout.addWidget(QLabel("API Key:"))
        c_layout.addWidget(self.api_key_edit)
        c_layout.addWidget(self.debug_check)
        c_layout.addWidget(self.start_btn)
        c_layout.addWidget(self.stop_btn)
        c_layout.addWidget(self.restart_btn)

        root.addWidget(controls)

        # --- Logs
        logs_group = QGroupBox("Server Output / Errors")
        logs_layout = QVBoxLayout()
        logs_group.setLayout(logs_layout)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        logs_layout.addWidget(self.log_view)

        root.addWidget(logs_group, 2)

        # --- Trains Data Viewer
        api_group = QGroupBox("Trains Data (from /trains)")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)

        top_bar = QHBoxLayout()
        self.server_url_edit = QLineEdit(
            "http://127.0.0.1:5000/trains?city=mnr&limit=20")
        self.refresh_btn = QPushButton("Refresh")
        self.auto_refresh_check = QCheckBox("Auto refresh (10s)")
        top_bar.addWidget(QLabel("Endpoint:"))
        top_bar.addWidget(self.server_url_edit)
        top_bar.addWidget(self.refresh_btn)
        top_bar.addWidget(self.auto_refresh_check)
        api_layout.addLayout(top_bar)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "trip_id", "route_id", "current_stop", "next_stop",
            "eta", "track", "status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        api_layout.addWidget(self.table)

        root.addWidget(api_group, 3)

        # Menu actions
        self._setup_menu()

        # Signals
        self.start_btn.clicked.connect(self.start_server)
        self.stop_btn.clicked.connect(self.stop_server)
        self.restart_btn.clicked.connect(self.restart_server)
        self.refresh_btn.clicked.connect(self.fetch_trains)
        self.auto_refresh_check.toggled.connect(self.on_auto_refresh)

        # Timers
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(10_000)
        self.refresh_timer.timeout.connect(self.fetch_trains)

    # ----- Menu
    def _setup_menu(self):
        m_file = self.menuBar().addMenu("File")
        act_open_logs = QAction("Open Log File...", self)
        act_open_logs.triggered.connect(self.open_log_file)
        m_file.addAction(act_open_logs)

        m_server = self.menuBar().addMenu("Server")
        m_server.addAction("Start", self.start_server)
        m_server.addAction("Stop", self.stop_server)
        m_server.addAction("Restart", self.restart_server)

        m_help = self.menuBar().addMenu("Help")
        m_help.addAction("About", self.show_about)

    # ----- Server process mgmt
    def start_server(self):
        if self.server_running:
            return
        self.log_view.append("Starting server...\n")
        self.server_process = QProcess(self)
        self.server_process.setProcessChannelMode(QProcess.MergedChannels)
        self.server_process.readyReadStandardOutput.connect(
            self.on_server_output)
        self.server_process.finished.connect(self.on_server_finished)

        # Prepare command
        py = sys.executable
        script = os.path.abspath(os.path.join(os.getcwd(), "web_server.py"))
        args = [script, "--host", self.host_edit.text(), "--port",
                str(self.port_spin.value())]
        if self.api_key_edit.text().strip():
            args += ["--api-key", self.api_key_edit.text().strip()]
        if self.debug_check.isChecked():
            args += ["--debug"]

        self.server_process.start(py, args)
        if not self.server_process.waitForStarted(5000):
            QMessageBox.critical(
                self, "Error", "Failed to start web_server.py")
            return

        self.server_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

    def stop_server(self):
        if not self.server_running or not self.server_process:
            return
        self.log_view.append("Stopping server...\n")
        self.server_process.terminate()
        if not self.server_process.waitForFinished(3000):
            self.server_process.kill()
            self.server_process.waitForFinished(2000)
        self.server_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)

    def restart_server(self):
        self.stop_server()
        self.start_server()

    def on_server_output(self):
        if not self.server_process:
            return
        data = self.server_process.readAllStandardOutput(
        ).data().decode("utf-8", errors="replace")
        if data:
            self.log_view.append(data)

    def on_server_finished(self):
        self.server_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.log_view.append("Server stopped.\n")

    # ----- Logs
    def open_log_file(self):
        # Try the known global log location first
        candidate = os.path.join(
            os.getcwd(), "output", "logs", "global", "global.log")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", candidate, "Log files (*.log *.txt);;All files (*.*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    self.log_view.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to open log file:\n{e}")

    # ----- Trains fetch + view
    def on_auto_refresh(self, checked: bool):
        if checked:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def fetch_trains(self):
        url = self.server_url_edit.text().strip()
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            trains = data.get("trains", [])
            self.populate_table(trains)
            self.statusBar().showMessage(
                f"Fetched {len(trains)} trains at {datetime.now().strftime('%H:%M:%S')}", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"Fetch failed: {e}", 5000)
            self.log_view.append(f"\n[Fetch error] {e}\n")

    def populate_table(self, trains):
        self.table.setRowCount(0)
        for t in trains:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(
                str(t.get("trip_id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(
                str(t.get("route_id", ""))))
            self.table.setItem(row, 2, QTableWidgetItem(
                str(t.get("current_stop", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(
                str(t.get("next_stop", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(str(t.get("eta", ""))))
            self.table.setItem(
                row, 5, QTableWidgetItem(str(t.get("track", ""))))
            self.table.setItem(row, 6, QTableWidgetItem(
                str(t.get("status", ""))))

    # ----- Misc
    def show_about(self):
        QMessageBox.information(
            self, "About", "MNR Real-Time Service\nGUI control panel built with PySide6.")
