/**
 * Wi-Fi Channel Analyzer - Frontend Application
 * Handles UI interactions and API communication
 */

// API Configuration
const API_BASE_URL = window.location.origin;
const API_ENDPOINTS = {
  scan: `${API_BASE_URL}/api/scan`,
  health: `${API_BASE_URL}/api/health`
};

// Global state
let chartInstance = null;

// DOM Elements
const elements = {
  scanButton: document.getElementById('scanButton'),
  statusMessage: document.getElementById('statusMessage'),
  resultsSection: document.getElementById('resultsSection'),
  loadingOverlay: document.getElementById('loadingOverlay'),
  recommendedChannel: document.getElementById('recommendedChannel'),
  predictedCongestion: document.getElementById('predictedCongestion'),
  totalNetworks: document.getElementById('totalNetworks'),
  activeChannels: document.getElementById('activeChannels'),
  networks24ghz: document.getElementById('networks24ghz'),
  networks5ghz: document.getElementById('networks5ghz'),
  networksTableBody: document.getElementById('networksTableBody'),
  channelChart: document.getElementById('channelChart')
};

/**
 * Initialize the application
 */
function init() {
  console.log('Initializing Wi-Fi Channel Analyzer...');

  // Attach event listeners
  elements.scanButton.addEventListener('click', handleScanClick);

  // Check backend health
  checkBackendHealth();

  console.log('Application initialized');
}

/**
 * Check if backend is reachable
 */
async function checkBackendHealth() {
  try {
    const response = await fetch(API_ENDPOINTS.health);
    const data = await response.json();
    console.log('Backend health check:', data);
    showStatus('준비 완료 - 스캔 버튼을 클릭하세요', 'success');
  } catch (error) {
    console.error('Backend health check failed:', error);
    showStatus('서버 연결 실패 - 백엔드가 실행 중인지 확인하세요', 'error');
  }
}

/**
 * Handle scan button click
 */
async function handleScanClick() {
  console.log('Scan button clicked');

  // Disable button and show loading
  setLoading(true);
  showStatus('네트워크 스캔 중...', 'info');

  try {
    // Call scan API
    const response = await fetch(API_ENDPOINTS.scan);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Scan results:', data);

    // Check for errors in response
    if (data.error) {
      throw new Error(data.error);
    }

    // Process and display results
    displayResults(data);
    showStatus('스캔 완료!', 'success');

  } catch (error) {
    console.error('Scan failed:', error);
    showStatus(`스캔 실패: ${error.message}`, 'error');

  } finally {
    setLoading(false);
  }
}

/**
 * Display scan results
 */
function displayResults(data) {
  const { networks, channel_usage, recommended, predicted } = data;

  // Show results section with animation
  elements.resultsSection.style.display = 'block';
  elements.resultsSection.classList.add('fade-in');

  // Update recommendation
  elements.recommendedChannel.textContent = recommended || '-';
  elements.predictedCongestion.textContent = predicted || 'N/A';

  // Calculate statistics
  const stats = calculateStatistics(networks);
  elements.totalNetworks.textContent = stats.total;
  elements.activeChannels.textContent = stats.activeChannels;
  elements.networks24ghz.textContent = stats.networks24ghz;
  elements.networks5ghz.textContent = stats.networks5ghz;

  // Update chart
  updateChart(channel_usage, recommended);

  // Update networks table
  updateNetworksTable(networks);
}

/**
 * Calculate statistics from networks data
 */
function calculateStatistics(networks) {
  const stats = {
    total: networks.length,
    activeChannels: 0,
    networks24ghz: 0,
    networks5ghz: 0
  };

  const channels = new Set();

  networks.forEach(network => {
    channels.add(network.channel);

    if (network.channel <= 14) {
      stats.networks24ghz++;
    } else {
      stats.networks5ghz++;
    }
  });

  stats.activeChannels = channels.size;

  return stats;
}

/**
 * Update channel distribution chart
 */
