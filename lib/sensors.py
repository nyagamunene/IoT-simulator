"""
IoT Device Simulator - Sensor Library
Contains sensor reading data models and data generators
"""

import time
import random
from dataclasses import dataclass, asdict
from typing import Dict, Any


# ==================== Data Models ====================

@dataclass
class SensorReading:
    """Base class for sensor readings"""
    timestamp: float
    device_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LocationReading(SensorReading):
    """GPS location data"""
    latitude: float
    longitude: float
    altitude: float
    accuracy: float


@dataclass
class TemperatureReading(SensorReading):
    """Temperature sensor data"""
    temperature: float
    unit: str = "celsius"


@dataclass
class PressureReading(SensorReading):
    """Pressure sensor data"""
    pressure: float
    unit: str = "hPa"


@dataclass
class HumidityReading(SensorReading):
    """Humidity sensor data"""
    humidity: float
    unit: str = "percent"


@dataclass
class AccelerometerReading(SensorReading):
    """Accelerometer data"""
    x: float
    y: float
    z: float
    unit: str = "m/s^2"


@dataclass
class CO2Reading(SensorReading):
    """CO2 sensor data (PPM)"""
    co2_ppm: float
    unit: str = "ppm"


@dataclass
class FlowReading(SensorReading):
    """Flow sensor data (liquid/water flow)"""
    flow_rate: float
    total_volume: float
    unit: str = "L/min"


@dataclass
class SoilMoistureReading(SensorReading):
    """Soil moisture sensor data"""
    moisture: float
    unit: str = "percent"


@dataclass
class SoilPHReading(SensorReading):
    """Soil pH sensor data"""
    ph: float
    unit: str = "pH"


@dataclass
class LightIntensityReading(SensorReading):
    """Light intensity sensor data"""
    intensity: float
    unit: str = "lux"


@dataclass
class RainReading(SensorReading):
    """Rain/Precipitation sensor data"""
    rainfall: float
    unit: str = "mm/h"


@dataclass
class WindSpeedReading(SensorReading):
    """Wind speed sensor data"""
    speed: float
    direction: float
    unit: str = "m/s"


# ==================== Data Generators ====================

