#!/usr/bin/env python3
"""
IoT Device Simulator - Main Module
Simulates IoT devices sending data via MQTT, CoAP, WebSocket, or HTTP
Supports multiple data types and SenML format
"""

import tkinter as tk
import ttkbootstrap as ttk_bootstrap
import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import queue
import ssl
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import sensor classes
from lib.sensors import (
    SensorReading, LocationReading, TemperatureReading, PressureReading,
    HumidityReading, AccelerometerReading, GyroscopeReading, CO2Reading, FlowReading,
    SoilMoistureReading, SoilPHReading, LightIntensityReading,
    RainReading, WindSpeedReading, FuelConsumptionReading, SpeedReading,
    WaterMeterReading, WaterPHReading, WaterTurbidityReading,
    WaterTDSReading, ChlorineReading,
    DataGenerator, MotionState
)

# Import actuator classes
from lib.actuators import Actuator, BulbActuator, RelayActuator, ThermostatActuator

# Import GUI
from lib.publisher_gui import SimulatorGUI

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


# ==================== Unit Converter ====================

class UnitConverter:
    """Converts sensor values between metric and imperial units"""
    
    @staticmethod
    def temperature(celsius: float, to_imperial: bool = False) -> tuple:
        """Convert temperature. Returns (value, unit)"""
        if to_imperial:
            fahrenheit = (celsius * 9/5) + 32
            return round(fahrenheit, 2), "°F"
        return round(celsius, 2), "°C"
    
    @staticmethod
    def pressure(hpa: float, to_imperial: bool = False) -> tuple:
        """Convert pressure. Returns (value, unit)"""
        if to_imperial:
            inhg = hpa * 0.02953
            return round(inhg, 2), "inHg"
        return round(hpa, 2), "hPa"
    
    @staticmethod
    def speed(ms: float, to_imperial: bool = False) -> tuple:
        """Convert speed from m/s. Returns (value, unit)"""
        if to_imperial:
            mph = ms * 2.23694
            return round(mph, 1), "mph"
        # Return km/h for metric (more common than m/s)
        kmh = ms * 3.6
        return round(kmh, 1), "km/h"
    
    @staticmethod
    def altitude(meters: float, to_imperial: bool = False) -> tuple:
        """Convert altitude. Returns (value, unit)"""
        if to_imperial:
            feet = meters * 3.28084
            return round(feet, 1), "ft"
        return round(meters, 1), "m"
    
    @staticmethod
    def rainfall(mmh: float, to_imperial: bool = False) -> tuple:
        """Convert rainfall rate. Returns (value, unit)"""
        if to_imperial:
            inh = mmh * 0.03937
            return round(inh, 2), "in/h"
        return round(mmh, 2), "mm/h"
    
    @staticmethod
    def flow_rate(lpm: float, to_imperial: bool = False) -> tuple:
        """Convert flow rate. Returns (value, unit)"""
        if to_imperial:
            gpm = lpm * 0.264172
            return round(gpm, 2), "gal/min"
        return round(lpm, 2), "L/min"
    
    @staticmethod
    def volume(liters: float, to_imperial: bool = False) -> tuple:
        """Convert volume. Returns (value, unit)"""
        if to_imperial:
            gallons = liters * 0.264172
            return round(gallons, 2), "gal"
        return round(liters, 2), "L"


# ==================== Format Encoders ====================

