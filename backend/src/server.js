/**
 * Wi-Fi Channel Analyzer - Backend Server
 * Node.js Express server with Python integration
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();

// Configuration from environment variables
const PORT = process.env.PORT || 5000;
const HOST = process.env.HOST || '0.0.0.0';
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*';
const PYTHON_COMMAND = process.env.PYTHON_COMMAND || (process.platform === 'win32' ? 'python' : 'python3');
const SCAN_TIMEOUT = (parseInt(process.env.SCAN_TIMEOUT) || 15) * 1000; // Convert to milliseconds
const NODE_ENV = process.env.NODE_ENV || 'development';

// Middleware
const corsOptions = {
  origin: CORS_ORIGIN === '*' ? '*' : CORS_ORIGIN.split(','),
  credentials: true
};
app.use(cors(corsOptions));
app.use(express.json());
app.use(express.static(path.join(__dirname, '../../frontend')));

// Logging middleware
app.use((req, _res, next) => {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${req.method} ${req.path}`);
  next();
});

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: new Date().toISOString(),
    platform: process.platform,
    nodeVersion: process.version,
    environment: NODE_ENV
  });
});

/**
 * Wi-Fi scan endpoint
 * Executes Python scanner and returns results
 */
app.get('/api/scan', async (req, res) => {
  const startTime = Date.now();

  try {
    const pythonScript = path.join(__dirname, 'wifi_scanner.py');

    console.log(`[SCAN] Starting Wi-Fi scan with ${PYTHON_COMMAND}`);
    console.log(`[SCAN] Python script: ${pythonScript}`);

    // Pass configuration to Python script via environment variables
    const env = {
      ...process.env,
      WIFI_INTERFACE_NAME: process.env.WIFI_INTERFACE_NAME || '',
      SCAN_TIMEOUT: process.env.SCAN_TIMEOUT || '10'
    };

    // Spawn Python process
    const pythonProcess = spawn(PYTHON_COMMAND, [pythonScript], { env });

    let dataString = '';
    let errorString = '';

    // Set timeout for Python process
    const timeout = setTimeout(() => {
      pythonProcess.kill();
      console.error('[SCAN] Process timeout');
    }, SCAN_TIMEOUT);

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
      clearTimeout(timeout);
      const duration = Date.now() - startTime;

      if (code !== 0) {
        console.error(`[SCAN] Failed (${duration}ms):`, errorString);
        return res.status(500).json({
          error: 'Wi-Fi 스캔에 실패했습니다',
          details: errorString || 'Python 스크립트 실행 오류',
          platform: process.platform,
          networks: [],
          channel_usage: {},
          recommended: 0,
          predicted: 'N/A'
        });
      }

      try {
        const result = JSON.parse(dataString);
        console.log(`[SCAN] Success (${duration}ms): ${result.networks.length} networks found`);
        res.json(result);
      } catch (parseError) {
        console.error('[SCAN] JSON parse error:', parseError);
        console.error('[SCAN] Raw output:', dataString);
        res.status(500).json({
          error: '스캔 결과 파싱 실패',
          details: parseError.message,
          networks: [],
          channel_usage: {},
          recommended: 0,
          predicted: 'N/A'
        });
      }
    });

    // Handle process errors
    pythonProcess.on('error', (error) => {
      clearTimeout(timeout);
      console.error('[SCAN] Process error:', error);

      let errorMessage = 'Python 스크립트를 실행할 수 없습니다';
      let suggestion = '';

      if (error.code === 'ENOENT') {
        errorMessage = 'Python을 찾을 수 없습니다';
        suggestion = `시스템에 Python이 설치되어 있는지 확인하세요. 현재 명령어: ${PYTHON_COMMAND}`;
      }

      res.status(500).json({
        error: errorMessage,
        details: error.message,
        suggestion: suggestion,
        networks: [],
        channel_usage: {},
        recommended: 0,
        predicted: 'N/A'
      });
    });

  } catch (error) {
    console.error('[SCAN] Server error:', error);
    res.status(500).json({
      error: '서버 내부 오류',
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
    config: {
      PORT: PORT,
      HOST: HOST,
      PYTHON_COMMAND: PYTHON_COMMAND,
      CORS_ORIGIN: CORS_ORIGIN,
      SCAN_TIMEOUT: SCAN_TIMEOUT,
      NODE_ENV: NODE_ENV,
      WIFI_INTERFACE_NAME: process.env.WIFI_INTERFACE_NAME || 'auto-detect'
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
    error: '요청한 리소스를 찾을 수 없습니다',
    path: req.path
  });
});

/**
 * Error handler
 */
app.use((err, req, res, next) => {
  console.error('[ERROR]', err);
  res.status(500).json({
    error: '서버 내부 오류',
    message: NODE_ENV === 'development' ? err.message : '서버 오류가 발생했습니다'
  });
});

/**
 * Start server
 */
const server = app.listen(PORT, HOST, () => {
  console.log('='.repeat(60));
  console.log('  Wi-Fi Channel Analyzer Server');
  console.log('='.repeat(60));
  console.log(`  URL: http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`);
  console.log(`  환경: ${NODE_ENV}`);
  console.log(`  플랫폼: ${process.platform}`);
  console.log(`  Node 버전: ${process.version}`);
  console.log(`  Python 명령어: ${PYTHON_COMMAND}`);
  console.log('='.repeat(60));
  console.log('  서버가 시작되었습니다. Ctrl+C로 종료할 수 있습니다.');
  console.log('='.repeat(60));
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('\n[SHUTDOWN] SIGTERM 신호를 받았습니다. 서버를 종료합니다...');
  server.close(() => {
    console.log('[SHUTDOWN] 서버가 정상적으로 종료되었습니다.');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('\n[SHUTDOWN] SIGINT 신호를 받았습니다. 서버를 종료합니다...');
  server.close(() => {
    console.log('[SHUTDOWN] 서버가 정상적으로 종료되었습니다.');
    process.exit(0);
  });
});

module.exports = app;