function updateChart(channelUsage, recommendedChannel) {
  const ctx = elements.channelChart.getContext('2d');

  // Destroy existing chart if present
  if (chartInstance) {
    chartInstance.destroy();
  }

  // Prepare data
  const channels = Object.keys(channelUsage).map(Number).sort((a, b) => a - b);
  const counts = channels.map(ch => channelUsage[ch]);

  // Color bars based on recommended channel
  const backgroundColors = channels.map(ch =>
    ch === recommendedChannel ? 'rgba(16, 185, 129, 0.8)' : 'rgba(79, 70, 229, 0.6)'
  );

  const borderColors = channels.map(ch =>
    ch === recommendedChannel ? 'rgba(16, 185, 129, 1)' : 'rgba(79, 70, 229, 1)'
  );

  // Create chart
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: channels.map(ch => `채널 ${ch}`),
      datasets: [{
        label: 'AP 개수',
        data: counts,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              const channel = channels[context.dataIndex];
              const count = context.parsed.y;
              const isRecommended = channel === recommendedChannel;
              return `${count}개 AP${isRecommended ? ' (추천)' : ''}`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            precision: 0
          },
          title: {
            display: true,
            text: 'AP 개수'
          }
        },
        x: {
          title: {
            display: true,
            text: '채널'
          }
        }
      }
    }
  });
}

/**
 * Update networks table
 */
function updateNetworksTable(networks) {
  // Clear existing rows
  elements.networksTableBody.innerHTML = '';

  // Sort networks by signal strength (descending)
  const sortedNetworks = [...networks].sort((a, b) => b.signal - a.signal);

  // Populate table
  sortedNetworks.forEach(network => {
    const row = document.createElement('tr');

    // SSID
    const ssidCell = document.createElement('td');
    ssidCell.textContent = network.ssid || '(숨겨진 네트워크)';
    row.appendChild(ssidCell);

    // Channel
    const channelCell = document.createElement('td');
    channelCell.textContent = network.channel;
    row.appendChild(channelCell);

    // Signal strength
    const signalCell = document.createElement('td');
    signalCell.textContent = `${network.signal}%`;
    signalCell.className = getSignalClass(network.signal);
    row.appendChild(signalCell);

    // Band
    const bandCell = document.createElement('td');
    const bandSpan = document.createElement('span');
    bandSpan.textContent = network.channel <= 14 ? '2.4GHz' : '5GHz';
    bandSpan.className = network.channel <= 14 ? 'band-24ghz' : 'band-5ghz';
    bandCell.appendChild(bandSpan);
    row.appendChild(bandCell);

    elements.networksTableBody.appendChild(row);
  });
}

/**
 * Get CSS class based on signal strength
 */
function getSignalClass(signal) {
  if (signal >= 70) return 'signal-strong';
  if (signal >= 40) return 'signal-medium';
  return 'signal-weak';
}

/**
 * Show status message
 */
function showStatus(message, type = 'info') {
  elements.statusMessage.textContent = message;
  elements.statusMessage.className = `status-message status-${type}`;
}

/**
 * Set loading state
 */
function setLoading(isLoading) {
  elements.scanButton.disabled = isLoading;
  elements.loadingOverlay.style.display = isLoading ? 'flex' : 'none';

  if (isLoading) {
    elements.scanButton.querySelector('.button-text').textContent = '스캔 중...';
  } else {
    elements.scanButton.querySelector('.button-text').textContent = '스캔 시작';
  }
}

/**
 * Format timestamp
 */
function formatTimestamp(date) {
  return new Date(date).toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

/**
 * Handle errors gracefully
 */
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  showStatus('오류가 발생했습니다. 콘솔을 확인하세요.', 'error');
});

/**
 * Handle unhandled promise rejections
 */
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  showStatus('비동기 오류가 발생했습니다.', 'error');
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export for debugging
window.WifiAnalyzer = {
  checkHealth: checkBackendHealth,
  scan: handleScanClick,
  API_ENDPOINTS
};

console.log('Wi-Fi Analyzer app.js loaded');