class SenMLEncoder:
    """Encodes sensor data in SenML (RFC 8428) format"""
    
    @staticmethod
    def encode(reading: SensorReading, base_name: str = "", unit_system: str = "metric") -> List[Dict[str, Any]]:
        """Convert a sensor reading to SenML format with unit conversion"""
        senml_pack = []
        # Convert timestamp to nanoseconds (integer)
        base_time = int(reading.timestamp * 1_000_000_000)
        to_imperial = (unit_system == "imperial")
        
        if isinstance(reading, LocationReading):
            # Format coordinates as JSON string for vs (string value) field
            coordinates_json = json.dumps({
                "latitude": reading.latitude,
                "longitude": reading.longitude
            }, ensure_ascii=False)
            alt_value, alt_unit = UnitConverter.altitude(reading.altitude, to_imperial)
            senml_pack = [
                {"n": "coordinates", "bt": base_time, "vs": coordinates_json},
                {"n": "altitude", "u": alt_unit, "v": alt_value}
            ]
        elif isinstance(reading, TemperatureReading):
            temp_value, temp_unit = UnitConverter.temperature(reading.temperature, to_imperial)
            senml_pack = [
                {"n": "temperature", "bu": temp_unit, "u": temp_unit, "bt": base_time, "v": temp_value}
            ]
        elif isinstance(reading, PressureReading):
            press_value, press_unit = UnitConverter.pressure(reading.pressure, to_imperial)
            senml_pack = [
                {"n": "pressure", "bu": press_unit, "u": press_unit, "bt": base_time, "v": press_value}
            ]
        elif isinstance(reading, HumidityReading):
            senml_pack = [
                {"n": "humidity", "bu": "%RH", "u": "%RH", "bt": base_time, "v": reading.humidity}
            ]
        elif isinstance(reading, AccelerometerReading):
            # Horizontal acceleration magnitude (x,y only; z includes gravity)
            accel_magnitude = round((reading.x ** 2 + reading.y ** 2) ** 0.5, 3)
            senml_pack = [
                {"n": "accel_x", "bu": "m/s2", "u": "m/s2", "bt": base_time, "v": reading.x},
                {"n": "accel_y", "u": "m/s2", "v": reading.y},
                {"n": "accel_z", "u": "m/s2", "v": reading.z},
                {"n": "acceleration", "u": "m/s2", "v": accel_magnitude},
            ]
        elif isinstance(reading, GyroscopeReading):
            senml_pack = [
                {"n": "gyro_x", "bu": "deg/s", "u": "deg/s", "bt": base_time, "v": reading.x},
                {"n": "gyro_y", "u": "deg/s", "v": reading.y},
                {"n": "gyro_z", "u": "deg/s", "v": reading.z}
            ]
        elif isinstance(reading, CO2Reading):
            senml_pack = [
                {"n": "co2", "bu": "ppm", "u": "ppm", "bt": base_time, "v": reading.co2_ppm}
            ]
        elif isinstance(reading, FlowReading):
            flow_value, flow_unit = UnitConverter.flow_rate(reading.flow_rate, to_imperial)
            vol_value, vol_unit = UnitConverter.volume(reading.total_volume, to_imperial)
            senml_pack = [
                {"n": "flow_rate", "bu": flow_unit, "u": flow_unit, "bt": base_time, "v": flow_value},
                {"n": "total_volume", "u": vol_unit, "v": vol_value}
            ]
        elif isinstance(reading, SoilMoistureReading):
            senml_pack = [
                {"n": "soil_moisture", "bu": "%", "u": "%", "bt": base_time, "v": reading.moisture}
            ]
        elif isinstance(reading, SoilPHReading):
            senml_pack = [
                {"n": "soil_ph", "bu": "pH", "u": "pH", "bt": base_time, "v": reading.ph}
            ]
        elif isinstance(reading, LightIntensityReading):
            senml_pack = [
                {"n": "light", "bu": "lx", "u": "lx", "bt": base_time, "v": reading.intensity}
            ]
        elif isinstance(reading, RainReading):
            rain_value, rain_unit = UnitConverter.rainfall(reading.rainfall, to_imperial)
            senml_pack = [
                {"n": "rainfall", "bu": rain_unit, "u": rain_unit, "bt": base_time, "v": rain_value}
            ]
        elif isinstance(reading, WindSpeedReading):
            wind_value, wind_unit = UnitConverter.speed(reading.speed, to_imperial)
            senml_pack = [
                {"n": "wind_speed", "bu": wind_unit, "u": wind_unit, "bt": base_time, "v": wind_value},
                {"n": "wind_direction", "u": "deg", "v": reading.direction}
            ]
        elif isinstance(reading, SpeedReading):
            speed_value, speed_unit = UnitConverter.speed(reading.speed, to_imperial)
            senml_pack = [
                {"n": "speed", "bu": speed_unit, "u": speed_unit, "bt": base_time, "v": speed_value},
                {"n": "heading", "u": "deg", "v": reading.heading}
            ]
        elif isinstance(reading, FuelConsumptionReading):
            # Fuel consumption already has both units, select based on system
            if to_imperial:
                total_vol, vol_unit = UnitConverter.volume(reading.total_consumed, to_imperial)
                senml_pack = [
                    {"n": "fuel_consumption", "bu": "MPG", "u": "MPG", "bt": base_time, "v": reading.consumption_mpg},
                    {"n": "fuel_level", "u": "%", "v": reading.fuel_level},
                    {"n": "fuel_total_consumed", "u": vol_unit, "v": total_vol}
                ]
            else:
                senml_pack = [
                    {"n": "fuel_consumption", "bu": "L/100km", "u": "L/100km", "bt": base_time, "v": reading.consumption_l_100km},
                    {"n": "fuel_level", "u": "%", "v": reading.fuel_level},
                    {"n": "fuel_total_consumed", "u": "L", "v": reading.total_consumed}
                ]
        elif isinstance(reading, WaterMeterReading):
            flow_value, flow_unit = UnitConverter.flow_rate(reading.flow_rate, to_imperial)
            vol_value, vol_unit = UnitConverter.volume(reading.cumulative_volume * 1000, to_imperial)  # m³ → L
            senml_pack = [
                {"n": "water_flow_rate", "bu": flow_unit, "u": flow_unit, "bt": base_time, "v": flow_value},
                {"n": "water_cumulative_volume", "u": vol_unit, "v": vol_value},
                {"n": "water_leak_detected", "u": "/", "vb": reading.leak_detected}
            ]
        elif isinstance(reading, WaterPHReading):
            senml_pack = [
                {"n": "water_ph", "bu": "pH", "u": "pH", "bt": base_time, "v": reading.ph}
            ]
        elif isinstance(reading, WaterTurbidityReading):
            senml_pack = [
                {"n": "water_turbidity", "bu": "NTU", "u": "NTU", "bt": base_time, "v": reading.turbidity}
            ]
        elif isinstance(reading, WaterTDSReading):
            senml_pack = [
                {"n": "water_tds", "bu": "ppm", "u": "ppm", "bt": base_time, "v": reading.tds},
                {"n": "water_conductivity", "u": "uS/cm", "v": reading.conductivity}
            ]
        elif isinstance(reading, ChlorineReading):
            senml_pack = [
                {"n": "chlorine", "bu": "mg/L", "u": "mg/L", "bt": base_time, "v": reading.chlorine}
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
    """MQTT protocol handler with TLS/mTLS support and subscription capability"""
    
    def __init__(self, config: Dict[str, Any], message_callback=None):
        super().__init__(config)
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt is required for MQTT support")
        
        logger.info(f"Initializing MQTT handler with config: broker={config.get('broker')}, port={config.get('port')}, topic={config.get('topic')}")
        
        self.client = mqtt.Client(client_id=config.get('client_id', ''))
        self.message_callback = message_callback
        
        # Set up MQTT callbacks
        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        # Set username and password if provided
        username = config.get('username')
        password = config.get('password')
        if username:
            logger.debug(f"Setting MQTT credentials: username={username}, password={'*' * len(password) if password else 'None'}")
            self.client.username_pw_set(username, password)
        else:
            logger.warning("No MQTT credentials provided")
        
        # Configure TLS if enabled
        tls_mode = config.get('tls_mode', 'none')
        if tls_mode in ['tls', 'mtls']:
            ca_cert = config.get('ca_cert')
            client_cert = config.get('client_cert') if tls_mode == 'mtls' else None
            client_key = config.get('client_key') if tls_mode == 'mtls' else None
            
            logger.info(f"Configuring TLS mode: {tls_mode}, ca_cert={ca_cert}, client_cert={client_cert}")
            
            # Set up TLS
            import os
            if ca_cert and not os.path.exists(ca_cert):
                logger.warning(f"CA certificate not found: {ca_cert}")
            
            self.client.tls_set(
                ca_certs=ca_cert if (ca_cert and os.path.exists(ca_cert)) else None,
                certfile=client_cert,
                keyfile=client_key,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None
            )
            
            # Disable insecure mode - require proper certificate verification
            self.client.tls_insecure_set(False)
            logger.debug("TLS configured successfully")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info("="*60)
            logger.info("✓ MQTT CONNECTION ESTABLISHED")
            logger.info(f"  Broker: {self.config.get('broker')}:{self.config.get('port')}")
            logger.info(f"  Client ID: {self.config.get('client_id')}")
            logger.info(f"  Publish Topic: {self.config.get('topic')}")
            logger.info("="*60)
            
            # Subscribe to control topics if configured
            subscribe_topics = self.config.get('subscribe_topics', [])
            if subscribe_topics:
                logger.info("Subscribing to control topics:")
            for topic in subscribe_topics:
                logger.info(f"  → {topic}")
                result = client.subscribe(topic)
                if result[0] == mqtt.MQTT_ERR_SUCCESS:
                    logger.debug(f"    ✓ Subscribed successfully")
                else:
                    logger.warning(f"    ✗ Subscription failed")
        else:
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            logger.error("="*60)
            logger.error("✗ MQTT CONNECTION FAILED")
            logger.error(f"  Error Code: {rc}")
            logger.error(f"  Reason: {error_messages.get(rc, f'Unknown error ({rc})')}")
            logger.error(f"  Broker: {self.config.get('broker')}:{self.config.get('port')}")
            logger.error("="*60)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        if rc == 0:
            logger.info("Disconnected from MQTT broker")
        else:
            logger.warning(f"Unexpected disconnection from MQTT broker (rc={rc})")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for when a message is published"""
        logger.debug(f"✓ Message published successfully (mid={mid})")
    
    def _on_message(self, client, userdata, msg):
        """Callback for when a message is received"""
        logger.debug(f"Received message on topic {msg.topic}: {msg.payload[:100]}...")
        if self.message_callback:
            try:
                payload = msg.payload.decode('utf-8')
                self.message_callback(msg.topic, payload)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                print(f"Error processing message: {e}")
    
    def connect(self):
        try:
            broker = self.config.get('broker', 'localhost')
            port = self.config.get('port', 1883)
            topic = self.config.get('topic', 'iot/data')
            
            logger.info("="*60)
            logger.info("MQTT Connection Details:")
            logger.info(f"  Broker: {broker}")
            logger.info(f"  Port: {port}")
            logger.info(f"  Topic: {topic}")
            logger.info(f"  Client ID: {self.config.get('client_id', 'N/A')}")
            logger.info(f"  TLS Mode: {self.config.get('tls_mode', 'none')}")
            logger.info("="*60)
            
            logger.info(f"⟳ Connecting to MQTT broker at {broker}:{port}...")
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            self.connected = True
            logger.info("✓ MQTT loop started, waiting for connection callback...")
        except Exception as e:
            logger.error(f"✗ Failed to connect to MQTT broker: {e}")
            raise ConnectionError(f"Failed to connect to MQTT broker: {e}")
    
    def disconnect(self):
        if self.connected:
            logger.info("Disconnecting from MQTT broker...")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT disconnected")
    
    def send(self, data: str):
        if not self.connected:
            logger.error("Cannot send: Not connected to MQTT broker")
            raise ConnectionError("Not connected to MQTT broker")
        
        topic = self.config.get('topic', 'iot/data')
        logger.info("─"*60)
        logger.info(f"📤 Publishing MQTT Message")
        logger.info(f"  Topic: {topic}")
        logger.info(f"  Size: {len(data)} bytes")
        logger.info(f"  QoS: 0")
        logger.info(f"  Full Payload:")
        logger.info(f"{data}")
        
        result = self.client.publish(topic, data, qos=0)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"  ✓ Publish queued (mid={result.mid})")
        else:
            logger.error(f"  ✗ Publish failed (error={result.rc})")
        logger.info("─"*60)
    
    def subscribe(self, topic: str):
        """Subscribe to a topic"""
        if self.connected:
            self.client.subscribe(topic, qos=1)


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
        url = self.config.get('url', 'N/A')
        logger.info("="*60)
        logger.info("HTTP/HTTPS Configuration:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Protocol: {'HTTPS' if url.startswith('https://') else 'HTTP'}")
        logger.info(f"  Method: {self.config.get('method', 'POST')}")
        logger.info(f"  Auth: {'Enabled' if self.config.get('auth_header') else 'None'}")
        logger.info(f"  TLS: {'Enabled' if self.config.get('tls_mode') != 'none' else 'None'}")
        logger.info("✓ HTTP/HTTPS handler ready (connectionless)")
        logger.info("="*60)
        self.connected = True
    
    def disconnect(self):
        self.session.close()
        self.connected = False
    
    def send(self, data: str):
        url = self.config.get('url', 'http://localhost:8080/data')
        method = self.config.get('method', 'POST').upper()
        
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if provided
        auth_header = self.config.get('auth_header')
        if auth_header:
            headers['Authorization'] = auth_header
            logger.debug(f"Using Authorization header: {auth_header[:20]}...")
        
        logger.info(f"Sending HTTP {method} to {url}: {len(data)} bytes")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Payload preview: {data[:200]}...")
        
        try:
            if method == 'POST':
                response = self.session.post(url, data=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = self.session.put(url, data=data, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            logger.info(f"✓ HTTP {method} successful: {response.status_code}")
            logger.debug(f"Response: {response.text[:200]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ HTTP request failed: {e}")
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
        
        logger.info("="*60)
        logger.info("WebSocket Connection Details:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Protocol: {'WSS (Secure)' if url.startswith('wss://') else 'WS (Unsecure)'}")
        logger.info(f"  SSL: {'Enabled' if self.sslopt else 'Disabled'}")
        logger.info("="*60)
        logger.info(f"  SSL: {'Enabled' if self.sslopt else 'Disabled'}")
        logger.info("="*60)
        
        logger.info(f"⟳ Connecting to WebSocket at {url}...")
        
        try:
            if self.sslopt:
                self.ws = websocket.create_connection(url, sslopt=self.sslopt)
            else:
                self.ws = websocket.create_connection(url)
            self.connected = True
            logger.info("="*60)
            logger.info("✓ WEBSOCKET CONNECTION ESTABLISHED")
            logger.info(f"  URL: {url}")
            logger.info("="*60)
        except Exception as e:
            logger.error("="*60)
            logger.error("✗ WEBSOCKET CONNECTION FAILED")
            logger.error(f"  URL: {url}")
            logger.error(f"  Error: {e}")
            logger.error("="*60)
            raise ConnectionError(f"Failed to connect to WebSocket: {e}")
    
    def disconnect(self):
        if self.ws:
            self.ws.close()
            self.connected = False
    
    def send(self, data: str):
        if not self.connected or not self.ws:
            logger.error("Cannot send: Not connected to WebSocket")
            raise ConnectionError("Not connected to WebSocket")
        
        logger.info(f"Sending WebSocket message: {len(data)} bytes")
        logger.debug(f"Payload preview: {data[:200]}...")
        
        try:
            self.ws.send(data)
            logger.debug("✓ WebSocket message sent successfully")
        except Exception as e:
            logger.error(f"✗ Failed to send WebSocket data: {e}")
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
        url = self.config.get('url', 'coap://localhost/data')
        logger.info("="*60)
        logger.info("CoAP Configuration:")
        logger.info(f"  URL: {url}")
        logger.info(f"  Protocol: {'COAPS (Secure)' if url.startswith('coaps://') else 'COAP (Unsecure)'}")
        logger.info(f"  Auth: {'Enabled' if self.config.get('auth') else 'None'}")
        logger.info("✓ CoAP handler ready (connectionless)")
        logger.info("="*60)
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
    """Main IoT device simulator with actuator support"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.generators: Dict[str, DataGenerator] = {}
        self.actuators: Dict[str, Actuator] = {}
        self.protocol_handler: Optional[ProtocolHandler] = None
        self.format_encoder = JSONEncoder
        self.unit_system = "metric"  # Default to metric
        self.running = False
        self.thread = None
        self.interval = 5.0  # seconds
        self.message_queue = queue.Queue()
        self.received_messages = queue.Queue()
    
    def add_generator(self, name: str, generator: DataGenerator):
        """Add a data generator"""
        self.generators[name] = generator
    
    def add_actuator(self, name: str, actuator: Actuator):
        """Add an actuator"""
        self.actuators[name] = actuator
    
    def get_actuator_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current state of all actuators"""
        return {name: actuator.get_state() for name, actuator in self.actuators.items()}
    
    def _handle_mqtt_message(self, topic: str, payload: str):
        """Handle incoming MQTT messages for actuator control"""
        try:
            # Log received message
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.received_messages.put(f"[{timestamp}] Topic: {topic}\nPayload: {payload}\n")
            
            # Try to parse as JSON
            try:
                command = json.loads(payload)
            except json.JSONDecodeError:
                # If not JSON, try simple key=value format
                if "=" in payload:
                    key, value = payload.split("=", 1)
                    command = {key.strip(): value.strip()}
                else:
                    return
            
            # Update actuators based on topic
            for name, actuator in self.actuators.items():
                # Matches both legacy (iot/actuator/<name>, iot/control/<name>) and
                # Magistrala (m/<dom>/c/<chan>/actuators/<name>, .../control/<name>) shapes
                if (f"actuators/{name}" in topic or f"actuator/{name}" in topic
                        or f"control/{name}" in topic):
                    actuator.update_state(command)
                    self.message_queue.put(f"[{timestamp}] Updated {name}: {actuator.get_state()}")
        except Exception as e:
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.message_queue.put(f"[{timestamp}] Error handling message: {e}")
    
    def set_protocol(self, protocol: str, config: Dict[str, Any]):
        """Set the communication protocol"""
        if self.protocol_handler:
            self.protocol_handler.disconnect()
        
        if protocol.lower() == 'mqtt':
            # Add subscription topics for actuators if any exist
            if self.actuators:
                subscribe_topics = config.get('subscribe_topics', [])
                if not subscribe_topics:
                    # Derive Magistrala channel root from publish topic
                    # (m/<dom>/c/<chan>/...) so actuator subs live on the same channel.
                    pub_topic = config.get('topic', '')
                    parts = pub_topic.split('/')
                    if len(parts) >= 4 and parts[0] == 'm' and parts[2] == 'c':
                        channel_root = '/'.join(parts[:4])
                        subscribe_topics = [
                            f"{channel_root}/actuators/#",
                            f"{channel_root}/control/#",
                        ]
                    else:
                        # Legacy fallback when topic is not in Magistrala shape
                        subscribe_topics = [
                            f"iot/actuator/{self.device_id}/#",
                            f"iot/control/{self.device_id}/#",
                        ]
                config['subscribe_topics'] = subscribe_topics
            
            self.protocol_handler = MQTTHandler(config, message_callback=self._handle_mqtt_message)
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
    
    def set_unit_system(self, unit_system: str):
        """Set the unit system (metric or imperial)"""
        if unit_system.lower() not in ['metric', 'imperial']:
            raise ValueError(f"Unsupported unit system: {unit_system}")
        self.unit_system = unit_system.lower()
    
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
        logger.info(f"Starting simulation loop with interval={self.interval}s")
        
        while self.running:
            try:
                logger.debug(f"Generating data from {len(self.generators)} generators...")
                
                # Generate data from all generators
                senml_records = []
                
                for name, generator in self.generators.items():
                    reading = generator.generate()
                    logger.debug(f"Generated reading from {name}: {type(reading).__name__}")
                    
                    # Encode the data
                    if self.format_encoder == SenMLEncoder:
                        encoded = SenMLEncoder.encode(reading, base_name=name, unit_system=self.unit_system)
                        # Add all records to the senml_records list
                        senml_records.extend(encoded)
                    else:
                        # For JSON format, keep the old structure
                        if not hasattr(self, '_json_data'):
                            self._json_data = {}
                        self._json_data[name] = JSONEncoder.encode(reading)
                
                # Convert to JSON string
                if self.format_encoder == SenMLEncoder:
                    # Send SenML as a direct array
                    payload = json.dumps(senml_records, ensure_ascii=False)
                else:
                    # Send JSON as object with sensor names
                    payload = json.dumps(self._json_data, indent=2, ensure_ascii=False)
                
                logger.debug(f"Created payload: {len(payload)} bytes")
                
                # Send via protocol
                logger.info(f"→ Sending data via {type(self.protocol_handler).__name__}...")
                self.protocol_handler.send(payload)
                
                # Log to queue with actual payload for dashboard charting
                timestamp = datetime.now().strftime('%H:%M:%S')
                self.message_queue.put(f"[{timestamp}] Sent: {payload}")
                logger.info(f"✓ Data sent successfully")
                
            except Exception as e:
                error_msg = f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}"
                self.message_queue.put(error_msg)
                logger.error(f"✗ Error in simulation loop: {e}", exc_info=True)
            
            time.sleep(self.interval)


# ==================== Main ====================

def main():
    root = ttk_bootstrap.Window(themename="darkly")
    app = SimulatorGUI(root, IoTDeviceSimulator)
    root.mainloop()


if __name__ == "__main__":
    main()
