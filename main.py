#!/usr/bin/env python3
"""
IoT Device Simulator - Main Module
Simulates IoT devices sending data via MQTT, CoAP, WebSocket, or HTTP
Supports multiple data types and SenML format
"""

import tkinter as tk
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import queue
import ssl

# Import sensor classes
from sensors import (
    SensorReading, LocationReading, TemperatureReading, PressureReading,
    HumidityReading, AccelerometerReading, CO2Reading, FlowReading,
    SoilMoistureReading, SoilPHReading, LightIntensityReading,
    RainReading, WindSpeedReading, DataGenerator
)

# Import GUI
from gui import SimulatorGUI

# Protocol handlers
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False

try:
    from aiocoap import *
    COAP_AVAILABLE = True
except ImportError:
    COAP_AVAILABLE = False

try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

try:
    import requests
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False


# ==================== Format Encoders ====================

class SenMLEncoder:
    """Encodes sensor data in SenML (RFC 8428) format"""
    
    @staticmethod
    def encode(reading: SensorReading, base_name: str = "") -> List[Dict[str, Any]]:
        """Convert a sensor reading to SenML format"""
        senml_pack = []
        base_time = reading.timestamp
        
        if isinstance(reading, LocationReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "latitude", "u": "lat", "v": reading.latitude},
                {"n": "longitude", "u": "lon", "v": reading.longitude},
                {"n": "altitude", "u": "m", "v": reading.altitude},
                {"n": "accuracy", "u": "m", "v": reading.accuracy}
            ]
        elif isinstance(reading, TemperatureReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "temperature", "u": "Cel", "v": reading.temperature}
            ]
        elif isinstance(reading, PressureReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "pressure", "u": "hPa", "v": reading.pressure}
            ]
        elif isinstance(reading, HumidityReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "humidity", "u": "%RH", "v": reading.humidity}
            ]
        elif isinstance(reading, AccelerometerReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "accel_x", "u": "m/s2", "v": reading.x},
                {"n": "accel_y", "u": "m/s2", "v": reading.y},
                {"n": "accel_z", "u": "m/s2", "v": reading.z}
            ]
        elif isinstance(reading, CO2Reading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "co2", "u": "ppm", "v": reading.co2_ppm}
            ]
        elif isinstance(reading, FlowReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "flow_rate", "u": "L/min", "v": reading.flow_rate},
                {"n": "total_volume", "u": "L", "v": reading.total_volume}
            ]
        elif isinstance(reading, SoilMoistureReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "soil_moisture", "u": "%", "v": reading.moisture}
            ]
        elif isinstance(reading, SoilPHReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "soil_ph", "u": "pH", "v": reading.ph}
            ]
        elif isinstance(reading, LightIntensityReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "light", "u": "lx", "v": reading.intensity}
            ]
        elif isinstance(reading, RainReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "rainfall", "u": "mm/h", "v": reading.rainfall}
            ]
        elif isinstance(reading, WindSpeedReading):
            senml_pack = [
                {"bn": base_name, "bt": base_time, "n": "wind_speed", "u": "m/s", "v": reading.speed},
                {"n": "wind_direction", "u": "deg", "v": reading.direction}
            ]
        
        return senml_pack


class JSONEncoder:
    """Simple JSON encoder for sensor data"""
    
    @staticmethod
    def encode(reading: SensorReading) -> Dict[str, Any]:
        return reading.to_dict()


# ==================== Protocol Handlers ====================

