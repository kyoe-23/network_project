#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wi-Fi Network Scanner Utility
Scans nearby wireless networks using system commands
"""

import subprocess
import json
import sys
from collections import Counter


def detect_platform():
    """Detect the operating system platform"""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    else:
        return "linux"


def scan_networks_windows(interface_name="Wi-Fi"):
    """
    Scan Wi-Fi networks on Windows using netsh command

    Args:
        interface_name (str): Network interface name

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        cmd = f'netsh wlan show networks interface="{interface_name}" mode=bssid'
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=10
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

        return networks

    except Exception as e:
        print(f"Error scanning networks: {e}", file=sys.stderr)
        return []


def scan_networks_macos():
    """
    Scan Wi-Fi networks on macOS using airport command

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s"
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=10
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
                    networks.append((ssid, channel, abs(signal)))
                except ValueError:
                    continue

        return networks

    except Exception as e:
        print(f"Error scanning networks: {e}", file=sys.stderr)
        return []


def scan_networks_linux():
    """
    Scan Wi-Fi networks on Linux using nmcli command

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    try:
        cmd = "nmcli -f SSID,CHAN,SIGNAL dev wifi"
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.DEVNULL,
            timeout=10
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

        return networks

    except Exception as e:
        print(f"Error scanning networks: {e}", file=sys.stderr)
        return []


def scan_networks():
    """
    Scan Wi-Fi networks based on the current platform

    Returns:
        list: List of tuples (ssid, channel, signal)
    """
    platform = detect_platform()

    if platform == "windows":
        return scan_networks_windows()
    elif platform == "macos":
        return scan_networks_macos()
    elif platform == "linux":
        return scan_networks_linux()
    else:
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
        return 0

    # Count APs per channel
    channel_counter = Counter(channel for _, channel, _ in networks)

    # Determine band and candidates
    channels = [ch for _, ch, _ in networks]
    max_channel = max(channels) if channels else 0

    if max_channel <= 14:  # 2.4GHz band
        candidates = [1, 6, 11]
    else:  # 5GHz band
        candidates = [36, 40, 44, 48, 149, 153, 157, 161]

    # Find channel with minimum AP count
    best_channel = min(candidates, key=lambda ch: channel_counter.get(ch, 0))

    return best_channel


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


def main():
    """Main function to scan networks and output JSON"""
    networks = scan_networks()
    channel_usage = calculate_channel_usage(networks)
    recommended = recommend_channel(networks)

    # Calculate predicted congestion
    total_aps = len(networks)
    best_channel_aps = channel_usage.get(recommended, 0)

    if total_aps > 0:
        predicted = f"{int((best_channel_aps / total_aps) * 100)}%"
    else:
        predicted = "N/A"

    # Format output
    result = {
        "networks": [
            {
                "ssid": ssid,
                "channel": channel,
                "signal": signal
            }
            for ssid, channel, signal in networks
        ],
        "channel_usage": channel_usage,
        "recommended": recommended,
        "predicted": predicted
    }

    # Output as JSON
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
