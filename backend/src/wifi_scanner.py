#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wi-Fi Network Scanner Utility
Scans nearby wireless networks using system commands
"""

import subprocess
import json
import sys
import os
import io
from collections import Counter

# 윈도우 폰트 깨짐 방지 조건
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

def detect_platform():
    """Detect the operating system platform"""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def get_windows_wifi_interface():
    """
    Auto-detect Wi-Fi interface name on Windows

    Returns:
        str: Wi-Fi interface name or None if not found
    """
    try:
        cmd = "netsh wlan show interfaces"
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=5
        ).decode('cp949', errors='ignore')

        # Extract interface name
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith('Name') or line.startswith('이름'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    interface_name = parts[1].strip()
                    print(f"[INFO] Detected Wi-Fi interface: {interface_name}", file=sys.stderr)
                    return interface_name

        # Fallback to common names
        common_names = ["Wi-Fi", "무선 네트워크 연결", "WLAN"]
        for name in common_names:
            try:
                test_cmd = f'netsh wlan show networks interface="{name}"'
                subprocess.check_output(test_cmd, shell=True, stderr=subprocess.DEVNULL, timeout=3)
                print(f"[INFO] Using fallback interface: {name}", file=sys.stderr)
                return name
            except:
                continue

        return None

    except Exception as e:
        print(f"[ERROR] Failed to detect Wi-Fi interface: {e}", file=sys.stderr)
        return None


def scan_networks_windows(interface_name=None):
    """
    Scan Wi-Fi networks on Windows using netsh command

    Args:
        interface_name (str): Network interface name (auto-detected if None)

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        # Get interface name from environment or auto-detect
        if not interface_name:
            interface_name = os.environ.get('WIFI_INTERFACE_NAME')

        if not interface_name:
            interface_name = get_windows_wifi_interface()

        if not interface_name:
            print("[ERROR] Could not detect Wi-Fi interface", file=sys.stderr)
            return []

        timeout = int(os.environ.get('SCAN_TIMEOUT', '10'))
        cmd = f'netsh wlan show networks interface="{interface_name}" mode=bssid'

        print(f"[INFO] Scanning with interface: {interface_name}", file=sys.stderr)

        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout
        ).decode('cp949', errors='ignore')

        networks = []
        current_ssid = None
        current_channel = None
        current_signal = None

        for line in output.split('\n'):
            line = line.strip()

            # Skip BSSID lines
            if 'BSSID' in line and ':' in line:
                continue

            # Extract SSID
            if line.startswith('SSID 1') or line.startswith('SSID ') or line.startswith('SSID번호'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    current_ssid = parts[1].strip()

            # Extract Channel
            if 'Channel' in line or '채널' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    try:
                        current_channel = int(parts[1].strip())
                    except ValueError:
                        pass

            # Extract Signal
            if 'Signal' in line or '신호' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    try:
                        signal_str = parts[1].strip().replace('%', '')
                        current_signal = int(signal_str)
                    except ValueError:
                        pass

            # Store network data when all three values are available
            if current_ssid and current_channel and current_signal is not None:
                networks.append((current_ssid, current_channel, current_signal))
                current_ssid = None
                current_channel = None
                current_signal = None

        print(f"[INFO] Found {len(networks)} networks", file=sys.stderr)
        return networks

    except subprocess.TimeoutExpired:
        print("[ERROR] Scan timeout", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ERROR] Scanning networks failed: {e}", file=sys.stderr)
        return []


def scan_networks_macos():
    """
    Scan Wi-Fi networks on macOS using airport command

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        timeout = int(os.environ.get('SCAN_TIMEOUT', '10'))
        cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s"

        print(f"[INFO] Scanning Wi-Fi networks on macOS", file=sys.stderr)

        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout
        ).decode('utf-8', errors='ignore')

        networks = []
        lines = output.strip().split('\n')[1:]  # Skip header

        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                ssid = parts[0]
                try:
                    channel = int(parts[2])
                    signal = int(parts[1])
                    # Convert negative signal to positive percentage
                    signal_percent = min(100, max(0, 100 + signal))
                    networks.append((ssid, channel, signal_percent))
                except ValueError:
                    continue

        print(f"[INFO] Found {len(networks)} networks", file=sys.stderr)
        return networks

    except subprocess.TimeoutExpired:
        print("[ERROR] Scan timeout", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ERROR] Scanning networks failed: {e}", file=sys.stderr)
        return []


def scan_networks_linux():
    """
    Scan Wi-Fi networks on Linux using nmcli command

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        timeout = int(os.environ.get('SCAN_TIMEOUT', '10'))

        # First, trigger a scan
        try:
            subprocess.run(
                ["nmcli", "device", "wifi", "rescan"],
                stderr=subprocess.DEVNULL,
                timeout=5
            )
        except:
            pass  # Rescan may fail on some systems, continue anyway

        cmd = "nmcli -f SSID,CHAN,SIGNAL dev wifi"

        print(f"[INFO] Scanning Wi-Fi networks on Linux", file=sys.stderr)

        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=timeout
        ).decode('utf-8', errors='ignore')

        networks = []
        lines = output.strip().split('\n')[1:]  # Skip header

        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                ssid = parts[0]
                try:
                    channel = int(parts[1])
                    signal = int(parts[2])
                    networks.append((ssid, channel, signal))
                except ValueError:
                    continue

        print(f"[INFO] Found {len(networks)} networks", file=sys.stderr)
        return networks

    except subprocess.TimeoutExpired:
        print("[ERROR] Scan timeout", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[ERROR] Scanning networks failed: {e}", file=sys.stderr)
        return []


def scan_networks():
    """
    Scan Wi-Fi networks based on the current platform

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    platform = detect_platform()
    print(f"[INFO] Platform: {platform}", file=sys.stderr)

    if platform == "windows":
        return scan_networks_windows()
    elif platform == "macos":
        return scan_networks_macos()
    elif platform == "linux":
        return scan_networks_linux()
    else:
        print(f"[ERROR] Unsupported platform: {platform}", file=sys.stderr)
        return []


def recommend_channel(networks):
    """
    Recommend the best Wi-Fi channel based on current usage

    Args:
        networks (list): List of tuples (ssid, channel, signal)

    Returns:
        int: Recommended channel number
    """
    if not networks:
        print("[WARNING] No networks found for recommendation", file=sys.stderr)
        return 0

    # Count APs per channel
    channel_counter = Counter(channel for _, channel, _ in networks)

    # Determine band and candidates
    channels = [ch for _, ch, _ in networks]
    max_channel = max(channels) if channels else 0

    if max_channel <= 14:  # 2.4GHz band
        candidates = [1, 6, 11]
        print("[INFO] Detected 2.4GHz band", file=sys.stderr)
    else:  # 5GHz band
        candidates = [36, 40, 44, 48, 149, 153, 157, 161]
        print("[INFO] Detected 5GHz band", file=sys.stderr)

    # Find channel with minimum AP count
    best_channel = min(candidates, key=lambda ch: channel_counter.get(ch, 0))
    best_count = channel_counter.get(best_channel, 0)

    print(f"[INFO] Recommended channel: {best_channel} (APs: {best_count})", file=sys.stderr)

    return best_channel


def get_recommended_channels_list(networks):
    """
    Get a ranked list of recommended channels based on AP distribution

    Args:
        networks (list): List of tuples (ssid, channel, signal)

    Returns:
        list: List of channel recommendations with details
    """
    if not networks:
        return []

    # Count APs per channel
    channel_counter = Counter(channel for _, channel, _ in networks)
    total_aps = len(networks)

    # Determine band and candidates
    channels = [ch for _, ch, _ in networks]
    max_channel = max(channels) if channels else 0

    if max_channel <= 14:  # 2.4GHz band
        candidates = [1, 6, 11]
        band = "2.4GHz"
    else:  # 5GHz band
        candidates = [36, 40, 44, 48, 149, 153, 157, 161]
        band = "5GHz"

    # Build recommendation list with details
    recommendations = []
    for channel in candidates:
        ap_count = channel_counter.get(channel, 0)
        congestion = int((ap_count / total_aps) * 100) if total_aps > 0 else 0

        # Determine recommendation grade
        if ap_count == 0:
            grade = "최적"
        elif congestion <= 10:
            grade = "양호"
        elif congestion <= 25:
            grade = "보통"
        else:
            grade = "혼잡"

        recommendations.append({
            "channel": channel,
            "ap_count": ap_count,
            "congestion": f"{congestion}%",
            "grade": grade,
            "band": band
        })

    # Sort by AP count (ascending) - less APs = better recommendation
    recommendations.sort(key=lambda x: x["ap_count"])

    # Add rank
    for i, rec in enumerate(recommendations):
        rec["rank"] = i + 1

    return recommendations


def calculate_channel_usage(networks):
    """
    Calculate channel usage statistics

    Args:
        networks (list): List of tuples (ssid, channel, signal)

    Returns:
        dict: Channel usage mapping
    """
    channel_counter = Counter(channel for _, channel, _ in networks)
    return dict(channel_counter)


def get_mock_networks():
    """Generate mock network data for testing"""
    return [
        ("KT_GIGA_5G_19DF", 36, 85),
        ("KT_GIGA_51DC", 6, 72),
        ("KT_GIGA_19DF", 11, 65),
        ("ZU NO", 1, 58),
        ("iptime_5G", 149, 45),
        ("SK_WiFi_ABCD", 6, 50),
        ("U+Net_1234", 11, 42),
        ("MyHome_WiFi", 1, 38),
        ("Neighbor_5G", 153, 55),
        ("Coffee_Shop", 6, 48),
        ("Apartment_201", 1, 35),
        ("Office_WiFi", 11, 52),
        ("Public_5G", 157, 40),
        ("Guest_Network", 6, 30),
        ("LG_U+_WiFi", 1, 45),
    ]


def main():
    """Main function to scan networks and output JSON"""
    print("[START] Wi-Fi Channel Analyzer", file=sys.stderr)

    # Check if mock data should be used
    use_mock = os.environ.get('USE_MOCK_DATA', 'false').lower() == 'true'

    if use_mock:
        print("[INFO] Using mock data for testing", file=sys.stderr)
        networks = get_mock_networks()
    else:
        networks = scan_networks()
    channel_usage = calculate_channel_usage(networks)
    recommended = recommend_channel(networks)
    recommended_list = get_recommended_channels_list(networks)

    # Calculate predicted congestion
    total_aps = len(networks)
    best_channel_aps = channel_usage.get(recommended, 0)

    if total_aps > 0:
        predicted = f"{int((best_channel_aps / total_aps) * 100)}%"
    else:
        predicted = "N/A"

    # Get networks using the recommended channel
    recommended_networks = [
        ssid if ssid else "(숨겨진 네트워크)"
        for ssid, channel, _ in networks
        if channel == recommended
    ]

    # Format output
    result = {
        "networks": [
            {
                "ssid": ssid if ssid else "(숨겨진 네트워크)",
                "channel": channel,
                "signal": signal
            }
            for ssid, channel, signal in networks
        ],
        "channel_usage": channel_usage,
        "recommended": recommended,
        "recommended_networks": recommended_networks,
        "recommended_list": recommended_list,
        "predicted": predicted,
        "total_networks": total_aps,
        "platform": detect_platform()
    }

    # Output as JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("[END] Scan completed successfully", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INTERRUPT] Scan interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
