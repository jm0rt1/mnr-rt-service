# Quick Start Guide

## 1. Hardware Setup

### Arduino Nano ESP32
- Connect Arduino Nano ESP32 to your computer via USB
- No additional wiring needed for basic serial monitor display

### Future: LCD Display (Optional)
If you want to add an LCD display later:
- I2C LCD (16x2 or 20x4)
  - VCC → 5V
  - GND → GND  
  - SDA → A4 (GPIO 21)
  - SCL → A5 (GPIO 22)

## 2. Software Setup

### Install PlatformIO
1. Download and install [VS Code](https://code.visualstudio.com/)
2. Open VS Code
3. Go to Extensions (Ctrl+Shift+X)
4. Search for "PlatformIO IDE"
5. Click Install

### Open Project
1. Open VS Code
2. File → Open Folder
3. Navigate to `docs/arduino-train-clock`
4. PlatformIO will auto-detect the project

## 3. Configure WiFi and API

1. Copy configuration template:
   ```bash
   cp include/config.example.h include/config.h
   ```

2. Edit `include/config.h`:
   - Set your WiFi SSID and password
   - Set your API endpoint URL

## 4. Setup Test Server (Optional)

For testing without a real server:

```bash
# Install Flask
pip install flask

# Run mock server
python mock_train_server.py
```

Find your computer's IP address:
- Windows: `ipconfig`
- Mac/Linux: `ifconfig` or `ip addr`

Update `config.h` with: `http://YOUR_IP:5000/api/trains`

## 5. Build and Upload

### Using PlatformIO IDE (VS Code)
1. Connect Arduino via USB
2. Click the "Upload" button (→) in the bottom toolbar
3. Wait for compile and upload to complete

### Using PlatformIO CLI
```bash
cd docs/arduino-train-clock
pio run -t upload
```

## 6. View Output

1. Click "Serial Monitor" button in PlatformIO toolbar
2. Or use CLI: `pio device monitor`
3. Set baud rate to 115200
4. Watch for train updates!

## Troubleshooting

### Can't upload to board
- Check USB cable is connected
- Try a different USB port
- Install [USB drivers](https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers)

### WiFi won't connect
- Verify SSID and password
- Make sure you're using 2.4GHz WiFi (not 5GHz)
- Check signal strength

### No train data
- Verify API endpoint URL is correct
- Check server is running: visit URL in browser
- Make sure Arduino and server are on same network

## Next Steps

- Add LCD display for visual output
- Modify code to filter specific routes or destinations
- Add LED indicators for train status
- Implement OTA updates for easier maintenance
