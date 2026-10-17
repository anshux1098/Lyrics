#!/usr/bin/env python3
"""
LyricSh UDP Broadcaster
Reads the JSON file that Rainmeter's Lua script writes,
broadcasts it over UDP so the PC renderer or Raspberry Pi can receive it.

Usage: python udp_broadcaster.py
"""

import json
import os
import socket
import sys
import time

BROADCAST_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Temp",
    "lyricsh_broadcast.json",
)
UDP_PORT = 5005
BROADCAST_ADDR = ("255.255.255.255", UDP_PORT)  # subnet broadcast
POLL_INTERVAL = 0.05  # 50ms


def read_broadcast_file():
    """Read the JSON file, return dict or None."""
    try:
        with open(BROADCAST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    last_payload = None
    print(f"[LyricSh] Broadcasting on UDP port {UDP_PORT}")
    print(f"[LyricSh] Watching: {BROADCAST_FILE}")

    try:
        while True:
            data = read_broadcast_file()
            if data is None:
                time.sleep(POLL_INTERVAL)
                continue

            payload = json.dumps(data).encode("utf-8")

            # Only re-send if changed
            if payload != last_payload:
                last_payload = payload
                sock.sendto(payload, BROADCAST_ADDR)
                print(f"[LyricSh] → {data.get('current', '?')}")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\n[LyricSh] Stopped.")
    finally:
        sock.close()


if __name__ == "__main__":
    main()
