/**
 * Configuration Template for Metro-North Railroad Train Clock
 * 
 * IMPORTANT: 
 *   1. Copy this file to config.h
 *   2. Update the values below with your settings
 *   3. DO NOT commit config.h to version control (it contains your credentials)
 */

#ifndef CONFIG_H
#define CONFIG_H

// WiFi Configuration
// Replace with your WiFi network credentials
#define WIFI_SSID "Your_WiFi_SSID"
#define WIFI_PASSWORD "Your_WiFi_Password"

// API Endpoint Configuration
// Replace with the URL of your MNR GTFS-RT web service
// 
// Expected endpoint format:
//   - Should return JSON with train data
//   - Example: http://your-server:5000/api/trains
//   - Or: http://192.168.1.100:8080/upcoming-trains
//
// Expected JSON response format:
// {
//   "trains": [
//     {
//       "trip_id": "1234567",
//       "route": "Hudson Line",
//       "destination": "Grand Central Terminal",
//       "track": "5",
//       "arrival_time": "14:30:00",
//       "status": "On Time",
//       "delay_seconds": 0
//     },
//     ...
//   ]
// }
#define API_ENDPOINT "http://192.168.1.100:5000/api/trains"

// Optional: API Key (if your service requires authentication)
// Uncomment and set if needed
// #define API_KEY "your-api-key-here"

#endif // CONFIG_H
