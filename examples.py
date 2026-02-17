#!/usr/bin/env python3
"""
Example: Using IoT Device Simulator Programmatically
Demonstrates how to use the simulator without the GUI
"""

import sys
import time
sys.path.insert(0, '.')

from main import IoTDeviceSimulator
from sensors import (
    LocationGenerator,
    TemperatureGenerator,
    PressureGenerator,
    HumidityGenerator,
    AccelerometerGenerator,
    CO2Generator,
    FlowGenerator,
    SoilMoistureGenerator,
    SoilPHGenerator,
    LightIntensityGenerator,
    RainGenerator,
    WindSpeedGenerator
)


def example_http_simulator():
    """Example: Send data via HTTP"""
    print("=== HTTP Simulator Example ===\n")
    
    # Create simulator
    simulator = IoTDeviceSimulator(device_id="demo_device_http")
    
    # Add sensors
    simulator.add_generator('temperature', TemperatureGenerator("demo_device_http", base_temp=25.0))
    simulator.add_generator('humidity', HumidityGenerator("demo_device_http", base_humidity=65.0))
    
    # Configure HTTP protocol
    http_config = {
        'url': 'http://localhost:8080/data',
        'method': 'POST'
    }
    simulator.set_protocol('HTTP', http_config)
    
    # Set format (JSON or SenML)
    simulator.set_format('JSON')
    
    # Set interval
    simulator.interval = 3.0  # Send every 3 seconds
    
    print("Starting HTTP simulator...")
    print("Make sure tests/test_http_server.py is running on port 8080")
    print("Press Ctrl+C to stop\n")
    
    try:
        simulator.start()
        
        # Run for 30 seconds or until interrupted
        for i in range(10):
            time.sleep(3)
            print(f"Running... {(i+1)*3}s elapsed")
        
        simulator.stop()
        print("\nSimulator stopped.")
        
    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped.")


def example_mqtt_simulator():
    """Example: Send data via MQTT"""
    print("=== MQTT Simulator Example ===\n")
    
    # Create simulator
    simulator = IoTDeviceSimulator(device_id="demo_device_mqtt")
    
    # Add sensors
    simulator.add_generator('location', LocationGenerator("demo_device_mqtt"))
    simulator.add_generator('temperature', TemperatureGenerator("demo_device_mqtt"))
    simulator.add_generator('pressure', PressureGenerator("demo_device_mqtt"))
    
    # Configure MQTT protocol
    mqtt_config = {
        'broker': 'localhost',
        'port': 1883,
        'topic': 'iot/demo/data',
        'client_id': 'demo_device_mqtt'
    }
    simulator.set_protocol('MQTT', mqtt_config)
    
    # Set format to SenML
    simulator.set_format('SenML')
    
    # Set interval
    simulator.interval = 2.0  # Send every 2 seconds
    
    print("Starting MQTT simulator...")
    print("Make sure MQTT broker is running on localhost:1883")
    print("Run test_mqtt_subscriber.py to see the messages")
    print("Press Ctrl+C to stop\n")
    
    try:
        simulator.start()
        
        # Run until interrupted
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped.")


def example_all_sensors():
    """Example: Simulate all sensor types"""
    print("=== All Sensors Example ===\n")
    
    # Create simulator
    simulator = IoTDeviceSimulator(device_id="demo_device_all")
    
    # Add all sensor types
    simulator.add_generator('location', LocationGenerator("demo_device_all", base_lat=40.7128, base_lon=-74.0060))
    simulator.add_generator('temperature', TemperatureGenerator("demo_device_all", base_temp=20.0))
    simulator.add_generator('pressure', PressureGenerator("demo_device_all"))
    simulator.add_generator('humidity', HumidityGenerator("demo_device_all"))
    simulator.add_generator('accelerometer', AccelerometerGenerator("demo_device_all"))
    
    # Configure HTTP protocol
    http_config = {
        'url': 'http://localhost:8080/data',
        'method': 'POST'
    }
    simulator.set_protocol('HTTP', http_config)
    
    # Use SenML format
    simulator.set_format('SenML')
    
    # Set interval
    simulator.interval = 5.0  # Send every 5 seconds
    
    print("Starting simulator with all sensors...")
    print("Make sure tests/test_http_server.py is running on port 8080")
    print("Press Ctrl+C to stop\n")
    
    try:
        simulator.start()
        
        # Run until interrupted
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped.")


