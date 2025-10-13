/**
 * Wi-Fi Channel Analyzer - Backend Server
 * Node.js Express server with Python integration
 */

const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../../frontend')));

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    platform: process.platform
  });
});

/**
 * Wi-Fi scan endpoint
 * Executes Python scanner and returns results
 */
app.get('/api/scan', async (req, res) => {
  try {
    const pythonScript = path.join(__dirname, 'wifi_scanner.py');

    // Determine Python command based on platform
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';

    // Spawn Python process
    const pythonProcess = spawn(pythonCommand, [pythonScript]);

    let dataString = '';
    let errorString = '';

    // Collect data from stdout
    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    // Collect error messages from stderr
    pythonProcess.stderr.on('data', (data) => {
      errorString += data.toString();
    });

    // Handle process completion
    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error('Python process error:', errorString);
        return res.status(500).json({
          error: 'Failed to scan networks',
          details: errorString,
          networks: [],
          channel_usage: {},
          recommended: 0,
          predicted: 'N/A'
        });
      }

      try {
        const result = JSON.parse(dataString);
        res.json(result);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        res.status(500).json({
          error: 'Failed to parse scan results',
          networks: [],
          channel_usage: {},
          recommended: 0,
          predicted: 'N/A'
        });
      }
    });

    // Handle process errors
    pythonProcess.on('error', (error) => {
      console.error('Failed to start Python process:', error);
      res.status(500).json({
        error: 'Failed to start scanner',
        details: error.message,
        networks: [],
        channel_usage: {},
        recommended: 0,
        predicted: 'N/A'
      });
    });

  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({
      error: 'Internal server error',
      details: error.message,
      networks: [],
      channel_usage: {},
      recommended: 0,
      predicted: 'N/A'
    });
  }
});

/**
 * Debug endpoint - returns system information
 */
app.get('/api/debug', (req, res) => {
  res.json({
    platform: process.platform,
    nodeVersion: process.version,
    cwd: process.cwd(),
    pythonScript: path.join(__dirname, 'wifi_scanner.py'),
    env: {
      PORT: process.env.PORT
    }
  });
});

/**
 * Serve frontend HTML
 */
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../../frontend/index.html'));
});

/**
 * 404 handler
 */
app.use((req, res) => {
  res.status(404).json({
    error: 'Not found',
    path: req.path
  });
});

/**
 * Error handler
 */
app.use((err, req, res, next) => {
  console.error('Server error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: err.message
  });
});

/**
 * Start server
 */
app.listen(PORT, () => {
  console.log(`Wi-Fi Analyzer Server running on http://localhost:${PORT}`);
  console.log(`Platform: ${process.platform}`);
  console.log(`Node version: ${process.version}`);
  console.log(`Press Ctrl+C to stop`);
});

module.exports = app;
