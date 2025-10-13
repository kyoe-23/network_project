# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Wi-Fi channel analyzer and optimizer tool for Windows that scans nearby wireless networks, analyzes channel congestion, and recommends optimal channels. The project consists of Python Flask backend servers that interface with Windows `netsh` commands and serve a web-based UI for visualization.

## Running the Application

### Prerequisites
- **Windows OS required** - The application uses Windows-specific `netsh` commands
- **Administrator privileges** - Required for `netsh wlan` commands to work
- Python 3.x with Flask installed
- Must run from Administrator PowerShell or CMD

### Running the Server

```bash
# Run the main server (includes embedded HTML UI)
python wifi_server.py

# Alternative server implementations
python wifi_server2.py
python wifi_tool_server.py

# Command-line only version with matplotlib visualization
python Scan_pywifi.py
```

Access the web UI at: `http://127.0.0.1:5000`

## Architecture

### Core Components

1. **Flask Web Servers** (`wifi_server.py`, `wifi_server2.py`, `wifi_tool_server.py`)
   - Serve web UI and REST API endpoints
   - Execute Windows netsh commands via subprocess
   - Parse netsh output for Wi-Fi network data
   - Calculate channel recommendations

2. **Wi-Fi Scanning Logic**
   - Uses `netsh wlan show networks interface="<name>" mode=bssid` command
   - Parses output for SSID, channel number, and signal strength
   - Handles Korean (cp949) and English locale outputs
   - Returns list of tuples: `(ssid, channel, signal_strength)`

3. **Channel Recommendation Algorithm**
   - Counts AP occurrences per channel using Counter
   - Considers non-overlapping channels: 1, 6, 11 (2.4GHz) and 36, 40, 44, 48, 149, 153, 157, 161 (5GHz)
   - Recommends channel with minimum AP count from candidate list

4. **Web UI** (`wifi.html`)
   - Modern, responsive single-page interface
   - Real-time channel congestion visualization
   - Bar chart showing AP distribution across channels
   - Korean language interface

### File Descriptions

- **wifi_server.py** - Main server with HTML embedded in Python string
- **wifi_server2.py** - Alternative server with auto-detection of network interface name (has a syntax error on line 169: `최고` should be `best`)
- **wifi_tool_server.py** - Simpler implementation with embedded HTML
- **Scan_pywifi.py** - CLI-only version with matplotlib graphing
- **wifi.html** - Standalone HTML/CSS/JS frontend

## API Endpoints

### `GET /`
Returns the web UI (HTML page)

### `GET /scan`
Scans Wi-Fi networks and returns JSON:
```json
{
  "networks": [
    {"ssid": "NetworkName", "channel": 6, "signal": 75}
  ],
  "channel_usage": {"1": 2, "6": 5, "11": 3},
  "recommended": 1,
  "predicted": "20%"
}
```

### `GET /debug_netsh` (wifi_server2.py only)
Returns raw netsh output for debugging interface detection issues

## Key Implementation Details

### Windows Interface Name Detection

The network interface name varies by Windows locale:
- English: `"Wi-Fi"` or `"Wireless Network Connection"`
- Korean: `"Wi-Fi"` or `"무선 LAN"` or `"무선 네트워크 연결"`

`wifi_server2.py` includes automatic detection logic that:
1. Tests the preferred interface name
2. Falls back to parsing `netsh wlan show interfaces` output
3. Validates the detected interface by attempting a scan

### netsh Output Parsing

The parsing logic handles variations in netsh output format:
- Multiple SSID formats: `"SSID 1 : name"` or `"SSID : name"`
- Bilingual field names: `"Channel"/"채널"`, `"Signal"/"신호"`
- cp949 encoding for Korean Windows
- BSSID lines are explicitly excluded from SSID detection

### Subprocess Execution

All servers use `subprocess.check_output()` with:
- `shell=True` for convenience on Windows
- `stderr=subprocess.DEVNULL` to suppress error messages
- Try-catch blocks returning empty lists on failure
- cp949 decoding with error="ignore" fallback

## Known Issues

1. **wifi_server2.py line 169**: Variable name bug - `최고` (Korean) should be `best`
2. **Security**: `shell=True` in subprocess calls could be a security risk if user input is incorporated
3. **Platform limitation**: Only works on Windows due to netsh dependency
4. **Permissions**: Requires administrator privileges to run netsh commands

## Development Notes

- The UI uses inline styles with CSS custom properties for theming
- JavaScript fetches from `/scan` endpoint and dynamically renders bar charts
- Signal strength is sometimes inverted to represent congestion percentage
- The "채널 적용" (Apply Channel) button is simulation-only and doesn't actually change router settings
