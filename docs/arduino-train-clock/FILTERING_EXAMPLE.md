# Arduino Train Clock - Advanced Filtering Example

This example demonstrates how to use the new API filtering capabilities to create an interactive Arduino train display.

## Hardware Requirements

- Arduino Nano ESP32 (or any ESP32 board)
- 20x4 LCD Display with I2C interface
- 3 push buttons (Up, Down, Select)
- WiFi connection

## Features Demonstrated

1. Fetch and display list of stations
2. User selects home station using buttons
3. User selects destination station
4. User sets time range preferences
5. Display filtered trains matching criteria
6. Select specific train to monitor
7. Display real-time updates for selected train

## Code Example

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// WiFi Configuration
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://192.168.1.100:5000";

// LCD Configuration (20 columns, 4 rows)
LiquidCrystal_I2C lcd(0x27, 20, 4);

// Button pins
const int BTN_UP = 2;
const int BTN_DOWN = 3;
const int BTN_SELECT = 4;

// Application states
enum AppState {
  STATE_SELECT_HOME_STATION,
  STATE_SELECT_DEST_STATION,
  STATE_SELECT_TIME_FROM,
  STATE_SELECT_TIME_TO,
  STATE_SHOW_TRAINS,
  STATE_MONITOR_TRAIN
};

AppState currentState = STATE_SELECT_HOME_STATION;

// Data structures
struct Station {
  String id;
  String name;
  String code;
};

struct Train {
  String tripId;
  String routeName;
  String destination;
  String track;
  String eta;
  String status;
};

// Global variables
Station stations[114];  // Max 114 stations
int stationCount = 0;
int selectedHomeIndex = 0;
int selectedDestIndex = 0;
int timeFromHour = 14;
int timeToHour = 16;

Train filteredTrains[10];
int trainCount = 0;
int selectedTrainIndex = 0;

HTTPClient http;

void setup() {
  Serial.begin(115200);
  
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  lcd.clear();
  
  // Initialize buttons
  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_SELECT, INPUT_PULLUP);
  
  // Connect to WiFi
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  lcd.clear();
  lcd.print("WiFi Connected!");
  Serial.println("\nWiFi connected");
  delay(1000);
  
  // Fetch stations list
  fetchStations();
  
  // Start with home station selection
  currentState = STATE_SELECT_HOME_STATION;
  displayHomeStationSelection();
}

void loop() {
  // Handle button presses
  if (digitalRead(BTN_UP) == LOW) {
    handleUpButton();
    delay(200); // Debounce
  }
  
  if (digitalRead(BTN_DOWN) == LOW) {
    handleDownButton();
    delay(200); // Debounce
  }
  
  if (digitalRead(BTN_SELECT) == LOW) {
    handleSelectButton();
    delay(200); // Debounce
  }
  
  // Update display based on current state
  switch (currentState) {
    case STATE_SHOW_TRAINS:
      // Auto-refresh trains every 30 seconds
      static unsigned long lastUpdate = 0;
      if (millis() - lastUpdate > 30000) {
        fetchFilteredTrains();
        displayTrains();
        lastUpdate = millis();
      }
      break;
      
    case STATE_MONITOR_TRAIN:
      // Auto-refresh specific train every 15 seconds
      static unsigned long lastTrainUpdate = 0;
      if (millis() - lastTrainUpdate > 15000) {
        fetchTrainDetails(filteredTrains[selectedTrainIndex].tripId);
        lastTrainUpdate = millis();
      }
      break;
  }
}

void fetchStations() {
  lcd.clear();
  lcd.print("Fetching stations..");
  
  String url = String(serverUrl) + "/stations";
  http.begin(url);
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON
    DynamicJsonDocument doc(20000);  // Large buffer for 114 stations
    deserializeJson(doc, payload);
    
    JsonArray stationsArray = doc["stations"];
    stationCount = stationsArray.size();
    
    for (int i = 0; i < stationCount && i < 114; i++) {
      stations[i].id = stationsArray[i]["stop_id"].as<String>();
      stations[i].name = stationsArray[i]["stop_name"].as<String>();
      stations[i].code = stationsArray[i]["stop_code"].as<String>();
    }
    
    lcd.clear();
    lcd.print("Loaded ");
    lcd.print(stationCount);
    lcd.print(" stations");
    Serial.println("Stations loaded successfully");
  } else {
    lcd.clear();
    lcd.print("Error loading");
    lcd.setCursor(0, 1);
    lcd.print("stations");
    Serial.println("Failed to fetch stations");
  }
  
  http.end();
  delay(2000);
}

