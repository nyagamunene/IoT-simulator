#!/usr/bin/env python3
"""
Simple HTTP test server for IoT Device Simulator
Receives and displays data sent from the simulator
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime


class IoTDataHandler(BaseHTTPRequestHandler):
    """Handler for IoT data requests"""
    
    def do_POST(self):
        """Handle POST requests"""
        self._handle_request()
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._handle_request()
    
    def _handle_request(self):
        """Process incoming data"""
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Read and parse body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Pretty print the received data
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n{'='*60}")
            print(f"[{timestamp}] Received Data from {self.client_address[0]}")
            print(f"{'='*60}")
            print(json.dumps(data, indent=2))
            print(f"{'='*60}\n")
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'success', 'message': 'Data received'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            print(f"Error processing request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'error', 'message': str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server(host='localhost', port=8080):
    """Start the HTTP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, IoTDataHandler)
    
    print(f"""
╔════════════════════════════════════════════════════════════╗
║          IoT Device Simulator - Test HTTP Server          ║
╚════════════════════════════════════════════════════════════╝

Server running on: http://{host}:{port}/data
Waiting for data from IoT Device Simulator...

Press Ctrl+C to stop the server
""")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        httpd.server_close()


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    
    run_server(host, port)
