"""
IoT Simulator Library

This package contains the core modules for the IoT Device Simulator:
- sensors: Sensor data generators and reading classes
- actuators: Actuator models (Bulb, Relay, Thermostat)
- publisher_gui: GUI for publishing sensor data
- subscriber_gui: GUI for subscribing to MQTT messages
"""

__version__ = "1.0.0"

# Expose commonly used classes for convenient imports
from lib.sensors import (
    SensorReading,
    LocationReading,
    TemperatureReading,
    PressureReading,
    HumidityReading,
    AccelerometerReading,
    CO2Reading,
    FlowReading,
    SoilMoistureReading,
    SoilPHReading,
    LightIntensityReading,
    RainReading,
    WindSpeedReading,
    DataGenerator,
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
    WindSpeedGenerator,
)

from lib.actuators import (
    Actuator,
    BulbActuator,
    RelayActuator,
    ThermostatActuator,
)

__all__ = [
    # Sensor readings
    "SensorReading",
    "LocationReading",
    "TemperatureReading",
    "PressureReading",
    "HumidityReading",
    "AccelerometerReading",
    "CO2Reading",
    "FlowReading",
    "SoilMoistureReading",
    "SoilPHReading",
    "LightIntensityReading",
    "RainReading",
    "WindSpeedReading",
    # Generators
    "DataGenerator",
    "LocationGenerator",
    "TemperatureGenerator",
    "PressureGenerator",
    "HumidityGenerator",
    "AccelerometerGenerator",
    "CO2Generator",
    "FlowGenerator",
    "SoilMoistureGenerator",
    "SoilPHGenerator",
    "LightIntensityGenerator",
    "RainGenerator",
    "WindSpeedGenerator",
    # Actuators
    "Actuator",
    "BulbActuator",
    "RelayActuator",
    "ThermostatActuator",
]
