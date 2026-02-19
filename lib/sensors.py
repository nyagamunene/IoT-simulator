"""
IoT Device Simulator - Sensor Library
Contains sensor reading data models and data generators
"""

import time
import random
import math
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


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
class GyroscopeReading(SensorReading):
    """Gyroscope data (angular velocity)"""
    x: float
    y: float
    z: float
    unit: str = "deg/s"


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


@dataclass
class FuelConsumptionReading(SensorReading):
    """Fuel consumption sensor data"""
    consumption_l_100km: float  # Liters per 100 kilometers (metric)
    consumption_mpg: float  # Miles per gallon (imperial/US)
    fuel_level: float  # percentage (0-100)
    total_consumed: float  # total liters consumed
    metric_unit: str = "L/100km"
    imperial_unit: str = "MPG"


@dataclass
class SpeedReading(SensorReading):
    """Speed sensor data (velocity)"""
    speed: float  # m/s
    heading: float  # degrees (0-360, where 0 is North)
    unit: str = "m/s"


# ==================== Motion State ====================

class MotionState:
    """Shared state for coordinated motion sensors (GPS, Speed, Accelerometer)
    
    Supports three motion modes:
    - stationary: No movement (speed=0, no position changes)
    - low_speed: Low speed movement (0-10 m/s, 0-36 km/h)
    - high_speed: High speed movement (10-30 m/s, 36-108 km/h)
    """
    
    def __init__(self, lat: float = 37.7749, lon: float = -122.4194, altitude: float = 50.0, 
                 mode: str = "low_speed"):
        # Position (GPS)
        self.latitude = lat
        self.longitude = lon
        self.altitude = altitude
        
        # Velocity (Speed)
        self.speed = 0.0  # m/s
        self.heading = random.uniform(0, 360)  # degrees
        
        # Acceleration
        self.acceleration_x = 0.0  # m/s^2 (lateral)
        self.acceleration_y = 0.0  # m/s^2 (longitudinal)
        self.acceleration_z = 0.0  # m/s^2 (vertical)
        
        # Motion mode
        self.mode = mode  # "stationary", "low_speed", or "high_speed"
    
    def update(self, dt: float = 5.0):
        """Update motion state based on physics and current mode
        dt: time interval in seconds (default 5s)
        """
        if self.mode == "stationary":
            # No movement at all
            self.speed = 0.0
            self.acceleration_x = 0.0
            self.acceleration_y = 0.0
            self.acceleration_z = 0.0
            return
        
        # Generate realistic acceleration changes based on mode
        if self.mode == "low_speed":
            # Low speed: 0-10 m/s (0-36 km/h)
            target_speed = random.uniform(2.0, 10.0)
            max_accel = 2.0  # m/s^2
            lateral_accel_range = 1.5
        else:  # high_speed
            # High speed: 10-30 m/s (36-108 km/h)
            target_speed = random.uniform(10.0, 30.0)
            max_accel = 3.0  # m/s^2
            lateral_accel_range = 2.0
        
        # Longitudinal acceleration (speeding up/slowing down)
        speed_diff = target_speed - self.speed
        self.acceleration_y = max(-max_accel, min(max_accel, speed_diff * 0.3))
        
        # Lateral acceleration (turning)
        self.acceleration_x = random.uniform(-lateral_accel_range, lateral_accel_range)
        
        # Vertical acceleration (small, mostly gravity variations)
        self.acceleration_z = random.uniform(-1.0, 1.0)
        
        # Update velocity based on acceleration
        self.speed += self.acceleration_y * dt
        
        # Clamp speed based on mode
        if self.mode == "low_speed":
            self.speed = max(0, min(10, self.speed))
        else:  # high_speed
            self.speed = max(0, min(30, self.speed))
        
        # Update heading based on lateral acceleration (simplified)
        heading_change = (self.acceleration_x / max(self.speed, 1.0)) * dt * 10  # degrees
        self.heading += heading_change
        self.heading = self.heading % 360
        
        # Update GPS position based on velocity
        # Convert heading to radians (0° = North, 90° = East)
        heading_rad = math.radians(self.heading)
        
        # Calculate displacement
        distance = self.speed * dt  # meters
        
        # Convert to lat/lon changes
        # 1 degree latitude ≈ 111,320 meters
        # 1 degree longitude ≈ 111,320 * cos(latitude) meters
        lat_change = (distance * math.cos(heading_rad)) / 111320
        lon_change = (distance * math.sin(heading_rad)) / (111320 * math.cos(math.radians(self.latitude)))
        
        self.latitude += lat_change
        self.longitude += lon_change
        
        # Small altitude changes
        self.altitude += random.uniform(-0.5, 0.5)
        self.altitude = max(0, min(500, self.altitude))


# ==================== Data Generators ====================

class DataGenerator:
    """Base class for data generators"""
    
    def __init__(self, device_id: str):
        self.device_id = device_id
    
    def generate(self) -> SensorReading:
        raise NotImplementedError


