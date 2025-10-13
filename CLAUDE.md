# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wi-Fi Channel Analyzer & Optimizer - A cross-platform web application that scans nearby wireless networks, analyzes channel congestion, and recommends optimal Wi-Fi channels to minimize interference.

**Key Features:**
- Real-time Wi-Fi network scanning across Windows, macOS, and Linux
- Channel congestion analysis for 2.4GHz and 5GHz bands
- Web-based UI with interactive data visualization
- Channel recommendation algorithm based on AP distribution

## Architecture

### System Design

```
┌─────────────────┐
│   Web Browser   │  (Frontend: Vanilla JS + Chart.js)
│   localhost     │
└────────┬────────┘
         │ HTTP REST API
         ▼
┌─────────────────┐
│  Node.js Server │  (Express.js on port 5000)
│  backend/src/   │
└────────┬────────┘
         │ child_process.spawn()
         ▼
┌─────────────────┐
│ Python Scanner  │  (Platform-specific CLI commands)
│ wifi_scanner.py │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OS Commands    │  (netsh/airport/nmcli)
└─────────────────┘
```

### Technology Stack

**Backend:**
- Node.js + Express.js (REST API server)
- Python 3 (Wi-Fi scanning utility)
- `child_process` module (Python script execution)

**Frontend:**
- Vanilla JavaScript (no frameworks)
- HTML5 + CSS3 (responsive design)
- Chart.js (data visualization)

**Data Flow:**
1. User clicks scan button in browser
2. Frontend `fetch()` calls `/api/scan`
3. Express server spawns Python subprocess
4. Python executes platform-specific system commands
5. Python parses output and returns JSON
6. Node.js forwards JSON to frontend
7. Frontend renders chart and table

## Commands

### Development

```bash
# Install dependencies
cd backend
npm install

# Start server (production mode)
npm start

# Start server (development mode with auto-restart)
npm run dev
```

Server runs on `http://localhost:5000`

### Testing the Scanner Directly

```bash
# Test Python scanner independently
python3 backend/src/wifi_scanner.py

# Windows
python backend/src/wifi_scanner.py

# Output should be valid JSON
```

### Platform Requirements

**Windows:**
- Must run with Administrator privileges
- Uses `netsh wlan show networks` command

**macOS:**
- Regular user privileges sufficient
- Uses `/System/Library/PrivateFrameworks/Apple80211.framework/.../airport -s`

**Linux:**
- Regular user privileges sufficient
- Uses `nmcli -f SSID,CHAN,SIGNAL dev wifi`

## Code Architecture

### Backend: Node.js Server (`backend/src/server.js`)

**Key Endpoints:**
- `GET /` - Serves frontend HTML
- `GET /api/health` - Health check (returns platform info)
- `GET /api/scan` - Triggers Wi-Fi scan, returns JSON results
- `GET /api/debug` - System debugging information

**Process Communication:**
The server uses `spawn()` to execute Python as a child process:
```javascript
const pythonProcess = spawn(pythonCommand, [pythonScript]);
// Collects stdout as JSON
// Handles stderr for errors
```

**Important:** The Python command differs by platform:
- Windows: `python`
- macOS/Linux: `python3`

### Backend: Python Scanner (`backend/src/wifi_scanner.py`)

**Platform Detection:**
Automatically detects OS using `sys.platform` and calls appropriate scanner function.

**Platform-Specific Implementations:**

1. **Windows (`scan_networks_windows`)**:
   - Command: `netsh wlan show networks interface="Wi-Fi" mode=bssid`
   - Encoding: cp949 (Korean Windows) with UTF-8 fallback
   - Parses SSID, Channel, Signal from structured output

2. **macOS (`scan_networks_macos`)**:
   - Command: `airport -s`
   - Encoding: UTF-8
   - Parses space-separated tabular output

3. **Linux (`scan_networks_linux`)**:
   - Command: `nmcli -f SSID,CHAN,SIGNAL dev wifi`
   - Encoding: UTF-8
   - Parses NetworkManager output

**Output Format:**
```json
{
  "networks": [
    {"ssid": "NetworkName", "channel": 6, "signal": 75}
  ],
  "channel_usage": {"6": 2, "11": 1},
  "recommended": 11,
  "predicted": "15%"
}
```

### Channel Recommendation Algorithm

Located in `recommend_channel()` function:

**Logic:**
1. Count APs per channel using `Counter`
2. Determine band (2.4GHz if max channel ≤ 14, else 5GHz)
3. Define non-overlapping candidates:
   - **2.4GHz**: channels 1, 6, 11
   - **5GHz**: channels 36, 40, 44, 48, 149, 153, 157, 161
4. Return channel with minimum AP count

**Why these channels?**
- 2.4GHz channels 1, 6, 11 don't overlap (each uses ~22MHz bandwidth)
- 5GHz channels selected avoid DFS (Dynamic Frequency Selection) restrictions

### Frontend Architecture

**File Structure:**
```
frontend/
├── index.html          # Main UI structure
├── css/style.css       # Styling (CSS variables, responsive design)
└── js/app.js           # Application logic
```

**Key JavaScript Functions:**

- `init()` - Initializes app, attaches event listeners
- `checkBackendHealth()` - Verifies server connectivity on load
- `handleScanClick()` - Triggers scan via `/api/scan`
- `displayResults(data)` - Updates UI with scan results
- `updateChart()` - Renders Chart.js bar chart
- `updateNetworksTable()` - Populates network list table

**State Management:**
Single global variable `chartInstance` holds Chart.js instance (destroyed/recreated on each scan).

**API Communication:**
Uses `fetch()` API with `async/await` pattern. No external HTTP library needed.

## Important Implementation Details

### Encoding Handling (Windows)

Korean Windows uses cp949 encoding for console output. The Python scanner handles this:

