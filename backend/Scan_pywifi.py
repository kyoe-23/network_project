import subprocess
from collections import Counter
import matplotlib.pyplot as plt
import sys

INTERFACE_NAME = "Wi-Fi"  # 네트워크 인터페이스 이름

def scan_wifi_windows():
    """Windows에서 netsh 명령어로 주변 Wi-Fi 스캔"""
    try:
        result = subprocess.check_output(
            [r"C:\Windows\System32\netsh.exe", "wlan", "show", "networks", f"interface={INTERFACE_NAME}", "mode=bssid"],
            shell=True
        ).decode("cp949", errors="ignore")  # ✅ 한글 윈도우는 cp949
    except subprocess.CalledProcessError:
        print("⚠️ Wi-Fi 스캔 중 오류 발생")
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
                ssid, chan = None, None  # 초기화
    
    return networks

def recommend_channel(networks):
    """2.4GHz 및 5GHz Wi-Fi 채널 최적화"""
    counter = {}
    best_channel = None

    if networks:
        channels = [n[1] for n in networks]
        counter = Counter(channels)
        
        # 대표적인 비중첩 채널 후보
        candidate_channels_24ghz = [1, 6, 11]
        candidate_channels_5ghz = [36, 40, 44, 48, 149, 153, 157, 161]

        candidates = candidate_channels_24ghz + candidate_channels_5ghz
        best_channel = min(candidates, key=lambda c: counter.get(c, 0))

    return best_channel, counter

def visualize(counter):
    """채널 혼잡도 그래프"""
    if not counter:
        print("⚠️ 시각화할 데이터가 없습니다.")
        return

    plt.bar(counter.keys(), counter.values(), color='skyblue')
    plt.xlabel("Wi-Fi Channel")
    plt.ylabel("AP Count")
    plt.title("Wi-Fi 채널 혼잡도")
    plt.xticks(list(counter.keys()))
    plt.show()

if __name__ == "__main__":
    print("📡 주변 Wi-Fi 스캔 중...\n")
    nets = scan_wifi_windows()
    
    if not nets:
        print("⚠️ 주변 Wi-Fi를 찾지 못했습니다.")
        sys.exit()

    for ssid, chan, sig in nets:
        print(f"SSID: {ssid}, 채널: {chan}, 신호 세기: {sig}%")
    
    best, counter = recommend_channel(nets)
    print("\n📊 채널 혼잡도:", dict(counter))
    if best:
        print(f"✅ 추천 채널: {best}")
    else:
        print("⚠️ 추천할 채널 없음")
    
    visualize(counter)
