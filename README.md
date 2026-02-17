# IoT Device Simulator

A comprehensive IoT device simulator that generates realistic sensor data and sends it using various protocols (MQTT, CoAP, WebSocket, HTTP) in multiple formats including SenML.

## Features

### 🌡️ Sensor Types

**Environmental Sensors:**
- **Location (GPS)**: Latitude, longitude, altitude, and accuracy
- **Temperature**: Celsius measurements with realistic fluctuations
- **Pressure**: Atmospheric pressure in hPa
- **Humidity**: Relative humidity percentage
- **Light Intensity**: Light levels in lux
- **Rain/Precipitation**: Rainfall in mm/h
- **Wind Speed**: Wind speed (m/s) and direction (degrees)

**Agricultural Sensors:**
- **Soil Moisture**: Soil water content percentage
- **Soil pH**: Soil acidity/alkalinity (pH scale)

**Air Quality Sensors:**
- **CO2 (PPM)**: Carbon dioxide concentration in parts per million

**Industrial/Utility Sensors:**
- **Flow Rate**: Liquid/water flow (L/min) with total volume tracking
- **Accelerometer**: 3-axis acceleration data (x, y, z)

### 📡 Supported Protocols
- **MQTT**: Lightweight messaging protocol for IoT (with TLS/mTLS support)
- **HTTP/HTTPS**: Standard web protocol (POST/PUT) with SSL/TLS
- **WebSocket/WSS**: Full-duplex communication with secure WebSocket
- **CoAP**: Constrained Application Protocol for IoT

### 🔒 Security Features
- **TLS**: Server authentication with certificate verification
- **mTLS**: Mutual authentication (client and server certificates)
- **Certificate Management**: GUI-based certificate file selection
- **Flexible Configuration**: Support for custom CA, client certificates, and private keys

### 📊 Data Formats
- **JSON**: Standard JSON format with all sensor readings
- **SenML**: Sensor Measurement Lists (RFC 8428) format

### 🎨 GUI Features
- Easy-to-use graphical interface
- Real-time log monitoring
- Configurable sensor selection
- Protocol-specific settings
- TLS/mTLS configuration with certificate browser
- Adjustable transmission interval

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Quick Start with Makefile

The easiest way to get started:

```bash
# Install dependencies and run the simulator
make run

# Or just install dependencies
make install

# View all available make targets
make help
```

**Test Infrastructure** (requires Docker for MQTT):
```bash
# Start MQTT broker
make mqtt-up

# Start HTTP test server (in another terminal)
make test-server

# View MQTT broker logs
make mqtt-logs

# Stop MQTT broker
make mqtt-down
```

**Cleanup:**
```bash
# Remove virtual environment
make clean
```

### Manual Installation

```bash
# Create virtual environment (optional but recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

Or install individually:

```bash
# For MQTT support
pip install paho-mqtt

# For HTTP support
pip install requests

# For WebSocket support
pip install websocket-client

# For CoAP support
pip install aiocoap
```

## Usage

### Launch the GUI

```bash
python main.py
```

### Using the GUI

1. **Configure Device**
   - Set a unique Device ID
   - Set the transmission interval (in seconds)

2. **Select Sensors**
   - Check the sensors you want to simulate
   - At least one sensor must be selected

3. **Choose Protocol**
   - Select from MQTT, HTTP, WebSocket, or CoAP
   - Configure protocol-specific settings:
     - **MQTT**: Broker address, port, topic
     - **HTTP**: URL, method (POST/PUT)
     - **WebSocket**: WebSocket URL
     - **CoAP**: CoAP URL

4. **Configure Security (Optional)**
   - **None**: No encryption (default for testing)
   - **TLS**: Server authentication only
     - GUI shows: CA certificate field only
     - CA certificate is optional (uses system CA if not provided)
     - Required for self-signed server certificates
   - **mTLS**: Mutual authentication (recommended for production)
     - GUI shows: CA certificate, client certificate, and client private key fields
     - All three certificates are required
   - The GUI automatically shows/hides certificate fields based on your selection
   - See [TLS_GUIDE.md](TLS_GUIDE.md) for certificate generation

5. **Select Format**
   - **JSON**: Standard JSON with nested sensor data
   - **SenML**: RFC 8428 compliant format

6. **Start Simulation**
   - Click "Start Simulation" to begin sending data
   - Monitor the log output for transmission status
   - Click "Stop Simulation" to stop

## Protocol Configuration Examples

### MQTT
```
Broker: test.mosquitto.org
Port: 1883
Topic: iot/devices/your-device-id
```

### HTTP
```
URL: http://your-server.com:8080/api/data
Method: POST
```

### WebSocket
```
URL: ws://your-server.com:8080/ws
```

### CoAP
```
URL: coap://your-server.com/api/data
```

## Data Format Examples

### JSON Format
```json
{
  "temperature": {
    "timestamp": 1708185600.123,
    "device_id": "device_001",
    "temperature": 22.5,
    "unit": "celsius"
  },
  "location": {
    "timestamp": 1708185600.123,
    "device_id": "device_001",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "altitude": 10.5,
    "accuracy": 2.3
  }
}
```

### SenML Format
```json
{
  "temperature": [
    {
      "bn": "device_001/temperature/",
      "bt": 1708185600.123,
      "n": "temperature",
      "u": "Cel",
      "v": 22.5
    }
  ],
  "location": [
    {
      "bn": "device_001/location/",
      "bt": 1708185600.123,
      "n": "latitude",
      "u": "lat",
      "v": 37.7749
    },
    {
      "n": "longitude",
      "u": "lon",
      "v": -122.4194
    },
    {
      "n": "altitude",
      "u": "m",
      "v": 10.5
    },
    {
      "n": "accuracy",
      "u": "m",
      "v": 2.3
    }
  ]
}
```

## Testing Locally

### Quick Start with Docker (Recommended)

Start **all test servers** with a single command:

```bash
# Start all test servers (MQTT, HTTP, WebSocket, CoAP)
make servers-up

