/**
 * Metro-North Railroad Train Clock
 * 
 * This Arduino sketch fetches real-time train information from the MNR GTFS-RT
 * web service and displays upcoming trains on the serial monitor.
 * 
 * Hardware:
 *   - Arduino Nano ESP32
 *   - Optional: LCD display (future enhancement)
 * 
 * Setup:
 *   1. Copy config.example.h to config.h
 *   2. Update WiFi credentials in config.h
 *   3. Update API endpoint in config.h
 *   4. Build and upload with PlatformIO
 * 
 * Usage:
 *   - Connect via serial monitor at 115200 baud
 *   - Watch for train updates every 30 seconds
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "config.h"

// Configuration (see config.h)
const char* ssid = WIFI_SSID;
const char* password = WIFI_PASSWORD;
const char* apiEndpoint = API_ENDPOINT;

// Update interval (milliseconds)
const unsigned long UPDATE_INTERVAL = 30000; // 30 seconds
unsigned long lastUpdate = 0;

// Function prototypes
void connectWiFi();
void fetchTrainData();
void displayTrainInfo(JsonDocument& doc);
void printWiFiStatus();

/**
 * Setup function - runs once at startup
 */
void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // Wait for serial port to connect
  }
  
  Serial.println("\n\n=================================");
  Serial.println("Metro-North Railroad Train Clock");
  Serial.println("=================================\n");
  
  // Connect to WiFi
  connectWiFi();
  
  // Perform initial data fetch
  fetchTrainData();
  lastUpdate = millis();
}

/**
 * Main loop - runs continuously
 */
void loop() {
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    connectWiFi();
  }
  
  // Update train data at regular intervals
  if (millis() - lastUpdate >= UPDATE_INTERVAL) {
    fetchTrainData();
    lastUpdate = millis();
  }
  
  // Small delay to prevent excessive CPU usage
  delay(100);
}

/**
 * Connect to WiFi network
 */
void connectWiFi() {
  Serial.print("Connecting to WiFi network: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 40) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    printWiFiStatus();
  } else {
    Serial.println("\nFailed to connect to WiFi");
    Serial.println("Please check credentials in config.h");
  }
}

/**
 * Print WiFi connection status
 */
void printWiFiStatus() {
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Signal Strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.println();
}

/**
 * Fetch train data from the API endpoint
 */
void fetchTrainData() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot fetch data: WiFi not connected");
    return;
  }
  
  Serial.println("\n--- Fetching Train Data ---");
  Serial.print("Endpoint: ");
  Serial.println(apiEndpoint);
  
  HTTPClient http;
  http.begin(apiEndpoint);
  http.setTimeout(10000); // 10 second timeout
  
  // Add headers if needed
  http.addHeader("Accept", "application/json");
  
  // Send GET request
  int httpCode = http.GET();
  
  if (httpCode > 0) {
    Serial.print("HTTP Response Code: ");
    Serial.println(httpCode);
    
    if (httpCode == HTTP_CODE_OK) {
      String payload = http.getString();
      
      // Parse JSON response
      JsonDocument doc;
      DeserializationError error = deserializeJson(doc, payload);
      
      if (error) {
        Serial.print("JSON parsing failed: ");
        Serial.println(error.c_str());
      } else {
        displayTrainInfo(doc);
      }
    } else {
      Serial.println("HTTP request failed");
    }
  } else {
    Serial.print("HTTP request error: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
}

/**
 * Display train information from JSON data
 * 
 * Expected JSON format (example):
 * {
 *   "trains": [
 *     {
 *       "trip_id": "123",
 *       "route": "Hudson Line",
 *       "destination": "Grand Central",
 *       "track": "5",
 *       "arrival_time": "14:30",
 *       "status": "On Time",
 *       "delay_seconds": 0
 *     }
 *   ]
 * }
 */
void displayTrainInfo(JsonDocument& doc) {
  Serial.println("\n╔═══════════════════════════════════════════════════════════╗");
  Serial.println("║           METRO-NORTH RAILROAD - UPCOMING TRAINS          ║");
  Serial.println("╚═══════════════════════════════════════════════════════════╝\n");
  
  // Check if trains array exists
  if (!doc.containsKey("trains")) {
    Serial.println("No train data available");
    Serial.println("\nNote: Ensure your web server provides JSON in the format:");
    Serial.println("  { \"trains\": [ { \"trip_id\": \"...\", \"route\": \"...\", ... } ] }");
    return;
  }
  
  JsonArray trains = doc["trains"];
  
  if (trains.size() == 0) {
    Serial.println("No upcoming trains scheduled");
    return;
  }
  
  // Display each train
  int count = 0;
  for (JsonObject train : trains) {
    count++;
    
    // Extract train information
    const char* trip_id = train["trip_id"] | "N/A";
    const char* route = train["route"] | "Unknown Route";
    const char* destination = train["destination"] | "Unknown";
    const char* track = train["track"] | "TBD";
    const char* arrival_time = train["arrival_time"] | "N/A";
    const char* status = train["status"] | "Unknown";
    int delay_seconds = train["delay_seconds"] | 0;
    
    // Format and display
    Serial.println("┌───────────────────────────────────────────────────────────┐");
    Serial.print("│ Train #");
    Serial.print(count);
    Serial.print(" - ");
    Serial.print(route);
    
    // Pad to align the right border
    int padding = 50 - strlen(route) - 12;
    for (int i = 0; i < padding; i++) Serial.print(" ");
    Serial.println("│");
    
    Serial.println("├───────────────────────────────────────────────────────────┤");
    
    // Destination
    Serial.print("│ → Destination:  ");
    Serial.print(destination);
    padding = 44 - strlen(destination);
    for (int i = 0; i < padding; i++) Serial.print(" ");
    Serial.println("│");
    
    // Track
    Serial.print("│   Track:        ");
    Serial.print(track);
    padding = 44 - strlen(track);
    for (int i = 0; i < padding; i++) Serial.print(" ");
    Serial.println("│");
    
    // Arrival time
    Serial.print("│   Arrival:      ");
    Serial.print(arrival_time);
    padding = 44 - strlen(arrival_time);
    for (int i = 0; i < padding; i++) Serial.print(" ");
    Serial.println("│");
    
    // Status
    Serial.print("│   Status:       ");
    Serial.print(status);
    
    // Add delay information if applicable
    if (delay_seconds > 0) {
      Serial.print(" (+");
      Serial.print(delay_seconds / 60);
      Serial.print(" min)");
      padding = 44 - strlen(status) - 8 - (delay_seconds >= 600 ? 1 : 0);
    } else {
      padding = 44 - strlen(status);
    }
    
    for (int i = 0; i < padding; i++) Serial.print(" ");
    Serial.println("│");
    
    Serial.println("└───────────────────────────────────────────────────────────┘");
    Serial.println();
  }
  
  Serial.print("Total trains: ");
  Serial.println(count);
  Serial.print("Last updated: ");
  Serial.print(millis() / 1000);
  Serial.println(" seconds since boot");
  Serial.println();
}
