# Troubleshooting Guide

## Common Issues and Solutions

### WiFi Connection Problems

#### Issue: Arduino won't connect to WiFi
**Symptoms:**
- Serial output shows "Failed to connect to WiFi"
- Continuous dots without "WiFi connected!" message

**Solutions:**
1. **Verify credentials**
   - Double-check SSID and password in `include/config.h`
   - Ensure no extra spaces or quotes
   - Remember: credentials are case-sensitive

2. **Check WiFi band**
   - ESP32 only supports 2.4GHz WiFi
   - 5GHz networks will NOT work
   - Verify router has 2.4GHz enabled

3. **Check signal strength**
   - Move Arduino closer to router
   - RSSI below -70 dBm may be unstable

4. **Router settings**
   - Ensure WPA2/WPA3 is enabled
   - Disable MAC filtering temporarily
   - Check if router has available DHCP addresses

#### Issue: WiFi keeps disconnecting
**Symptoms:**
- "WiFi disconnected. Reconnecting..." messages

**Solutions:**
1. Improve signal strength (move closer to router)
2. Check for interference (microwaves, cordless phones)
3. Update router firmware
4. Use a WiFi range extender

---

### HTTP Request Problems

#### Issue: HTTP request fails (error code -1)
**Symptoms:**
- "HTTP request error: connection refused"

**Solutions:**
1. **Verify server is running**
   ```bash
   # Test with curl from your computer
   curl http://YOUR_IP:5000/api/trains
   ```

2. **Check network connectivity**
   - Ensure Arduino and server are on same network
   - Or server is accessible from Arduino's network

3. **Verify endpoint URL**
   - Check IP address is correct
   - Ensure port number is correct (default: 5000)
   - Include `http://` prefix (not `https://`)

#### Issue: HTTP 404 Not Found
**Symptoms:**
- "HTTP Response Code: 404"

**Solutions:**
1. Verify endpoint path: `/api/trains`
2. Check server is configured correctly
3. Test endpoint in browser: `http://YOUR_IP:5000/api/trains`

#### Issue: HTTP timeout
**Symptoms:**
- Request hangs for 10 seconds then fails

**Solutions:**
1. Increase timeout in code:
   ```cpp
   http.setTimeout(30000); // 30 seconds
   ```
2. Check server response time
3. Verify network latency

---

### JSON Parsing Problems

#### Issue: "JSON parsing failed"
**Symptoms:**
- Serial shows JSON parsing error message

**Solutions:**
1. **Verify JSON format**
   - Test endpoint in browser
   - Use online JSON validator
   - Ensure response matches expected format

2. **Check JSON size**
   - Large responses may exceed buffer
   - Reduce number of trains returned
   - Note: ArduinoJson v6 auto-allocates, but v7 requires explicit size:
   ```cpp
   // For ArduinoJson v7 (if upgrading):
   JsonDocument doc(4096); // Specify size
   ```

3. **Server-side issues**
   - Check server logs for errors
   - Verify server returns valid JSON
   - Test with curl: `curl -v http://YOUR_IP:5000/api/trains`

---

### Display Problems

#### Issue: No output in Serial Monitor
**Symptoms:**
- Serial monitor is blank

**Solutions:**
1. **Check baud rate**
   - Must be set to 115200
   - Match the rate in code: `Serial.begin(115200);`

2. **Check USB connection**
   - Try different USB cable
   - Try different USB port
   - Ensure board is powered

3. **Verify upload**
   - Re-upload the sketch
   - Check for upload errors
   - Press reset button on Arduino

#### Issue: Garbled text in Serial Monitor
**Symptoms:**
- Random characters, symbols

**Solutions:**
1. Set correct baud rate: 115200
2. Close and reopen serial monitor
3. Reset Arduino board

---

### Build/Upload Problems

#### Issue: Upload fails
**Symptoms:**
- PlatformIO can't upload to board

**Solutions:**
1. **Check board connection**
   - Verify USB cable is data cable (not charge-only)
   - Try different USB port
   - Check Device Manager (Windows) or `ls /dev/tty*` (Mac/Linux)

2. **Install drivers**
   - Download CP210x drivers
   - Install and restart computer

3. **Try manual reset**
   - Hold BOOT button
   - Press and release RESET button
   - Release BOOT button
   - Immediately upload

#### Issue: Compilation errors
**Symptoms:**
- Build fails with error messages

**Solutions:**
1. **Check PlatformIO installation**
   ```bash
   pio --version
   ```