# Run the simulator (in another terminal)
make run

# View logs from all servers
make servers-logs

# Stop all servers
make servers-down
```

**All servers will be available at:**
- **MQTT**: localhost:1883
- **HTTP**: localhost:8080
- **WebSocket**: ws://localhost:8765
- **CoAP**: coap://localhost:5683

**Start individual servers:**
```bash
make mqtt-up    # MQTT broker only
make http-up    # HTTP server only
make ws-up      # WebSocket server only
make coap-up    # CoAP server only
```

### Test with MQTT

**Option 1: Using Docker (Recommended)**
```bash
# Start MQTT broker
make mqtt-up

# In another terminal, subscribe to messages
docker exec -it iot-mqtt-broker mosquitto_sub -t "iot/#"

# Or view logs
docker compose logs -f mosquitto
```

**Option 2: Install Mosquitto locally**
1. Install Mosquitto:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install mosquitto mosquitto-clients
   
   # macOS
   brew install mosquitto
   ```

2. Subscribe to the topic:
   ```bash
   mosquitto_sub -h localhost -t "iot/data"
   ```

### Test with HTTP

**Option 1: Using Docker (Recommended)**
```bash
# Start HTTP server
make http-up

# View received data
docker compose logs -f http-server
```

**Option 2: Using Python test server**
```bash
# Start HTTP test server locally
python tests/test_http_server.py
```

### Test with WebSocket

**Using Docker:**
```bash
# Start WebSocket server
make ws-up

# View received data
docker compose logs -f websocket-server
```

**Or run locally:**
```bash
python tests/test_websocket_server.py
```

### Test with CoAP

**Using Docker:**
```bash
# Start CoAP server
make coap-up

# View received data
docker compose logs -f coap-server
```

**Or run locally:**
```bash
python tests/test_coap_server.py
```

### Complete Testing Workflow

```bash
# Terminal 1: Start all test servers
make servers-up

# Terminal 2: Run the simulator
make run

# Terminal 3: Monitor logs (optional)
make servers-logs

# When done, stop all servers
make servers-down
make test-server

# Or manually
python test_http_server.py
```

**Option 2: Create a simple test server**

Create a simple test server (`test_server.py`):
```python
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        print(f"Received data: {body.decode('utf-8')}")
        self.send_response(200)
        self.end_headers()

HTTPServer(('localhost', 8080), Handler).serve_forever()
```

Run it: `python test_server.py`

### Test with TLS/mTLS

1. Generate test certificates:
   ```bash
   ./scripts/generate-certs.sh
   ```
   This creates certificates in `./certs/` directory

2. For MQTT with TLS, configure Mosquitto with TLS support (see [TLS_GUIDE.md](TLS_GUIDE.md))

3. In the simulator GUI:
   - Select security mode (TLS or mTLS)
   - Browse and select appropriate certificate files
   - Update ports (e.g., MQTT port 8883 for TLS)

For detailed TLS/mTLS configuration and testing, see **[TLS_GUIDE.md](TLS_GUIDE.md)**

## Architecture

The simulator is designed with modularity in mind:

- **Data Generators**: Each sensor type has its own generator class that produces realistic data
- **Format Encoders**: Support for multiple output formats (JSON, SenML)
- **Protocol Handlers**: Abstracted protocol implementations for easy extension
- **GUI**: Tkinter-based interface for easy configuration and monitoring

## Extending the Simulator

### Adding a New Sensor

```python
class CustomSensorGenerator(DataGenerator):
    def __init__(self, device_id: str):
        super().__init__(device_id)
        # Initialize your sensor
    
    def generate(self) -> SensorReading:
        # Generate and return sensor reading
        pass
```

### Adding a New Protocol

```python
class CustomProtocolHandler(ProtocolHandler):
    def connect(self):
        # Implement connection logic
        pass
    
    def disconnect(self):
        # Implement disconnection logic
        pass
    
    def send(self, data: str):
        # Implement data transmission
        pass
```

## Troubleshooting

### "Module not found" errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### MQTT connection fails
- Check if the broker is running and accessible
- Verify the broker address and port
- Check firewall settings

### HTTP connection fails
- Verify the server is running and the URL is correct
- Check if the server accepts the HTTP method (POST/PUT)

### CoAP issues
- CoAP support is experimental and requires Python 3.7+
- Some systems may need additional dependencies

## License

MIT License - Feel free to use and modify as needed.

## Acknowledgments

Inspired by the [AWS IoT Device Simulator](https://github.com/aws-solutions/iot-device-simulator) project.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.
