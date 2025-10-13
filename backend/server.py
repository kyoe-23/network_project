from flask import Flask, jsonify, render_template_string
import subprocess
from collections import Counter

app = Flask(__name__)

INTERFACE_NAME = "Wi-Fi"  # 자신의 네트워크 어댑터 이름

# ✅ 실제 Wi-Fi 스캔 함수 (당신이 준 코드 그대로)
def scan_wifi_windows():
    try:
        result = subprocess.check_output(
            [r"C:\Windows\System32\netsh.exe", "wlan", "show", "networks", f"interface={INTERFACE_NAME}", "mode=bssid"],
            shell=True
        ).decode("cp949", errors="ignore")
    except subprocess.CalledProcessError:
        return []

    networks = []
    ssid = None
    chan = None

    for line in result.split("\n"):
        line = line.strip()
        if "SSID" in line and "BSSID" not in line:
            ssid = line.split(":", 1)[1].strip()
        elif "채널" in line or "Channel" in line:
            try:
                chan = int(line.split(":", 1)[1].strip())
            except:
                chan = None
        elif "신호" in line or "Signal" in line:
            try:
                signal = int(line.split(":", 1)[1].replace("%","").strip())
            except:
                signal = 0
            if ssid and chan:
                networks.append((ssid, chan, signal))
                ssid, chan = None, None
    return networks


def recommend_channel(networks):
    counter = Counter([n[1] for n in networks])
    candidate_channels = [1, 6, 11, 36, 40, 44, 48, 149, 153, 157, 161]
    best_channel = min(candidate_channels, key=lambda c: counter.get(c, 0))
    return best_channel, counter


