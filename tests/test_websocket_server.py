#!/usr/bin/env python3
"""
Simple WebSocket test server for IoT Device Simulator
Receives and displays WebSocket messages
"""

import asyncio
import websockets
import json

async def handle_message(websocket, path):
    """Handle incoming WebSocket messages"""
    try:
        async for message in websocket:
            # Try to parse as JSON for pretty printing
            try:
                data = json.loads(message)
                print("\nReceived:")
                print(json.dumps(data, indent=2))
                print()
            except json.JSONDecodeError:
                print(f"\nReceived: {message}\n")
            
            # Send acknowledgment
            await websocket.send(json.dumps({"status": "received"}))
            
    except websockets.exceptions.ConnectionClosed:
        pass

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