void fetchFilteredTrains() {
  lcd.clear();
  lcd.print("Fetching trains...");
  
  // Build URL with filters
  String url = String(serverUrl) + "/trains?";
  url += "origin_station=" + stations[selectedHomeIndex].id;
  url += "&destination_station=" + stations[selectedDestIndex].id;
  url += "&time_from=" + String(timeFromHour) + ":00";
  url += "&time_to=" + String(timeToHour) + ":00";
  url += "&limit=10";
  
  Serial.println("URL: " + url);
  http.begin(url);
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON
    DynamicJsonDocument doc(8000);
    deserializeJson(doc, payload);
    
    JsonArray trainsArray = doc["trains"];
    trainCount = trainsArray.size();
    
    for (int i = 0; i < trainCount && i < 10; i++) {
      filteredTrains[i].tripId = trainsArray[i]["trip_id"].as<String>();
      filteredTrains[i].routeName = trainsArray[i]["route_name"].as<String>();
      filteredTrains[i].destination = trainsArray[i]["trip_headsign"].as<String>();
      filteredTrains[i].track = trainsArray[i]["track"].as<String>();
      filteredTrains[i].eta = trainsArray[i]["eta"].as<String>();
      filteredTrains[i].status = trainsArray[i]["status"].as<String>();
    }
    
    Serial.println("Found " + String(trainCount) + " trains");
  } else {
    lcd.clear();
    lcd.print("No trains found");
    trainCount = 0;
  }
  
  http.end();
}

void fetchTrainDetails(String tripId) {
  String url = String(serverUrl) + "/train/" + tripId;
  http.begin(url);
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    
    // Parse JSON
    DynamicJsonDocument doc(4000);
    deserializeJson(doc, payload);
    
    JsonObject train = doc["train"];
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print(train["route_name"].as<String>());
    
    lcd.setCursor(0, 1);
    lcd.print("To: ");
    lcd.print(train["trip_headsign"].as<String>());
    
    lcd.setCursor(0, 2);
    lcd.print("Next: ");
    lcd.print(train["next_stop_name"].as<String>());
    
    lcd.setCursor(0, 3);
    lcd.print("Trk ");
    lcd.print(train["track"].as<String>());
    lcd.print(" - ");
    lcd.print(train["status"].as<String>());
    
    // Extract time from ISO format
    String eta = train["eta"].as<String>();
    int timeStart = eta.indexOf('T') + 1;
    String timeStr = eta.substring(timeStart, timeStart + 5);
    
    lcd.setCursor(13, 3);
    lcd.print(timeStr);
  } else {
    lcd.clear();
    lcd.print("Train not found");
  }
  
  http.end();
}

void displayHomeStationSelection() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Select Home Station");
  lcd.setCursor(0, 1);
  lcd.print("------------------");
  lcd.setCursor(0, 2);
  lcd.print(stations[selectedHomeIndex].name);
  lcd.setCursor(0, 3);
  lcd.print("UP/DOWN to scroll");
}

void displayDestStationSelection() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Select Destination");
  lcd.setCursor(0, 1);
  lcd.print("------------------");
  lcd.setCursor(0, 2);
  lcd.print(stations[selectedDestIndex].name);
  lcd.setCursor(0, 3);
  lcd.print("UP/DOWN to scroll");
}

void displayTimeFromSelection() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Select Time From");
  lcd.setCursor(0, 1);
  lcd.print("------------------");
  lcd.setCursor(0, 2);
  lcd.print("     ");
  lcd.print(timeFromHour);
  lcd.print(":00");
  lcd.setCursor(0, 3);
  lcd.print("UP/DOWN to adjust");
}

void displayTimeToSelection() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Select Time To");
  lcd.setCursor(0, 1);
  lcd.print("------------------");
  lcd.setCursor(0, 2);
  lcd.print("     ");
  lcd.print(timeToHour);
  lcd.print(":00");
  lcd.setCursor(0, 3);
  lcd.print("UP/DOWN to adjust");
}

void displayTrains() {
  if (trainCount == 0) {
    lcd.clear();
    lcd.print("No trains found");
    lcd.setCursor(0, 1);
    lcd.print("for this time/route");
    return;
  }
  
  Train& train = filteredTrains[selectedTrainIndex];
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Train ");
  lcd.print(selectedTrainIndex + 1);
  lcd.print("/");
  lcd.print(trainCount);
  lcd.print(" ");
  lcd.print(train.routeName);
  
  lcd.setCursor(0, 1);
  lcd.print("To: ");
  lcd.print(train.destination.substring(0, 16));
  
  lcd.setCursor(0, 2);
  lcd.print("Track: ");
  lcd.print(train.track);
  lcd.print(" ");
  lcd.print(train.status);
  
  lcd.setCursor(0, 3);
  // Extract time from ISO format
  String eta = train.eta;
  int timeStart = eta.indexOf('T') + 1;
  String timeStr = eta.substring(timeStart, timeStart + 5);
  lcd.print("ETA: ");
  lcd.print(timeStr);
  lcd.print(" SEL=Track");
}

