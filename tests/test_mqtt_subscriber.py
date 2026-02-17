#!/usr/bin/env python3
"""
Simple MQTT subscriber for testing IoT Device Simulator
Subscribes to MQTT topics and displays received messages
"""

import sys
import json
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed")
    print("Install it with: pip install paho-mqtt")
    sys.exit(1)


class MQTTSubscriber:
    """MQTT subscriber for IoT data"""
    
    def __init__(self, broker="localhost", port=1883, topic="iot/#"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker: {self.broker}:{self.port}")
            print(f"✓ Subscribed to topic: {self.topic}\n")
            client.subscribe(self.topic)
        else:
            print(f"✗ Connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n{'='*60}")
        print(f"[{timestamp}] Topic: {msg.topic}")
        print(f"{'='*60}")
        
        try:
            # Try to parse as JSON for pretty printing
            data = json.loads(msg.payload.decode('utf-8'))
            print(json.dumps(data, indent=2))
        except:
            # If not JSON, print raw payload
            print(msg.payload.decode('utf-8'))
        
        print(f"{'='*60}\n")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        if rc != 0:
            print(f"✗ Unexpected disconnection (code: {rc})")
    
    def run(self):
        """Start the subscriber"""
        print(f"""
╔════════════════════════════════════════════════════════════╗
║         IoT Device Simulator - MQTT Test Subscriber       ║
╚════════════════════════════════════════════════════════════╝

Broker: {self.broker}:{self.port}
Topic: {self.topic}

Connecting to MQTT broker...
""")
        
        self.client = mqtt.Client(client_id="iot_simulator_test_subscriber")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        try:
            self.client.connect(self.broker, self.port, 60)
            print("Waiting for messages... (Press Ctrl+C to stop)\n")
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\nDisconnecting...")
            self.client.disconnect()
            print("Subscriber stopped.")
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Parse command line arguments
    broker = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 1883
    topic = sys.argv[3] if len(sys.argv) > 3 else "iot/#"
    
    subscriber = MQTTSubscriber(broker, port, topic)
    subscriber.run()
