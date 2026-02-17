#!/usr/bin/env python3
"""
Simple WebSocket test server for IoT Device Simulator
Receives and displays WebSocket messages
"""

import asyncio
import websockets
import json
from datetime import datetime

async def handle_message(websocket, path):
    """Handle incoming WebSocket messages"""
    client_address = websocket.remote_address
    print(f"✓ New connection from {client_address[0]}:{client_address[1]}")
    
    try:
        async for message in websocket:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to parse as JSON for pretty printing
            try:
                data = json.loads(message)
                print(f"\n[{timestamp}] Received from {client_address[0]}:")
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                print(f"\n[{timestamp}] Received from {client_address[0]}:")
                print(message)
            
            # Send acknowledgment
            await websocket.send(json.dumps({"status": "received", "timestamp": timestamp}))
            
    except websockets.exceptions.ConnectionClosed:
        print(f"✗ Connection closed from {client_address[0]}:{client_address[1]}")

async def main():
    host = "0.0.0.0"
    port = 8765
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║      IoT Device Simulator - WebSocket Test Server         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"\nStarting WebSocket server on ws://{host}:{port}")
    print(f"Waiting for connections...\n")
    print("Press Ctrl+C to stop")
    print("─" * 60)
    
    async with websockets.serve(handle_message, host, port):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