class DataGenerator:
    """Base class for data generators"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
    
    def generate(self) -> SensorReading:
        raise NotImplementedError


class LocationGenerator(DataGenerator):
    """Generates realistic GPS location data"""
    
    def __init__(self, device_id: str, base_lat: float = 37.7749, base_lon: float = -122.4194):
        super().__init__(device_id)
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.lat = base_lat
        self.lon = base_lon
        self.alt = random.uniform(0, 100)
    
    def generate(self) -> LocationReading:
        # Simulate movement
        self.lat += random.uniform(-0.0001, 0.0001)
        self.lon += random.uniform(-0.0001, 0.0001)
        self.alt += random.uniform(-0.5, 0.5)
        
        return LocationReading(
            timestamp=time.time(),
            device_id=self.device_id,
            latitude=round(self.lat, 6),
            longitude=round(self.lon, 6),
            altitude=round(self.alt, 2),
            accuracy=round(random.uniform(1.0, 5.0), 2)
        )


class TemperatureGenerator(DataGenerator):
    """Generates realistic temperature data"""
    
    def __init__(self, device_id: str, base_temp: float = 22.0):
        super().__init__(device_id)
        self.base_temp = base_temp
        self.current_temp = base_temp
    
    def generate(self) -> TemperatureReading:
        # Simulate temperature fluctuation
        self.current_temp += random.uniform(-0.5, 0.5)
        self.current_temp = max(-20, min(50, self.current_temp))
        
        return TemperatureReading(
            timestamp=time.time(),
            device_id=self.device_id,
            temperature=round(self.current_temp, 2)
        )


class PressureGenerator(DataGenerator):
    """Generates realistic pressure data"""
    
    def __init__(self, device_id: str, base_pressure: float = 1013.25):
        super().__init__(device_id)
        self.base_pressure = base_pressure
        self.current_pressure = base_pressure
    
    def generate(self) -> PressureReading:
        # Simulate pressure fluctuation
        self.current_pressure += random.uniform(-1.0, 1.0)
        self.current_pressure = max(950, min(1050, self.current_pressure))
        
        return PressureReading(
            timestamp=time.time(),
            device_id=self.device_id,
            pressure=round(self.current_pressure, 2)
        )


class HumidityGenerator(DataGenerator):
    """Generates realistic humidity data"""
    
    def __init__(self, device_id: str, base_humidity: float = 60.0):
        super().__init__(device_id)
        self.current_humidity = base_humidity
    
    def generate(self) -> HumidityReading:
        # Simulate humidity fluctuation
        self.current_humidity += random.uniform(-2.0, 2.0)
        self.current_humidity = max(0, min(100, self.current_humidity))
        
        return HumidityReading(
            timestamp=time.time(),
            device_id=self.device_id,
            humidity=round(self.current_humidity, 2)
        )


class AccelerometerGenerator(DataGenerator):
    """Generates realistic accelerometer data"""
    
    def __init__(self, device_id: str):
        super().__init__(device_id)
    
    def generate(self) -> AccelerometerReading:
        return AccelerometerReading(
            timestamp=time.time(),
            device_id=self.device_id,
            x=round(random.uniform(-10, 10), 3),
            y=round(random.uniform(-10, 10), 3),
            z=round(random.uniform(-10, 10), 3)
        )


class CO2Generator(DataGenerator):
    """Generates realistic CO2 PPM data"""
    
    def __init__(self, device_id: str, base_ppm: float = 400.0):
        super().__init__(device_id)
        self.current_ppm = base_ppm
    
    def generate(self) -> CO2Reading:
        # Simulate CO2 fluctuation (typical range 400-1000 ppm indoor)
        self.current_ppm += random.uniform(-10, 15)
        self.current_ppm = max(300, min(2000, self.current_ppm))
        
        return CO2Reading(
            timestamp=time.time(),
            device_id=self.device_id,
            co2_ppm=round(self.current_ppm, 1)
        )


class FlowGenerator(DataGenerator):
    """Generates realistic flow sensor data"""
    
    def __init__(self, device_id: str, base_flow: float = 5.0):
        super().__init__(device_id)
        self.current_flow = base_flow
        self.total_volume = 0.0
        self.last_time = time.time()
    
    def generate(self) -> FlowReading:
        # Simulate flow rate changes
        self.current_flow += random.uniform(-0.5, 0.5)
        self.current_flow = max(0, min(20, self.current_flow))
        
        # Calculate volume
        current_time = time.time()
        elapsed_minutes = (current_time - self.last_time) / 60.0
        self.total_volume += self.current_flow * elapsed_minutes
        self.last_time = current_time
        
        return FlowReading(
            timestamp=time.time(),
            device_id=self.device_id,
            flow_rate=round(self.current_flow, 2),
            total_volume=round(self.total_volume, 2)
        )


class SoilMoistureGenerator(DataGenerator):
    """Generates realistic soil moisture data"""
    
    def __init__(self, device_id: str, base_moisture: float = 45.0):
        super().__init__(device_id)
        self.current_moisture = base_moisture
    
    def generate(self) -> SoilMoistureReading:
        # Simulate moisture changes (typically decreases slowly)
        self.current_moisture += random.uniform(-1.5, 0.5)
        self.current_moisture = max(0, min(100, self.current_moisture))
        
        return SoilMoistureReading(
            timestamp=time.time(),
            device_id=self.device_id,
            moisture=round(self.current_moisture, 1)
        )


class SoilPHGenerator(DataGenerator):
    """Generates realistic soil pH data"""
    
    def __init__(self, device_id: str, base_ph: float = 6.5):
        super().__init__(device_id)
        self.current_ph = base_ph
    
    def generate(self) -> SoilPHReading:
        # Simulate pH fluctuation (pH usually stable, small changes)
        self.current_ph += random.uniform(-0.1, 0.1)
        self.current_ph = max(4.0, min(9.0, self.current_ph))
        
        return SoilPHReading(
            timestamp=time.time(),
            device_id=self.device_id,
            ph=round(self.current_ph, 2)
        )


class LightIntensityGenerator(DataGenerator):
    """Generates realistic light intensity data"""
    
    def __init__(self, device_id: str, base_lux: float = 10000.0):
        super().__init__(device_id)
        self.current_lux = base_lux
    
    def generate(self) -> LightIntensityReading:
        # Simulate light intensity changes (0-100000 lux range)
        self.current_lux += random.uniform(-1000, 1000)
        self.current_lux = max(0, min(100000, self.current_lux))
        
        return LightIntensityReading(
            timestamp=time.time(),
            device_id=self.device_id,
            intensity=round(self.current_lux, 1)
        )


class RainGenerator(DataGenerator):
    """Generates realistic rain/precipitation data"""
    
    def __init__(self, device_id: str, base_rain: float = 0.0):
        super().__init__(device_id)
        self.current_rain = base_rain
    
    def generate(self) -> RainReading:
        # Simulate rainfall (0-50 mm/h, often 0)
        if random.random() < 0.7:  # 70% chance of no rain
            self.current_rain = max(0, self.current_rain - random.uniform(0, 2))
        else:
            self.current_rain += random.uniform(0, 5)
        
        self.current_rain = max(0, min(50, self.current_rain))
        
        return RainReading(
            timestamp=time.time(),
            device_id=self.device_id,
            rainfall=round(self.current_rain, 2)
        )


class WindSpeedGenerator(DataGenerator):
    """Generates realistic wind speed data"""
    
    def __init__(self, device_id: str, base_speed: float = 3.0):
        super().__init__(device_id)
        self.current_speed = base_speed
        self.current_direction = random.uniform(0, 360)
    
    def generate(self) -> WindSpeedReading:
        # Simulate wind speed changes
        self.current_speed += random.uniform(-0.5, 0.5)
        self.current_speed = max(0, min(30, self.current_speed))
        
        # Simulate direction changes
        self.current_direction += random.uniform(-10, 10)
        self.current_direction = self.current_direction % 360
        
        return WindSpeedReading(
            timestamp=time.time(),
            device_id=self.device_id,
            speed=round(self.current_speed, 2),
            direction=round(self.current_direction, 1)
        )