2. **Update platform**
   ```bash
   pio platform update espressif32
   ```

3. **Clean and rebuild**
   ```bash
   pio run -t clean
   pio run
   ```

4. **Verify platformio.ini**
   - Check board name is correct
   - Verify library versions

#### Issue: Missing config.h
**Symptoms:**
- "config.h: No such file or directory"

**Solutions:**
1. Copy the example config:
   ```bash
   cp include/config.example.h include/config.h
   ```
2. Edit with your settings
3. Rebuild

---

### API/Server Problems

#### Issue: Server returns empty trains array
**Symptoms:**
- "No upcoming trains scheduled"
- JSON: `{"trains": []}`

**Solutions:**
1. **Check MTA API status**
   - MTA API may be down
   - Check MTA developer status page

2. **Verify server configuration**
   - Check server logs
   - Ensure GTFS client is working
   - Test with mock server instead

3. **Check time of day**
   - May be no scheduled trains
   - Try different time

#### Issue: Mock server won't start
**Symptoms:**
- "Address already in use"

**Solutions:**
1. **Port already in use**
   ```bash
   # Find and kill process using port 5000
   # On Linux/Mac:
   lsof -ti:5000 | xargs kill -9
   
   # On Windows:
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

2. **Use different port**
   - Edit server code to use port 8000
   - Update Arduino config.h with new port

---

### Performance Issues

#### Issue: Slow updates
**Symptoms:**
- Updates take longer than expected

**Solutions:**
1. **Check update interval**
   - Default is 30 seconds
   - Configured in: `UPDATE_INTERVAL`

2. **Network latency**
   - Use `ping` to check network speed
   - Consider wired connection for server

3. **Server performance**
   - Check server CPU usage
   - Enable caching on server

#### Issue: High memory usage
**Symptoms:**
- Board resets randomly
- Crashes during JSON parsing

**Solutions:**
1. **Reduce JSON buffer**
   - Request fewer trains
   - Parse incrementally

2. **Optimize code**
   - Remove debug prints
   - Free unused memory

3. **Check for memory leaks**
   - Monitor free heap: `ESP.getFreeHeap()`

---

### Development Issues

#### Issue: Changes not taking effect
**Symptoms:**
- Code changes don't appear after upload

**Solutions:**
1. **Clean build**
   ```bash
   pio run -t clean
   pio run -t upload
   ```

2. **Verify file is saved**
   - Check file has no asterisk (*) in editor

3. **Hard reset board**
   - Disconnect USB
   - Wait 5 seconds
   - Reconnect

#### Issue: Library not found
**Symptoms:**
- "library not found" error

**Solutions:**
1. **Update dependencies**
   ```bash
   pio lib update
   ```

2. **Install manually**
   ```bash
   pio lib install "bblanchon/ArduinoJson@^6.21.3"
   ```
   Note: Version must match platformio.ini specification

---

## Diagnostic Commands

### Test WiFi connectivity
```cpp
// Add to loop() for debugging
Serial.print("WiFi Status: ");
Serial.println(WiFi.status());
Serial.print("RSSI: ");
Serial.println(WiFi.RSSI());
```

### Test HTTP endpoint
```bash
# From computer on same network
curl -v http://YOUR_IP:5000/api/trains

# Expected response:
# HTTP/1.1 200 OK
# Content-Type: application/json
# {"trains": [...]}
```

### Check memory usage
```cpp
// Add to setup() or loop()
Serial.print("Free heap: ");
Serial.println(ESP.getFreeHeap());
```

### Enable verbose debugging
```ini
# In platformio.ini
build_flags = 
    -D CORE_DEBUG_LEVEL=5  ; Maximum verbosity
```

---

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check serial output**
   - Copy full serial output
   - Look for error messages

2. **Test with mock server**
   - Verify Arduino code works
   - Isolates API/server issues

3. **Minimal test case**
   - Start with simple WiFi connection
   - Add features incrementally

4. **Documentation**
   - Review README.md
   - Check ARCHITECTURE.md
   - Read library documentation

5. **Community support**
   - PlatformIO forums
   - Arduino forums
   - ESP32 community

---

## Useful Links

- [PlatformIO Troubleshooting](https://docs.platformio.org/en/latest/faq.html)
- [ESP32 Arduino Core Issues](https://github.com/espressif/arduino-esp32/issues)
- [ArduinoJson Troubleshooter](https://arduinojson.org/v6/troubleshooter/)
- [ESP32 Forum](https://esp32.com/)