# ✅ HTML + JS (당신이 좋아하던 원래 UI 스타일)
html_code = """
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Wi‑Fi Optimizer — Prototype</title>
  <style>
    /* 기본 리셋 */
    *{box-sizing:border-box;margin:0;padding:0}
    :root{
      --bg:#f5f7fb;--card:#ffffff;--muted:#6b7280;--accent:#2563eb;--good:#10b981;--warn:#f59e0b;--bad:#ef4444;
      --glass: rgba(255,255,255,0.6);
      font-family: Inter, system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif;
    }
    body{background:var(--bg);color:#111;line-height:1.3;padding:28px}

    /* 레이아웃 */
    .container{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 380px;gap:24px}
    header{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
    .brand{display:flex;gap:12px;align-items:center}
    .logo{width:44px;height:44px;border-radius:8px;background:linear-gradient(135deg,var(--accent),#7c3aed);display:flex;align-items:center;justify-content:center;color:white;font-weight:700}
    h1{font-size:18px}
    .top-actions{display:flex;gap:10px;align-items:center}
    button.icon{background:transparent;border:0;padding:8px;border-radius:8px;cursor:pointer}

    /* 메인 카드 */
    .card{background:var(--card);border-radius:12px;padding:18px;box-shadow:0 6px 18px rgba(15,23,42,0.06)}
    .main-card{display:flex;flex-direction:column;gap:14px}

    .ssid-row{display:flex;align-items:center;justify-content:space-between}
    .ssid{font-weight:600}
    .meta{color:var(--muted);font-size:13px}

    .channel-row{display:flex;align-items:center;gap:16px}
    .channel-big{font-size:40px;font-weight:700}
    .signal{display:flex;flex-direction:column;gap:6px}

    .progress-wrap{width:240px}
    .progress{height:14px;background:#eee;border-radius:8px;overflow:hidden}
    .progress > i{display:block;height:100%;background:linear-gradient(90deg,var(--good),var(--warn));width:40%}
    .status-tag{display:inline-block;padding:6px 10px;border-radius:999px;font-weight:600}

    .recommend{display:flex;align-items:center;justify-content:space-between;margin-top:6px}
    .rec-box{display:flex;gap:12px;align-items:center}
    .rec-channel{background:linear-gradient(90deg,#fff,rgba(0,0,0,0.02));padding:8px 12px;border-radius:10px;font-weight:700}
    .apply-btn{background:var(--accent);color:white;border:0;padding:10px 14px;border-radius:10px;cursor:pointer}

    /* 오른쪽: 요약 카드 */
    .summary{display:flex;flex-direction:column;gap:12px}
    .mini{display:flex;flex-direction:column;gap:8px}
    .mini .row{display:flex;justify-content:space-between;color:var(--muted)}

    /* 채널 분석 */
    .wide{grid-column:1/ -1}
    .chart{display:flex;flex-direction:column;gap:10px;padding:12px}
    .bars{display:flex;gap:8px;align-items:end;height:180px;padding:8px}
    .bar{flex:1;border-radius:6px;padding:6px 4px;display:flex;align-items:flex-end;justify-content:center;position:relative}
    .bar > span{position:absolute;top:-22px;font-size:12px;color:var(--muted)}
    .bar .fill{width:100%;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--accent),#60a5fa);display:block}

    .controls{display:flex;gap:8px;align-items:center;margin-top:8px}
    select,input[type=radio]{padding:8px;border-radius:8px;border:1px solid #e6e9ef}

    footer{grid-column:1/-1;margin-top:12px;color:var(--muted);font-size:13px}

    /* 반응형 */
    @media (max-width:980px){.container{grid-template-columns:1fr}.wide{grid-column:1}.container {padding:0 12px}}

  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo">WF</div>
      <div>
        <h1>Wi‑Fi Optimizer</h1>
        <div class="meta">채널 혼잡도 분석 및 최적 채널 추천</div>
      </div>
    </div>
    <div class="top-actions">
      <button class="icon" title="설정">⚙️</button>
      <button class="icon" title="도움말">❓</button>
    </div>
  </header>

  <main class="container">
    <!-- 왼쪽: 메인 정보 -->
    <section class="card main-card">
      <div class="ssid-row">
        <div>
          <div class="ssid" id="ssid">SSID: Home_Network</div>
          <div class="meta">연결 중: 2.4 GHz • BSSID: 11:22:33:44:55:66</div>
        </div>
        <div class="meta">스캔 간격: <span id="scan-interval">30s</span></div>
      </div>

      <div class="channel-row">
        <div>
          <div class="channel-big" id="current-channel">6</div>
          <div class="meta">현재 채널</div>
        </div>

        <div class="signal">
          <div class="progress-wrap">
            <div class="progress" aria-hidden="true"><i id="congestion-fill"></i></div>
            <div class="meta" style="margin-top:6px">혼잡도: <strong id="congestion-percent">40%</strong></div>
          </div>
          <div id="status-tag" class="status-tag" style="background:var(--good);color:white">양호</div>
        </div>

        <div style="margin-left:auto;text-align:right">
          <div class="meta">추천 채널</div>
          <div class="rec-channel" id="recommended">11</div>
        </div>
      </div>

      <div class="recommend">
        <div class="rec-box">
          <div class="meta">이 채널로 변경하면 예상 혼잡도: <strong id="predicted">22%</strong></div>
        </div>
        <div>
          <button class="apply-btn" id="apply-btn">채널 적용 (시뮬레이션)</button>
        </div>
      </div>

      <div style="display:flex;gap:12px;margin-top:6px;align-items:center">
        <button id="rescan" class="apply-btn" style="background:#111;color:#fff;padding:8px 12px">다시 스캔</button>
        <div class="meta">스캔 시간: <span id="last-scan">-</span></div>
      </div>
    </section>

    <!-- 오른쪽: 요약 -->
    <aside class="summary">
      <div class="card mini">
        <div class="row"><div>주파수</div><div id="band">2.4 GHz</div></div>
        <div class="row"><div>연결 기기 수(예시)</div><div id="clients">6</div></div>
        <div class="row"><div>업로드/다운로드 속도(예시)</div><div id="speed">20 / 85 Mbps</div></div>
      </div>

      <div class="card mini">
        <div class="meta">알림</div>
        <div>혼잡도 > 70% 일 때 푸시 알림</div>
      </div>
    </aside>

    <!-- 채널 분석 (전체 너비) -->
    <section class="card wide">
      <div class="chart">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="font-weight:700">채널 분석</div>
          <div class="controls">
            <label class="meta">대역</label>
            <select id="band-select">
              <option>2.4 GHz</option>
              <option>5 GHz</option>
            </select>
            <label class="meta">보기</label>
            <select id="view-select">
              <option>혼잡도(%)</option>
              <option>기기 수</option>
            </select>
          </div>
        </div>

        <div class="bars" id="bars">
          <!-- 바들은 JS로 생성됩니다 -->
        </div>

        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px">
          <div class="meta">가장 낮은 혼잡도 채널이 추천됩니다</div>
          <div>
            <small class="meta">참고: 이 UI는 프로토타입이며 실제 라우터 설정 변경 권한은 없습니다.</small>
          </div>
        </div>

      </div>
    </section>

    <footer>프로토타입 — HTML/CSS/JS. 필요하면 컴포넌트별로 분리해 드릴게요.</footer>
  </main>

  <script>
  const barsEl = document.getElementById('bars');
  const recommendedEl = document.getElementById('recommended');
  const predictedEl = document.getElementById('predicted');
  const congestionFill = document.getElementById('congestion-fill');
  const congestionPercent = document.getElementById('congestion-percent');
  const statusTag = document.getElementById('status-tag');
  const currentChannelEl = document.getElementById('current-channel');
  const lastScanEl = document.getElementById('last-scan');
  const ssidEl = document.getElementById('ssid');

  async function rescan() {
    const res = await fetch("/scan");
    const data = await res.json();
    const results = data.networks;
    if (!results || results.length === 0) {
      alert("⚠️ Wi-Fi를 찾지 못했습니다.");
      return;
    }

    // 혼잡도 계산 (예시: 신호 세기 반대로 계산)
    const barsData = results.map(n => ({
      channel: n.channel,
      value: 100 - n.signal
    }));

    // 가장 신호 좋은(혼잡도 낮은) 채널 선택
    const minItem = barsData.reduce((a, b) => a.value < b.value ? a : b);
    recommendedEl.textContent = data.recommended || minItem.channel;
    predictedEl.textContent = Math.max(0, Math.round(minItem.value * 0.6)) + '%';

    // 임시로 첫 번째 네트워크 표시
    const bestNet = results[0];
    ssidEl.textContent = "SSID: " + bestNet.ssid;
    currentChannelEl.textContent = bestNet.channel;

    // 혼잡도 표시
    const perc = Math.round(100 - bestNet.signal);
    congestionFill.style.width = perc + '%';
    congestionPercent.textContent = perc + '%';
    lastScanEl.textContent = new Date().toLocaleTimeString();

    if (perc < 40){ statusTag.textContent='양호'; statusTag.style.background='var(--good)'; }
    else if (perc < 70){ statusTag.textContent='보통'; statusTag.style.background='var(--warn)'; }
    else { statusTag.textContent='혼잡'; statusTag.style.background='var(--bad)'; }

    // 막대 그래프 표시
    renderBars(barsData);
  }

  function renderBars(data) {
    barsEl.innerHTML = "";
    data.forEach(d => {
      const bar = document.createElement('div');
      bar.className = 'bar';
      const label = document.createElement('span');
      label.textContent = d.channel;
      const fill = document.createElement('div');
      fill.className = 'fill';
      fill.style.height = d.value + '%';
      bar.appendChild(label);
      bar.appendChild(fill);
      barsEl.appendChild(bar);
    });
  }

  // 초기 로드 + 다시스캔 버튼 연결
  document.getElementById('rescan').addEventListener('click', rescan);
  window.addEventListener('load', rescan);
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(html_code)

@app.route("/scan")
def scan():
    networks = scan_wifi_windows()
    if not networks:
        return jsonify({"networks": [], "recommended": None})
    best, counter = recommend_channel(networks)
    net_data = [{"ssid": s, "channel": c, "signal": sig} for s, c, sig in networks]
    return jsonify({"networks": net_data, "recommended": best})

if __name__ == "__main__":
    app.run(debug=True)