```python
output.decode('cp949', errors='ignore')
```

If working on Windows parsing logic, ensure both Korean and English field names are supported:
- "SSID 1" / "SSID번호"
- "Channel" / "채널"
- "Signal" / "신호"

### Static File Serving

Express serves the entire `frontend/` directory as static files:

```javascript
app.use(express.static(path.join(__dirname, '../../frontend')));
```

CSS and JS files are loaded via relative paths in `index.html`:
- `<link rel="stylesheet" href="css/style.css">`
- `<script src="js/app.js"></script>`

### CORS Configuration

CORS is enabled for all origins during development:

```javascript
app.use(cors());
```

For production deployment, restrict CORS to specific origins.

### Subprocess Security

The Python script is executed without user input in the command:

```javascript
spawn(pythonCommand, [pythonScript]);
```

**Important:** Never incorporate user input into subprocess commands. Current implementation is safe as no user data reaches `spawn()`.

## Common Pitfalls

### Python Not Found Error

**Symptom:** "Failed to start Python process" or "ENOENT"

**Cause:** Python not in PATH or wrong command name

**Solution:** Modify `pythonCommand` detection in `server.js:39`:
```javascript
const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
```

### Empty Scan Results on Windows

**Symptom:** `networks: []` returned despite nearby networks

**Cause:** Server not running with Administrator privileges

**Solution:** Start command prompt/PowerShell as Administrator before `npm start`

### Chart Not Rendering

**Symptom:** No chart displays, console shows Chart.js errors

**Cause:** Chart.js CDN not loaded (offline or network issue)

**Solution:** Check browser console. Consider downloading Chart.js locally for offline use.

### Interface Name Issues (Windows)

**Symptom:** Empty results on non-English Windows

**Cause:** Hardcoded interface name "Wi-Fi" doesn't match system language

**Current Implementation:** Fixed to "Wi-Fi" which works on most systems

**Enhancement:** Could auto-detect interface name by parsing `netsh wlan show interfaces`

## Debugging

### Backend Debugging

```bash
# Check server logs in console
cd backend
npm start
# Logs will show Python stdout/stderr

# Test endpoints manually
curl http://localhost:5000/api/health
curl http://localhost:5000/api/scan
curl http://localhost:5000/api/debug
```

### Python Debugging

```bash
# Run scanner directly to see raw output
python3 backend/src/wifi_scanner.py

# Check if JSON is valid
python3 backend/src/wifi_scanner.py | python3 -m json.tool
```

### Frontend Debugging

Open browser console and use exposed debug functions:

```javascript
// Check API endpoints
console.log(WifiAnalyzer.API_ENDPOINTS);

// Trigger health check
WifiAnalyzer.checkHealth();

// Trigger scan
WifiAnalyzer.scan();
```

## File Paths and Structure

```
network_project/
├── backend/
│   ├── package.json           # Node.js dependencies and scripts
│   └── src/
│       ├── server.js          # Express server (165 lines)
│       └── wifi_scanner.py    # Python scanner (280+ lines)
└── frontend/
    ├── index.html             # UI structure
    ├── css/
    │   └── style.css          # Responsive design with CSS variables
    └── js/
        └── app.js             # Frontend logic with Chart.js integration
```

**Path Resolution:**
Backend uses `path.join(__dirname, '../../frontend')` to serve static files from parent directory.

## Code Style

**JavaScript:**
- ES6+ syntax (arrow functions, async/await, template literals)
- 2-space indentation
- camelCase for functions and variables
- UPPER_SNAKE_CASE for constants

**Python:**
- 4-space indentation
- snake_case naming
- Docstrings for all functions
- Type hints not currently used (could be added)

**CSS:**
- CSS custom properties (variables) for theming
- BEM-like naming conventions (e.g., `.card-title`)
- Mobile-first responsive design with `@media` queries

## Extension Points

### Adding New Platforms

To add support for a new OS:

1. Add detection in `detect_platform()` in `wifi_scanner.py`
2. Implement `scan_networks_<platform>()` function
3. Return list of `(ssid, channel, signal)` tuples
4. Add to `scan_networks()` dispatcher

### Adding New API Endpoints

1. Add route in `server.js` using `app.get()` or `app.post()`
2. Return JSON with appropriate HTTP status codes
3. Add endpoint to `API_ENDPOINTS` in `frontend/js/app.js`
4. Implement frontend handler function

### Modifying Channel Recommendation Logic

Edit `recommend_channel()` in `wifi_scanner.py`. Current algorithm is simple (minimum AP count). Could enhance with:
- Signal strength weighting
- Channel overlap calculation
- Historical congestion data
- DFS channel avoidance

## Known Limitations

1. **Administrator Requirements (Windows)**: Cannot be bypassed - OS security requirement
2. **Single Concurrent Scan**: Only one scan can run at a time (no queue mechanism)
3. **CDN Dependency**: Chart.js loaded from CDN - requires internet connection
4. **No Persistence**: Scan results not saved - purely in-memory
5. **Fixed Interface Name**: Windows version uses hardcoded "Wi-Fi" interface name

## Production Deployment

**Do NOT use in production as-is.** Flask development server and lack of security hardening make this unsuitable for production. Required changes:

1. Use production WSGI server (e.g., Gunicorn, uWSGI)
2. Restrict CORS to specific origins
3. Add rate limiting (e.g., express-rate-limit)
4. Add authentication if exposed externally
5. Use HTTPS with proper certificates
6. Add request validation and sanitization
7. Implement proper logging (e.g., Winston)
8. Add monitoring and alerting
9. Consider containerization (Docker)

---

**Last Updated:** 2025-10-13
**Architecture:** Node.js + Python + Vanilla JavaScript
**Language:** Korean (UI), English (code/comments)