def example_agriculture_sensors():
    """Example: Agricultural/Environmental monitoring sensors"""
    print("=== Agriculture Sensors Example ===\n")
    
    # Create simulator
    simulator = IoTDeviceSimulator(device_id="agri_device_001")
    
    # Add agriculture-specific sensors
    simulator.add_generator('soil_moisture', SoilMoistureGenerator("agri_device_001", base_moisture=50.0))
    simulator.add_generator('soil_ph', SoilPHGenerator("agri_device_001", base_ph=6.8))
    simulator.add_generator('temperature', TemperatureGenerator("agri_device_001", base_temp=24.0))
    simulator.add_generator('humidity', HumidityGenerator("agri_device_001", base_humidity=70.0))
    simulator.add_generator('light', LightIntensityGenerator("agri_device_001", base_lux=15000.0))
    simulator.add_generator('rain', RainGenerator("agri_device_001"))
    simulator.add_generator('co2', CO2Generator("agri_device_001", base_ppm=450.0))
    
    # Configure HTTP protocol
    http_config = {
        'url': 'http://localhost:8080/data',
        'method': 'POST'
    }
    simulator.set_protocol('HTTP', http_config)
    
    # Use SenML format (great for agriculture IoT)
    simulator.set_format('SenML')
    
    # Set interval
    simulator.interval = 10.0  # Send every 10 seconds (typical for agriculture)
    
    print("Starting agriculture monitoring simulator...")
    print("Sensors: Soil Moisture, Soil pH, Temperature, Humidity, Light, Rain, CO2")
    print("Make sure tests/test_http_server.py is running on port 8080")
    print("Press Ctrl+C to stop\n")
    
    try:
        simulator.start()
        
        # Run until interrupted
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped.")


def example_water_monitoring():
    """Example: Water system monitoring"""
    print("=== Water Monitoring Example ===\n")
    
    # Create simulator
    simulator = IoTDeviceSimulator(device_id="water_monitor_001")
    
    # Add water monitoring sensors
    simulator.add_generator('flow', FlowGenerator("water_monitor_001", base_flow=8.0))
    simulator.add_generator('pressure', PressureGenerator("water_monitor_001", base_pressure=1020.0))
    simulator.add_generator('temperature', TemperatureGenerator("water_monitor_001", base_temp=18.0))
    
    # Configure MQTT protocol
    mqtt_config = {
        'broker': 'localhost',
        'port': 1883,
        'topic': 'water/monitoring/data',
        'client_id': 'water_monitor_001'
    }
    simulator.set_protocol('MQTT', mqtt_config)
    
    # Use JSON format
    simulator.set_format('JSON')
    
    # Set interval
    simulator.interval = 3.0  # Send every 3 seconds
    
    print("Starting water monitoring simulator...")
    print("Sensors: Flow Rate, Pressure, Temperature")
    print("Make sure MQTT broker is running on localhost:1883")
    print("Press Ctrl+C to stop\n")
    
    try:
        simulator.start()
        
        # Run until interrupted
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n\nStopping simulator...")
        simulator.stop()
        print("Simulator stopped.")


def main():
    """Main function - select example to run"""
    print("""
╔════════════════════════════════════════════════════════════╗
║      IoT Device Simulator - Programmatic Examples         ║
╚════════════════════════════════════════════════════════════╝

Select an example to run:

1. HTTP Simulator (Temperature + Humidity, JSON format)
2. MQTT Simulator (Location + Temperature + Pressure, SenML format)
3. All Sensors (HTTP, SenML format)
4. Agriculture Monitoring (Soil, Light, Rain, CO2, SenML format)
5. Water System Monitoring (Flow, Pressure, Temperature, JSON format)

""")
    
    choice = input("Enter your choice (1-5): ").strip()
    
    print()
    
    if choice == '1':
        example_http_simulator()
    elif choice == '2':
        example_mqtt_simulator()
    elif choice == '3':
        example_all_sensors()
    elif choice == '4':
        example_agriculture_sensors()
    elif choice == '5':
        example_water_monitoring()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    main()
