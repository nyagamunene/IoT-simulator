#!/usr/bin/env python3
"""
Test script to send MQTT commands to control actuators
Usage: python tests/test_actuator_control.py [device_id]
"""

import paho.mqtt.client as mqtt
import json
import time
import sys

# Configuration
BROKER = "localhost"
PORT = 1883
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "device_001"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {BROKER}:{PORT}")
        print(f"✓ Sending commands to device: {DEVICE_ID}\n")
        
        # Demo commands
        print("=" * 60)
        print("ACTUATOR CONTROL DEMO")
        print("=" * 60)
        
        # Bulb commands
        print("\n1. Turning Smart Bulb ON...")
        client.publish(f"iot/actuator/{DEVICE_ID}/bulb", json.dumps({"power": "on"}))
        time.sleep(1)
        
        print("2. Setting bulb brightness to 75%...")
        client.publish(f"iot/actuator/{DEVICE_ID}/bulb", json.dumps({"brightness": 75}))
        time.sleep(1)
        
        print("3. Changing bulb color to blue...")
        client.publish(f"iot/actuator/{DEVICE_ID}/bulb", json.dumps({"color": "#0000FF"}))
        time.sleep(1)
        
        print("4. Turning bulb OFF...")
        client.publish(f"iot/actuator/{DEVICE_ID}/bulb", json.dumps({"power": "off"}))
        time.sleep(1)
        
        # Relay commands
        print("\n5. Turning Relay ON...")
        client.publish(f"iot/control/{DEVICE_ID}/relay", json.dumps({"power": "on"}))
        time.sleep(1)
        
        print("6. Turning Relay OFF...")
        client.publish(f"iot/control/{DEVICE_ID}/relay", json.dumps({"power": "off"}))
        time.sleep(1)
        
        # Thermostat commands
        print("\n7. Turning Thermostat ON in HEAT mode...")
        client.publish(f"iot/actuator/{DEVICE_ID}/thermostat", json.dumps({
            "power": "on",
            "mode": "heat",
            "target_temperature": 24.5
        }))
        time.sleep(1)
        
        print("8. Changing thermostat to COOL mode at 20°C...")
        client.publish(f"iot/actuator/{DEVICE_ID}/thermostat", json.dumps({
            "mode": "cool",
            "target_temperature": 20.0
        }))
        time.sleep(1)
        
        print("\n" + "=" * 60)
        print("✓ All commands sent successfully!")
        print("=" * 60)
        print("\nCheck the simulator GUI:")
        print("  - 'Received Messages' tab for MQTT messages")
        print("  - 'Actuator Status' tab for current actuator states")
        print("\nPress Ctrl+C to exit...")
        
    else:
        print(f"✗ Failed to connect to broker. Return code: {rc}")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print(f"✗ Unexpected disconnection. Return code: {rc}")


def main():
    print(f"MQTT Actuator Control Test")
    print(f"Broker: {BROKER}:{PORT}")
    print(f"Device ID: {DEVICE_ID}")
    print(f"\nMake sure:")
    print(f"  1. MQTT broker is running (make mqtt-up)")
    print(f"  2. Simulator is running with MQTT protocol")
    print(f"  3. At least one actuator is enabled")
    print("\nConnecting...\n")
    
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        client.disconnect()
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
