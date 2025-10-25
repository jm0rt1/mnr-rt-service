# MNR Real-Time Service - Quick Start

A simple web server that provides real-time Metro-North Railroad (MNR) train information in easy-to-use JSON format.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Server

```bash
python web_server.py
```

The server will start on `http://0.0.0.0:5000`

### 3. Get Train Information

```bash
curl "http://localhost:5000/trains?city=mnr&limit=20"
```

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `GET /trains?city=mnr&limit=20` - Get real-time train data

## Example Response

```json
{
  "timestamp": "2025-10-25T14:30:00",
  "city": "mnr",
  "total_trains": 20,
  "trains": [
    {
      "trip_id": "1234567",
      "route_id": "Hudson",
      "current_stop": "Grand_Central",
      "next_stop": "125th_Street",
      "eta": "2025-10-25T14:45:00",
      "track": "42",
      "status": "On Time"
    }
  ]
}
```

## Options

```bash
python web_server.py --port 8080 --host 0.0.0.0
```

- `--port`: Server port (default: 5000)
- `--host`: Server host (default: 0.0.0.0)
- `--api-key`: Optional MTA API key
- `--debug`: Enable debug mode

See README.md for full documentation.