class LocationGenerator(DataGenerator):
    """Generates realistic GPS location data using shared motion state"""
    
    def __init__(self, device_id: str, base_lat: float = 37.7749, base_lon: float = -122.4194, 
                 motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.motion_state = motion_state if motion_state else MotionState(base_lat, base_lon)
    
    def generate(self) -> LocationReading:
        # Update motion state (position is updated by physics)
        self.motion_state.update(dt=5.0)
        
        return LocationReading(
            timestamp=time.time(),
            device_id=self.device_id,
            latitude=round(self.motion_state.latitude, 6),
            longitude=round(self.motion_state.longitude, 6),
            altitude=round(self.motion_state.altitude, 2),
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
    """Generates realistic accelerometer data using shared motion state"""
    
    def __init__(self, device_id: str, motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.motion_state = motion_state if motion_state else MotionState()
    
    def generate(self) -> AccelerometerReading:
        # Get acceleration from motion state (with small noise)
        return AccelerometerReading(
            timestamp=time.time(),
            device_id=self.device_id,
            x=round(self.motion_state.acceleration_x + random.uniform(-0.1, 0.1), 3),
            y=round(self.motion_state.acceleration_y + random.uniform(-0.1, 0.1), 3),
            z=round(self.motion_state.acceleration_z + 9.81 + random.uniform(-0.1, 0.1), 3)  # Include gravity
        )


class GyroscopeGenerator(DataGenerator):
    """Generates realistic gyroscope data (angular velocity)"""
    
    def __init__(self, device_id: str):
        super().__init__(device_id)
        self.x_rate = 0.0
        self.y_rate = 0.0
        self.z_rate = 0.0
    
    def generate(self) -> GyroscopeReading:
        # Simulate angular velocity changes (typical range -250 to 250 deg/s)
        self.x_rate += random.uniform(-5, 5)
        self.y_rate += random.uniform(-5, 5)
        self.z_rate += random.uniform(-5, 5)
        
        # Clamp to realistic range
        self.x_rate = max(-250, min(250, self.x_rate))
        self.y_rate = max(-250, min(250, self.y_rate))
        self.z_rate = max(-250, min(250, self.z_rate))
        
        return GyroscopeReading(
            timestamp=time.time(),
            device_id=self.device_id,
            x=round(self.x_rate, 3),
            y=round(self.y_rate, 3),
            z=round(self.z_rate, 3)
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


class SpeedGenerator(DataGenerator):
    """Generates realistic speed data using shared motion state"""
    
    def __init__(self, device_id: str, motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.motion_state = motion_state if motion_state else MotionState()
    
    def generate(self) -> SpeedReading:
        return SpeedReading(
            timestamp=time.time(),
            device_id=self.device_id,
            speed=round(self.motion_state.speed, 2),
            heading=round(self.motion_state.heading, 1)
        )


class FuelConsumptionGenerator(DataGenerator):
    """Generates realistic fuel consumption data based on vehicle motion"""
    
    def __init__(self, device_id: str, tank_capacity: float = 50.0, motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.fuel_level = random.uniform(30, 100)  # Start with 30-100% fuel
        self.total_consumed = 0.0
        self.tank_capacity = tank_capacity
        self.motion_state = motion_state if motion_state else MotionState()
        self.base_consumption = 6.5  # Base L/100km at optimal conditions
    
    def generate(self) -> FuelConsumptionReading:
        # Get current speed from motion state (m/s to km/h)
        speed_kmh = self.motion_state.speed * 3.6
        
        # Calculate fuel consumption based on speed and acceleration
        # Realistic consumption model:
        # - Idle/very low speed: 0.8-1.5 L/h (city traffic)
        # - Optimal speed (60-80 km/h): 6-8 L/100km
        # - High speed (>100 km/h): 10-15 L/100km
        # - Acceleration increases consumption
        # - Deceleration/coasting reduces consumption
        
        if speed_kmh < 1.0:
            # Idle consumption (convert to L/100km equivalent for consistency)
            consumption_l_100km = 100.0  # Very high per 100km but actual consumption is low due to no distance
        elif speed_kmh < 30.0:
            # City driving - stop and go
            consumption_l_100km = 8.0 + random.uniform(-0.5, 1.0)
        elif speed_kmh < 60.0:
            # Moderate speed - decent efficiency
            consumption_l_100km = 6.5 + random.uniform(-0.3, 0.8)
        elif speed_kmh < 90.0:
            # Optimal speed - best efficiency
            consumption_l_100km = self.base_consumption + random.uniform(-0.5, 0.5)
        else:
            # High speed - increased drag and consumption
            drag_factor = (speed_kmh - 90.0) / 50.0  # Increases with speed
            consumption_l_100km = 8.0 + drag_factor * 4.0 + random.uniform(-0.3, 0.8)
        
        # Acceleration impact (more throttle = more fuel)
        accel_impact = abs(self.motion_state.acceleration_y) * 1.5
        consumption_l_100km += accel_impact
        
        # Clamp to realistic range
        consumption_l_100km = max(4.0, min(20.0, consumption_l_100km))
        
        # Convert L/100km to MPG (US gallons)
        # Formula: MPG = 235.215 / (L/100km)
        consumption_mpg = 235.215 / consumption_l_100km
        
        # Calculate actual fuel consumed since last reading (5 second intervals)
        interval_hours = 5.0 / 3600.0  # 5 seconds in hours
        distance_km = speed_kmh * interval_hours  # actual distance traveled
        
        # Fuel consumed this interval
        if distance_km > 0:
            consumed_this_interval = (consumption_l_100km / 100.0) * distance_km
        else:
            # Idle consumption: ~0.8 L/h
            consumed_this_interval = 0.8 * interval_hours
        
        # Update total and fuel level
        self.total_consumed += consumed_this_interval
        fuel_level_decrease = (consumed_this_interval / self.tank_capacity) * 100
        self.fuel_level = max(0, self.fuel_level - fuel_level_decrease)
        
        return FuelConsumptionReading(
            timestamp=time.time(),
            device_id=self.device_id,
            consumption_l_100km=round(consumption_l_100km, 2),
            consumption_mpg=round(consumption_mpg, 1),
            fuel_level=round(self.fuel_level, 1),
            total_consumed=round(self.total_consumed, 3)
        )
