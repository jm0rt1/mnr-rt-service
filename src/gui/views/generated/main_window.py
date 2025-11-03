# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMainWindow, QMenu,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1200, 800)
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.serverTab = QWidget()
        self.serverTab.setObjectName(u"serverTab")
        self.verticalLayout_2 = QVBoxLayout(self.serverTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.serverControlGroup = QGroupBox(self.serverTab)
        self.serverControlGroup.setObjectName(u"serverControlGroup")
        self.gridLayout = QGridLayout(self.serverControlGroup)
        self.gridLayout.setObjectName(u"gridLayout")
        self.serverStatusLabel = QLabel(self.serverControlGroup)
        self.serverStatusLabel.setObjectName(u"serverStatusLabel")

        self.gridLayout.addWidget(self.serverStatusLabel, 0, 0, 1, 1)

        self.serverStatusValue = QLabel(self.serverControlGroup)
        self.serverStatusValue.setObjectName(u"serverStatusValue")
        self.serverStatusValue.setStyleSheet(u"font-weight: bold;")

        self.gridLayout.addWidget(self.serverStatusValue, 0, 1, 1, 1)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.startButton = QPushButton(self.serverControlGroup)
        self.startButton.setObjectName(u"startButton")

        self.horizontalLayout.addWidget(self.startButton)

        self.stopButton = QPushButton(self.serverControlGroup)
        self.stopButton.setObjectName(u"stopButton")
        self.stopButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.stopButton)

        self.restartButton = QPushButton(self.serverControlGroup)
        self.restartButton.setObjectName(u"restartButton")
        self.restartButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.restartButton)


        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 2)


        self.verticalLayout_2.addWidget(self.serverControlGroup)

        self.configGroup = QGroupBox(self.serverTab)
        self.configGroup.setObjectName(u"configGroup")
        self.formLayout = QFormLayout(self.configGroup)
        self.formLayout.setObjectName(u"formLayout")
        self.hostLabel = QLabel(self.configGroup)
        self.hostLabel.setObjectName(u"hostLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.hostLabel)

        self.hostEdit = QLineEdit(self.configGroup)
        self.hostEdit.setObjectName(u"hostEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.hostEdit)

        self.portLabel = QLabel(self.configGroup)
        self.portLabel.setObjectName(u"portLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.portLabel)

        self.portSpinBox = QSpinBox(self.configGroup)
        self.portSpinBox.setObjectName(u"portSpinBox")
        self.portSpinBox.setMinimum(1024)
        self.portSpinBox.setMaximum(65535)
        self.portSpinBox.setValue(5000)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.portSpinBox)

        self.apiKeyLabel = QLabel(self.configGroup)
        self.apiKeyLabel.setObjectName(u"apiKeyLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.apiKeyLabel)

        self.apiKeyEdit = QLineEdit(self.configGroup)
        self.apiKeyEdit.setObjectName(u"apiKeyEdit")
        self.apiKeyEdit.setEchoMode(QLineEdit.Password)

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.apiKeyEdit)

        self.debugLabel = QLabel(self.configGroup)
        self.debugLabel.setObjectName(u"debugLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.debugLabel)

        self.debugCheckBox = QCheckBox(self.configGroup)
        self.debugCheckBox.setObjectName(u"debugCheckBox")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.debugCheckBox)

        self.skipGtfsLabel = QLabel(self.configGroup)
        self.skipGtfsLabel.setObjectName(u"skipGtfsLabel")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.skipGtfsLabel)

        self.skipGtfsCheckBox = QCheckBox(self.configGroup)
        self.skipGtfsCheckBox.setObjectName(u"skipGtfsCheckBox")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.skipGtfsCheckBox)

        self.applyConfigButton = QPushButton(self.configGroup)
        self.applyConfigButton.setObjectName(u"applyConfigButton")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.applyConfigButton)


        self.verticalLayout_2.addWidget(self.configGroup)

        self.gtfsGroup = QGroupBox(self.serverTab)
        self.gtfsGroup.setObjectName(u"gtfsGroup")
        self.verticalLayout_4 = QVBoxLayout(self.gtfsGroup)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.gtfsInfoLabel = QLabel(self.gtfsGroup)
        self.gtfsInfoLabel.setObjectName(u"gtfsInfoLabel")

        self.verticalLayout_4.addWidget(self.gtfsInfoLabel)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.updateGtfsButton = QPushButton(self.gtfsGroup)
        self.updateGtfsButton.setObjectName(u"updateGtfsButton")

        self.horizontalLayout_3.addWidget(self.updateGtfsButton)

        self.forceUpdateGtfsButton = QPushButton(self.gtfsGroup)
        self.forceUpdateGtfsButton.setObjectName(u"forceUpdateGtfsButton")

        self.horizontalLayout_3.addWidget(self.forceUpdateGtfsButton)


        self.verticalLayout_4.addLayout(self.horizontalLayout_3)


        self.verticalLayout_2.addWidget(self.gtfsGroup)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.serverTab, "")
        self.logsTab = QWidget()
        self.logsTab.setObjectName(u"logsTab")
        self.verticalLayout_3 = QVBoxLayout(self.logsTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.clearLogsButton = QPushButton(self.logsTab)
        self.clearLogsButton.setObjectName(u"clearLogsButton")

        self.horizontalLayout_2.addWidget(self.clearLogsButton)

        self.saveLogsButton = QPushButton(self.logsTab)
        self.saveLogsButton.setObjectName(u"saveLogsButton")

        self.horizontalLayout_2.addWidget(self.saveLogsButton)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer)

        self.autoScrollCheckBox = QCheckBox(self.logsTab)
        self.autoScrollCheckBox.setObjectName(u"autoScrollCheckBox")
        self.autoScrollCheckBox.setChecked(True)

        self.horizontalLayout_2.addWidget(self.autoScrollCheckBox)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)

        self.logsTextEdit = QTextEdit(self.logsTab)
        self.logsTextEdit.setObjectName(u"logsTextEdit")
        self.logsTextEdit.setReadOnly(True)

        self.verticalLayout_3.addWidget(self.logsTextEdit)

        self.tabWidget.addTab(self.logsTab, "")
        self.dataTab = QWidget()
        self.dataTab.setObjectName(u"dataTab")
        self.verticalLayout_5 = QVBoxLayout(self.dataTab)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.limitLabel = QLabel(self.dataTab)
        self.limitLabel.setObjectName(u"limitLabel")

        self.horizontalLayout_4.addWidget(self.limitLabel)

        self.trainLimitSpinBox = QSpinBox(self.dataTab)
        self.trainLimitSpinBox.setObjectName(u"trainLimitSpinBox")
        self.trainLimitSpinBox.setMinimum(1)
        self.trainLimitSpinBox.setMaximum(100)
        self.trainLimitSpinBox.setValue(20)

        self.horizontalLayout_4.addWidget(self.trainLimitSpinBox)

        self.refreshDataButton = QPushButton(self.dataTab)
        self.refreshDataButton.setObjectName(u"refreshDataButton")

        self.horizontalLayout_4.addWidget(self.refreshDataButton)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.autoRefreshCheckBox = QCheckBox(self.dataTab)
        self.autoRefreshCheckBox.setObjectName(u"autoRefreshCheckBox")

        self.horizontalLayout_4.addWidget(self.autoRefreshCheckBox)


        self.verticalLayout_5.addLayout(self.horizontalLayout_4)

        self.dataStatusLabel = QLabel(self.dataTab)
        self.dataStatusLabel.setObjectName(u"dataStatusLabel")

        self.verticalLayout_5.addWidget(self.dataStatusLabel)

        self.trainTableWidget = QTableWidget(self.dataTab)
        if (self.trainTableWidget.columnCount() < 7):
            self.trainTableWidget.setColumnCount(7)
        __qtablewidgetitem = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(4, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(5, __qtablewidgetitem5)
        __qtablewidgetitem6 = QTableWidgetItem()
        self.trainTableWidget.setHorizontalHeaderItem(6, __qtablewidgetitem6)
        self.trainTableWidget.setObjectName(u"trainTableWidget")
        self.trainTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.trainTableWidget.setAlternatingRowColors(True)
        self.trainTableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trainTableWidget.setSortingEnabled(True)

        self.verticalLayout_5.addWidget(self.trainTableWidget)

        self.tabWidget.addTab(self.dataTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1200, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuHelp = QMenu(self.menubar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionExit)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MNR Real-Time Service Manager", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.serverControlGroup.setTitle(QCoreApplication.translate("MainWindow", u"Server Control", None))
        self.serverStatusLabel.setText(QCoreApplication.translate("MainWindow", u"Server Status:", None))
        self.serverStatusValue.setText(QCoreApplication.translate("MainWindow", u"Stopped", None))
        self.startButton.setText(QCoreApplication.translate("MainWindow", u"Start Server", None))
        self.stopButton.setText(QCoreApplication.translate("MainWindow", u"Stop Server", None))
        self.restartButton.setText(QCoreApplication.translate("MainWindow", u"Restart Server", None))
        self.configGroup.setTitle(QCoreApplication.translate("MainWindow", u"Server Configuration", None))
        self.hostLabel.setText(QCoreApplication.translate("MainWindow", u"Host:", None))
        self.hostEdit.setText(QCoreApplication.translate("MainWindow", u"0.0.0.0", None))
        self.portLabel.setText(QCoreApplication.translate("MainWindow", u"Port:", None))
        self.apiKeyLabel.setText(QCoreApplication.translate("MainWindow", u"MTA API Key:", None))
        self.apiKeyEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Optional", None))
        self.debugLabel.setText(QCoreApplication.translate("MainWindow", u"Debug Mode:", None))
        self.debugCheckBox.setText(QCoreApplication.translate("MainWindow", u"Enable Debug Mode", None))
        self.skipGtfsLabel.setText(QCoreApplication.translate("MainWindow", u"GTFS Update:", None))
        self.skipGtfsCheckBox.setText(QCoreApplication.translate("MainWindow", u"Skip GTFS update on startup", None))
        self.applyConfigButton.setText(QCoreApplication.translate("MainWindow", u"Apply Configuration", None))
        self.gtfsGroup.setTitle(QCoreApplication.translate("MainWindow", u"GTFS Data Management", None))
        self.gtfsInfoLabel.setText(QCoreApplication.translate("MainWindow", u"Last Download: Never", None))
        self.updateGtfsButton.setText(QCoreApplication.translate("MainWindow", u"Update GTFS Data Now", None))
        self.forceUpdateGtfsButton.setText(QCoreApplication.translate("MainWindow", u"Force Update (Bypass Rate Limit)", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.serverTab), QCoreApplication.translate("MainWindow", u"Server Control", None))
        self.clearLogsButton.setText(QCoreApplication.translate("MainWindow", u"Clear Logs", None))
        self.saveLogsButton.setText(QCoreApplication.translate("MainWindow", u"Save Logs", None))
        self.autoScrollCheckBox.setText(QCoreApplication.translate("MainWindow", u"Auto-scroll", None))
        self.logsTextEdit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Server logs and errors will appear here...", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.logsTab), QCoreApplication.translate("MainWindow", u"Logs & Errors", None))
        self.limitLabel.setText(QCoreApplication.translate("MainWindow", u"Train Limit:", None))
        self.refreshDataButton.setText(QCoreApplication.translate("MainWindow", u"Refresh Train Data", None))
        self.autoRefreshCheckBox.setText(QCoreApplication.translate("MainWindow", u"Auto-refresh (30s)", None))
        self.dataStatusLabel.setText(QCoreApplication.translate("MainWindow", u"Last updated: Never", None))
        ___qtablewidgetitem = self.trainTableWidget.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MainWindow", u"Trip ID", None));
        ___qtablewidgetitem1 = self.trainTableWidget.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MainWindow", u"Route", None));
        ___qtablewidgetitem2 = self.trainTableWidget.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("MainWindow", u"Current Stop", None));
        ___qtablewidgetitem3 = self.trainTableWidget.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("MainWindow", u"Next Stop", None));
        ___qtablewidgetitem4 = self.trainTableWidget.horizontalHeaderItem(4)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("MainWindow", u"ETA", None));
        ___qtablewidgetitem5 = self.trainTableWidget.horizontalHeaderItem(5)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("MainWindow", u"Track", None));
        ___qtablewidgetitem6 = self.trainTableWidget.horizontalHeaderItem(6)
        ___qtablewidgetitem6.setText(QCoreApplication.translate("MainWindow", u"Status", None));
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.dataTab), QCoreApplication.translate("MainWindow", u"Train Data Visualization", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

