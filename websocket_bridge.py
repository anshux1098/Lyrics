#!/usr/bin/env python3
"""
LyricSh WebSocket Bridge
Receives UDP broadcasts and forwards them to connected WebSocket clients.
This lets the HTML renderer (browser) receive lyric updates in real-time.

Usage: python websocket_bridge.py
Requires: pip install websockets
"""

import asyncio
import json
import os
import socket
import time

try:
    import websockets
except ImportError:
    print("ERROR: websockets not installed. Run: pip install websockets")
    exit(1)

BROADCAST_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "Temp",
    "lyricsh_broadcast.json",
)
WS_PORT = 5006

clients = set()


async def watch_file_and_broadcast():
    """Watch the JSON file and push updates to all connected WebSocket clients."""
    global clients
    last_payload = None

    while True:
        try:
            with open(BROADCAST_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            payload = json.dumps(data)

            if payload != last_payload:
                last_payload = payload
                # Send to all connected clients
                if clients:
                    disconnected = set()
                    for ws in clients:
                        try:
                            await ws.send(payload)
                        except Exception:
                            disconnected.add(ws)
                    clients -= disconnected

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

        await asyncio.sleep(0.05)  # 50ms poll


async def handler(websocket):
    """Handle WebSocket connections."""
    clients.add(websocket)
    print(f"[LyricSh WS] Client connected ({len(clients)} total)")

    # Send current state immediately on connect
    try:
        with open(BROADCAST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        await websocket.send(json.dumps(data))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    try:
        async for _ in websocket:
            pass  # We don't expect messages from the client
    finally:
        clients.discard(websocket)
        print(f"[LyricSh WS] Client disconnected ({len(clients)} remaining)")


async def main():
    print(f"[LyricSh WS] Starting WebSocket server on port {WS_PORT}")
    print(f"[LyricSh WS] Watching: {BROADCAST_FILE}")

    async with websockets.serve(handler, "0.0.0.0", WS_PORT):
        await watch_file_and_broadcast()


if __name__ == "__main__":
    asyncio.run(main())
