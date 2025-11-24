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
  channelChart: document.getElementById('channelChart'),
  recommendedListBody: document.getElementById('recommendedListBody'),
  recommendationDescription: document.getElementById('recommendationDescription')
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
    showStatus('PUSH BUTTON', 'success');
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
    showStatus('Scan Success', 'success');

  } catch (error) {
    console.error('Scan failed:', error);
    showStatus(`Scan Failed: ${error.message}`, 'error');

  } finally {
    setLoading(false);
  }
}

/**
 * Display scan results
 */
function displayResults(data) {
  const { networks, channel_usage, recommended, predicted, recommended_list, recommended_networks } = data;

  // Show results section with animation
  elements.resultsSection.style.display = 'block';
  elements.resultsSection.classList.add('fade-in');

  // Update recommendation
  elements.recommendedChannel.textContent = recommended || '-';
  elements.predictedCongestion.textContent = predicted || 'N/A';

  // Update recommendation description
  updateRecommendationDescription(recommended, recommended_networks, channel_usage);

  // Calculate statistics
  const stats = calculateStatistics(networks);
  elements.totalNetworks.textContent = stats.total;
  elements.activeChannels.textContent = stats.activeChannels;
  elements.networks24ghz.textContent = stats.networks24ghz;
  elements.networks5ghz.textContent = stats.networks5ghz;

  // Update chart
  updateChart(networks);

  // Update recommended channels list
  updateRecommendedList(recommended_list);

  // Update networks table
  updateNetworksTable(networks);
}

/**
 * Update recommendation description
 */
function updateRecommendationDescription(recommended, recommendedNetworks, channelUsage) {
  if (!recommended) {
    elements.recommendationDescription.innerHTML = '';
    return;
  }

  const apCount = channelUsage[recommended] || 0;
  const band = recommended <= 14 ? '2.4GHz' : '5GHz';

  let description = '';

  if (apCount === 0) {
    description = `
      <p class="desc-main">이 채널을 사용하는 네트워크가 없습니다.</p>
      <p class="desc-detail">→ 간섭이 없어 <strong>최적의 채널</strong>입니다.</p>
    `;
  } else {
    const networkList = recommendedNetworks.slice(0, 5).join(', ');
    const moreCount = recommendedNetworks.length > 5 ? ` 외 ${recommendedNetworks.length - 5}개` : '';

    description = `
      <p class="desc-main">이 채널을 사용하는 네트워크 (${apCount}개):</p>
      <p class="desc-networks">${networkList}${moreCount}</p>
      <p class="desc-detail">→ 다른 채널보다 혼잡도가 낮아 추천됩니다.</p>
    `;
  }

  description += `<p class="desc-band">${band} 대역 | 채널 ${recommended}</p>`;

  elements.recommendationDescription.innerHTML = description;
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
 * Update network signal strength chart
 */
function updateChart(networks) {
  const ctx = elements.channelChart.getContext('2d');

  // Destroy existing chart if present
  if (chartInstance) {
    chartInstance.destroy();
  }

  // Sort networks by signal strength (descending)
  const sortedNetworks = [...networks].sort((a, b) => b.signal - a.signal);

  // Prepare data
  const labels = sortedNetworks.map(n => n.ssid || '(숨김)');
  const signals = sortedNetworks.map(n => n.signal);

  // Color bars based on signal strength
  const backgroundColors = signals.map(signal => {
    if (signal >= 70) return 'rgba(34, 197, 94, 0.7)';
    if (signal >= 40) return 'rgba(234, 179, 8, 0.7)';
    return 'rgba(239, 68, 68, 0.7)';
  });

  const borderColors = signals.map(signal => {
    if (signal >= 70) return 'rgba(34, 197, 94, 1)';
    if (signal >= 40) return 'rgba(234, 179, 8, 1)';
    return 'rgba(239, 68, 68, 1)';
  });

  // Create chart
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: '신호 강도',
        data: signals,
        backgroundColor: backgroundColors,
        borderColor: borderColors,
        borderWidth: 1
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
              const network = sortedNetworks[context.dataIndex];
              return `${context.parsed.y}% (채널 ${network.channel})`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: '신호 강도 (%)'
          }
        },
        x: {
          title: {
            display: true,
            text: '네트워크'
          }
        }
      }
    }
  });
}

/**
 * Update recommended channels list
 */
function updateRecommendedList(recommendedList) {
  // Clear existing rows
  elements.recommendedListBody.innerHTML = '';

  if (!recommendedList || recommendedList.length === 0) {
    return;
  }

  // Populate table
  recommendedList.forEach(item => {
    const row = document.createElement('tr');

    // Highlight best recommendation
    if (item.rank === 1) {
      row.className = 'best-recommendation';
    }

    // Rank
    const rankCell = document.createElement('td');
    rankCell.textContent = item.rank;
    rankCell.className = 'rank-cell';
    row.appendChild(rankCell);

    // Channel
    const channelCell = document.createElement('td');
    channelCell.textContent = `채널 ${item.channel}`;
    channelCell.className = 'channel-cell';
    row.appendChild(channelCell);

    // AP Count
    const apCountCell = document.createElement('td');
    apCountCell.textContent = `${item.ap_count}개`;
    row.appendChild(apCountCell);

    // Congestion
    const congestionCell = document.createElement('td');
    congestionCell.textContent = item.congestion;
    row.appendChild(congestionCell);

    // Grade
    const gradeCell = document.createElement('td');
    const gradeSpan = document.createElement('span');
    gradeSpan.textContent = item.grade;
    gradeSpan.className = `grade-badge grade-${getGradeClass(item.grade)}`;
    gradeCell.appendChild(gradeSpan);
    row.appendChild(gradeCell);

    elements.recommendedListBody.appendChild(row);
  });
}

/**
 * Get CSS class based on grade
 */
function getGradeClass(grade) {
  switch (grade) {
    case '최적': return 'optimal';
    case '양호': return 'good';
    case '보통': return 'normal';
    case '혼잡': return 'congested';
    default: return 'normal';
  }
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
