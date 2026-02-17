#!/usr/bin/env python3
"""
Simple CoAP test server for IoT Device Simulator
Receives and displays CoAP messages
"""

import asyncio
import aiocoap.resource as resource
import aiocoap
import json
from datetime import datetime

class DataResource(resource.Resource):
    """CoAP resource that receives and displays data"""
    
    async def render_post(self, request):
        """Handle POST requests"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = request.payload.decode('utf-8')
        
        print(f"\n[{timestamp}] Received CoAP POST:")
        
        # Try to parse as JSON for pretty printing
        try:
            data = json.loads(payload)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(payload)
        
        print("─" * 60)
        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Data received")
    
    async def render_put(self, request):
        """Handle PUT requests"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = request.payload.decode('utf-8')
        
        print(f"\n[{timestamp}] Received CoAP PUT:")
        
        # Try to parse as JSON for pretty printing
        try:
            data = json.loads(payload)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(payload)
        
        print("─" * 60)
        
        return aiocoap.Message(code=aiocoap.CHANGED, payload=b"Data updated")

async def main():
    # Create CoAP server
    root = resource.Site()
    
    # Add resources
    root.add_resource(['.well-known', 'core'],
                      resource.WKCResource(root.get_resources_as_linkheader))
    root.add_resource(['data'], DataResource())
    root.add_resource(['iot', 'data'], DataResource())
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       IoT Device Simulator - CoAP Test Server             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\nStarting CoAP server on coap://0.0.0.0:5683")
    print("\nAvailable resources:")
    print("  - coap://localhost:5683/data")
    print("  - coap://localhost:5683/iot/data")
    print("\nWaiting for messages...")
    print("Press Ctrl+C to stop")
    print("─" * 60)
    
    await aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683))
    
    # Run forever
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped")