class ProtocolHandler:
    """Base class for protocol handlers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connected = False
    
    def connect(self):
        raise NotImplementedError
    
    def disconnect(self):
        raise NotImplementedError
    
    def send(self, data: str):
        raise NotImplementedError


class MQTTHandler(ProtocolHandler):
    """MQTT protocol handler with TLS/mTLS support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt is required for MQTT support")
        
        self.client = mqtt.Client(client_id=config.get('client_id', ''))
        
        # Configure TLS if enabled
        tls_mode = config.get('tls_mode', 'none')
        if tls_mode in ['tls', 'mtls']:
            ca_cert = config.get('ca_cert')
            client_cert = config.get('client_cert') if tls_mode == 'mtls' else None
            client_key = config.get('client_key') if tls_mode == 'mtls' else None
            
            # Set up TLS
            self.client.tls_set(
                ca_certs=ca_cert if ca_cert else None,
                certfile=client_cert,
                keyfile=client_key,
                cert_reqs=ssl.CERT_REQUIRED if ca_cert else ssl.CERT_NONE,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
            
            # Enable TLS insecure mode if no CA cert provided (for testing)
            if not ca_cert:
                self.client.tls_insecure_set(True)
    
    def connect(self):
        try:
            broker = self.config.get('broker', 'localhost')
            port = self.config.get('port', 1883)
            
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            self.connected = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
    
    def send(self, data: str):
        if not self.connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        topic = self.config.get('topic', 'iot/data')
        self.client.publish(topic, data, qos=1)


class HTTPHandler(ProtocolHandler):
    """HTTP/HTTPS protocol handler with TLS support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not HTTP_AVAILABLE:
            raise ImportError("requests is required for HTTP support")
        
        # Configure session with TLS if enabled
        self.session = requests.Session()
        tls_mode = config.get('tls_mode', 'none')
        
        if tls_mode in ['tls', 'mtls']:
            ca_cert = config.get('ca_cert')
            client_cert = config.get('client_cert')
            client_key = config.get('client_key')
            
            if ca_cert:
                self.session.verify = ca_cert
            
            if tls_mode == 'mtls' and client_cert and client_key:
                self.session.cert = (client_cert, client_key)
    
    def connect(self):
        # HTTP is connectionless, mark as connected
        self.connected = True
    
    def disconnect(self):
        self.session.close()
        self.connected = False
    
    def send(self, data: str):
        url = self.config.get('url', 'http://localhost:8080/data')
        method = self.config.get('method', 'POST').upper()
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'POST':
                response = self.session.post(url, data=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = self.session.put(url, data=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"HTTP request failed: {e}")


class WebSocketHandler(ProtocolHandler):
    """WebSocket protocol handler with WSS support"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not WS_AVAILABLE:
            raise ImportError("websocket-client is required for WebSocket support")
        
        self.ws = None
        
        # Configure TLS options if enabled
        self.sslopt = {}
        tls_mode = config.get('tls_mode', 'none')
        
        if tls_mode in ['tls', 'mtls']:
            ca_cert = config.get('ca_cert')
            client_cert = config.get('client_cert')
            client_key = config.get('client_key')
            
            if ca_cert:
                self.sslopt['ca_certs'] = ca_cert
            
            if tls_mode == 'mtls' and client_cert and client_key:
                self.sslopt['certfile'] = client_cert
                self.sslopt['keyfile'] = client_key
    
    def connect(self):
        url = self.config.get('url', 'ws://localhost:8080/')
        
        try:
            if self.sslopt:
                self.ws = websocket.create_connection(url, sslopt=self.sslopt)
            else:
                self.ws = websocket.create_connection(url)
            self.connected = True
        except Exception as e:
            raise ConnectionError(f"Failed to connect to WebSocket: {e}")
    
    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.connected = False
    
    def send(self, data: str):
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to WebSocket")
        
        try:
            self.ws.send(data)
        except Exception as e:
            raise ConnectionError(f"Failed to send data: {e}")


class CoAPHandler(ProtocolHandler):
    """CoAP protocol handler (DTLS support requires additional setup)"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        if not COAP_AVAILABLE:
            raise ImportError("aiocoap is required for CoAP support")
        
        import asyncio
        self.loop = asyncio.new_event_loop()
        self.context = None
    
    def connect(self):
        # CoAP is connectionless
        self.connected = True
    
    def disconnect(self):
        self.connected = False
    
    def send(self, data: str):
        import asyncio
        from aiocoap import Context, Message, POST
        
        url = self.config.get('url', 'coap://localhost/data')
        
        async def _send():
            if not self.context:
                self.context = await Context.create_client_context()
            
            request = Message(code=POST, payload=data.encode('utf-8'), uri=url)
            request.opt.content_format = 50  # application/json
            
            try:
                response = await self.context.request(request).response
                return response
            except Exception as e:
                raise ConnectionError(f"CoAP request failed: {e}")
        
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(_send())
        except Exception as e:
            raise ConnectionError(f"Failed to send CoAP message: {e}")


# ==================== IoT Device Simulator ====================

class IoTDeviceSimulator:
    """Main IoT device simulator"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.generators: Dict[str, DataGenerator] = {}
        self.protocol_handler: Optional[ProtocolHandler] = None
        self.format_encoder = JSONEncoder
        self.running = False
        self.thread = None
        self.interval = 5.0  # seconds
        self.message_queue = queue.Queue()
    
    def add_generator(self, name: str, generator: DataGenerator):
        """Add a data generator"""
        self.generators[name] = generator
    
    def set_protocol(self, protocol: str, config: Dict[str, Any]):
        """Set the communication protocol"""
        if self.protocol_handler:
            self.protocol_handler.disconnect()
        
        if protocol.lower() == 'mqtt':
            self.protocol_handler = MQTTHandler(config)
        elif protocol.lower() == 'http' or protocol.lower() == 'https':
            self.protocol_handler = HTTPHandler(config)
        elif protocol.lower() == 'ws' or protocol.lower() == 'websocket':
            self.protocol_handler = WebSocketHandler(config)
        elif protocol.lower() == 'coap':
            self.protocol_handler = CoAPHandler(config)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")
    
    def set_format(self, format_type: str):
        """Set the data format"""
        if format_type.lower() == 'senml':
            self.format_encoder = SenMLEncoder
        elif format_type.lower() == 'json':
            self.format_encoder = JSONEncoder
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def start(self):
        """Start the simulator"""
        if self.running:
            return
        
        if not self.protocol_handler:
            raise ValueError("Protocol handler not set")
        
        if not self.generators:
            raise ValueError("No data generators configured")
        
        self.protocol_handler.connect()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the simulator"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.protocol_handler:
            self.protocol_handler.disconnect()
    
    def _run(self):
        """Main simulation loop"""
        while self.running:
            try:
                # Generate data from all generators
                all_data = {}
                
                for name, generator in self.generators.items():
                    reading = generator.generate()
                    
                    # Encode the data
                    if self.format_encoder == SenMLEncoder:
                        encoded = SenMLEncoder.encode(reading, base_name=f"{self.device_id}/{name}/")
                        all_data[name] = encoded
                    else:
                        all_data[name] = JSONEncoder.encode(reading)
                
                # Convert to JSON string
                payload = json.dumps(all_data, indent=2)
                
                # Send via protocol
                self.protocol_handler.send(payload)
                
                # Log to queue
                self.message_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Sent: {len(payload)} bytes")
                
            except Exception as e:
                self.message_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
            
            time.sleep(self.interval)


# ==================== Main ====================

def main():
    root = tk.Tk()
    app = SimulatorGUI(root, IoTDeviceSimulator)
    root.mainloop()


if __name__ == "__main__":
    main()