void handleUpButton() {
  switch (currentState) {
    case STATE_SELECT_HOME_STATION:
      selectedHomeIndex = (selectedHomeIndex - 1 + stationCount) % stationCount;
      displayHomeStationSelection();
      break;
      
    case STATE_SELECT_DEST_STATION:
      selectedDestIndex = (selectedDestIndex - 1 + stationCount) % stationCount;
      displayDestStationSelection();
      break;
      
    case STATE_SELECT_TIME_FROM:
      timeFromHour = (timeFromHour - 1 + 24) % 24;
      displayTimeFromSelection();
      break;
      
    case STATE_SELECT_TIME_TO:
      timeToHour = (timeToHour - 1 + 24) % 24;
      displayTimeToSelection();
      break;
      
    case STATE_SHOW_TRAINS:
      selectedTrainIndex = (selectedTrainIndex - 1 + trainCount) % trainCount;
      displayTrains();
      break;
  }
}

void handleDownButton() {
  switch (currentState) {
    case STATE_SELECT_HOME_STATION:
      selectedHomeIndex = (selectedHomeIndex + 1) % stationCount;
      displayHomeStationSelection();
      break;
      
    case STATE_SELECT_DEST_STATION:
      selectedDestIndex = (selectedDestIndex + 1) % stationCount;
      displayDestStationSelection();
      break;
      
    case STATE_SELECT_TIME_FROM:
      timeFromHour = (timeFromHour + 1) % 24;
      displayTimeFromSelection();
      break;
      
    case STATE_SELECT_TIME_TO:
      timeToHour = (timeToHour + 1) % 24;
      displayTimeToSelection();
      break;
      
    case STATE_SHOW_TRAINS:
      selectedTrainIndex = (selectedTrainIndex + 1) % trainCount;
      displayTrains();
      break;
  }
}

void handleSelectButton() {
  switch (currentState) {
    case STATE_SELECT_HOME_STATION:
      currentState = STATE_SELECT_DEST_STATION;
      displayDestStationSelection();
      break;
      
    case STATE_SELECT_DEST_STATION:
      currentState = STATE_SELECT_TIME_FROM;
      displayTimeFromSelection();
      break;
      
    case STATE_SELECT_TIME_FROM:
      currentState = STATE_SELECT_TIME_TO;
      displayTimeToSelection();
      break;
      
    case STATE_SELECT_TIME_TO:
      currentState = STATE_SHOW_TRAINS;
      fetchFilteredTrains();
      displayTrains();
      break;
      
    case STATE_SHOW_TRAINS:
      if (trainCount > 0) {
        currentState = STATE_MONITOR_TRAIN;
        fetchTrainDetails(filteredTrains[selectedTrainIndex].tripId);
      }
      break;
      
    case STATE_MONITOR_TRAIN:
      currentState = STATE_SHOW_TRAINS;
      displayTrains();
      break;
  }
}
```

## User Flow

1. **Power On** → Device connects to WiFi and fetches station list
2. **Station Selection** → User scrolls through stations with UP/DOWN buttons
3. **Press SELECT** → Confirms home station, moves to destination selection
4. **Station Selection** → User scrolls through stations for destination
5. **Press SELECT** → Confirms destination, moves to time range selection
6. **Time From** → User adjusts hour with UP/DOWN buttons
7. **Press SELECT** → Confirms start time, moves to end time selection
8. **Time To** → User adjusts hour with UP/DOWN buttons
9. **Press SELECT** → Fetches filtered trains matching criteria
10. **Train List** → User scrolls through matching trains with UP/DOWN
11. **Press SELECT** → Monitors selected train in real-time
12. **Press SELECT** → Returns to train list

## Display Examples

### Home Station Selection
```
Select Home Station
------------------
Grand Central Terminal
UP/DOWN to scroll
```

### Filtered Train Display
```
Train 2/3 Hudson
To: Poughkeepsie
Track: 42 On Time
ETA: 14:45 SEL=Track
```

### Train Monitoring
```
Hudson
To: Poughkeepsie
Next: Harlem-125 St
Trk 42 - On Time 14:45
```

## Features

- **Interactive station selection** from full list of 114 stations
- **Destination filtering** to show only relevant trains
- **Time range filtering** to show trains in user's commute window
- **Real-time monitoring** of selected train with auto-refresh
- **Intuitive navigation** with only 3 buttons
- **Clear display** on 20x4 LCD

## Memory Considerations

- Station list requires ~20KB of RAM (can be reduced by storing only common stations)
- JSON parsing buffers sized appropriately for responses
- Train list limited to 10 trains to save memory
- Consider using SPIFFS to cache station list between restarts

## Future Enhancements

- Add route filtering option
- Save preferences to EEPROM
- Add WiFi Manager for easy configuration
- Add RGB LED status indicators
- Add buzzer alerts for arriving trains
- Display multiple trains simultaneously on larger displays
