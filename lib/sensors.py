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


@dataclass
class WaterMeterReading(SensorReading):
    """Water meter sensor data"""
    flow_rate: float       # L/min
    cumulative_volume: float  # m³ (total consumed)
    leak_detected: bool    # simple leak flag
    unit: str = "L/min"


@dataclass
class WaterPHReading(SensorReading):
    """Water pH sensor data"""
    ph: float
    unit: str = "pH"


@dataclass
class WaterTurbidityReading(SensorReading):
    """Water turbidity sensor data (clarity)"""
    turbidity: float   # NTU (Nephelometric Turbidity Units)
    unit: str = "NTU"

@dataclass
class WaterTDSReading(SensorReading):
    """Water Total Dissolved Solids sensor data"""
    tds: float         # ppm (parts per million)
    conductivity: float  # μS/cm
    unit: str = "ppm"

@dataclass
class ChlorineReading(SensorReading):
    """Chlorine level sensor data"""
    chlorine: float    # mg/L (ppm)
    unit: str = "mg/L"

# ==================== Motion State ====================

class MotionState:
    """Shared state for coordinated motion sensors (GPS, Speed, Accelerometer)
    
    Supports four motion modes:
    - stationary: No movement (speed=0, no position changes)
    - low_speed: Low speed movement (0-10 m/s, 0-36 km/h)
    - medium_speed: Medium speed movement (10-30 m/s, 36-108 km/h)
    - high_speed: High speed movement (30-70 m/s, 108-250 km/h)
    """
    
    def __init__(self, lat: float = 40.7128, lon: float = -74.0060, altitude: float = 10.0, 
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
        self.mode = mode  # "stationary", "low_speed", "medium_speed", or "high_speed"
    
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
            max_speed = 10.0
        elif self.mode == "medium_speed":
            # Medium speed: 10-30 m/s (36-108 km/h)
            target_speed = random.uniform(10.0, 30.0)
            max_accel = 3.0  # m/s^2
            lateral_accel_range = 2.0
            max_speed = 30.0
        else:  # high_speed
            # High speed: 30-70 m/s (108-250 km/h)
            target_speed = random.uniform(30.0, 69.4)  # 69.4 m/s = 250 km/h
            max_accel = 4.0  # m/s^2 (sports car acceleration)
            lateral_accel_range = 2.5
            max_speed = 69.4
        
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
        self.speed = max(0, min(max_speed, self.speed))
        
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
    """Base class for data generators with optional level control.

    Subclasses may define ``LEVEL_BANDS`` to expose Auto / Low / Medium / High
    presets in the GUI. When ``self.level`` is anything other than ``"auto"``
    the generator emits values from the matching band instead of running its
    default (typically the safe/unsafe cycle).
    """

    LEVEL_BANDS = None  # type: ignore  # subclass override: Dict[str, Tuple[float, float]]

    def __init__(self, device_id: str):
        self.device_id = device_id
        self.level = "auto"

    def set_level(self, level: str) -> None:
        if level in ("auto", "low", "medium", "high"):
            self.level = level

    def supports_levels(self) -> bool:
        return self.LEVEL_BANDS is not None

    def _level_band(self):
        """Return (lo, hi) for the current non-auto level, or None."""
        if self.level == "auto" or not self.LEVEL_BANDS:
            return None
        return self.LEVEL_BANDS.get(self.level)

    def generate(self) -> SensorReading:
        raise NotImplementedError


class LocationGenerator(DataGenerator):
    """Generates realistic GPS location data using shared motion state"""
    
    def __init__(self, device_id: str, base_lat: float = 40.7128, base_lon: float = -74.0060, 
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
    """
    Cold-chain / cargo temperature sensor.
    Go thresholds: >8°C or <2°C → alarm. >=12°C → sev4, >=20°C → sev5.
    Cycles: 5 safe readings (3–7 °C) then 5 unsafe readings (>8 or <2 °C).
    """
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (-2.0, 1.9), "medium": (3.0, 7.0), "high": (12.0, 25.0)}

    def __init__(self, device_id: str, base_temp: float = 5.0):
        super().__init__(device_id)
        self.current_temp   = base_temp
        self._reading_count = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> TemperatureReading:
        band = self._level_band()
        if band is not None:
            self.current_temp = round(random.uniform(*band), 2)
            return TemperatureReading(timestamp=time.time(), device_id=self.device_id,
                                      temperature=self.current_temp)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()
        cycle_num = (self._reading_count - 1) // (self.SAFE_READINGS + self.UNSAFE_READINGS)

        if unsafe:
            # Alternate: even cycles → too warm (severity 3→5), odd → too cold (severity 3)
            if cycle_num % 2 == 0:
                self.current_temp = round(random.uniform(9.0, 25.0), 2)  # >8 triggers alarm
            else:
                self.current_temp = round(random.uniform(-2.0, 1.9),  2)  # <2 triggers alarm
        else:
            # Safe: 3–7 °C, small drift
            drift = random.uniform(-0.2, 0.2)
            self.current_temp = round(max(3.0, min(7.0, self.current_temp + drift)), 2)

        return TemperatureReading(
            timestamp=time.time(),
            device_id=self.device_id,
            temperature=self.current_temp
        )


class PressureGenerator(DataGenerator):
    """Generates realistic pressure data"""
    LEVEL_BANDS = {"low": (950.0, 980.0), "medium": (1010.0, 1020.0), "high": (1030.0, 1050.0)}

    def __init__(self, device_id: str, base_pressure: float = 1013.25):
        super().__init__(device_id)
        self.base_pressure = base_pressure
        self.current_pressure = base_pressure

    def generate(self) -> PressureReading:
        band = self._level_band()
        if band is not None:
            self.current_pressure = random.uniform(*band)
        else:
            # Simulate pressure fluctuation
            self.current_pressure += random.uniform(-1.0, 1.0)
            self.current_pressure = max(950, min(1050, self.current_pressure))
        
        return PressureReading(
            timestamp=time.time(),
            device_id=self.device_id,
            pressure=round(self.current_pressure, 2)
        )


class HumidityGenerator(DataGenerator):
    """
    Cargo-hold humidity sensor.
    Go thresholds: >60% or <30% → alarm. >=70.2% → sev4, >=79.8% → sev5.
    Cycles: 5 safe readings (32–58%) then 5 unsafe (>60% or <30%).
    """
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (10.0, 29.0), "medium": (32.0, 58.0), "high": (65.0, 85.0)}

    def __init__(self, device_id: str, base_humidity: float = 45.0):
        super().__init__(device_id)
        self.current_humidity = base_humidity
        self._reading_count   = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> HumidityReading:
        band = self._level_band()
        if band is not None:
            self.current_humidity = round(random.uniform(*band), 2)
            return HumidityReading(timestamp=time.time(), device_id=self.device_id,
                                   humidity=self.current_humidity)

        self._reading_count += 1
        unsafe   = self._is_unsafe_phase()
        cycle_num = (self._reading_count - 1) // (self.SAFE_READINGS + self.UNSAFE_READINGS)

        if unsafe:
            # Alternate: even cycles → too humid (sev 3→5), odd → too dry (sev 3)
            if cycle_num % 2 == 0:
                self.current_humidity = round(random.uniform(61.0, 85.0), 2)  # >60 triggers alarm
            else:
                self.current_humidity = round(random.uniform(10.0, 29.0), 2)  # <30 triggers alarm
        else:
            # Safe: 32–58%, small drift
            drift = random.uniform(-1.0, 1.0)
            self.current_humidity = round(max(32.0, min(58.0, self.current_humidity + drift)), 2)

        return HumidityReading(
            timestamp=time.time(),
            device_id=self.device_id,
            humidity=self.current_humidity
        )


class AccelerometerGenerator(DataGenerator):
    """
    Vehicle accelerometer — also publishes horizontal magnitude as 'acceleration'.
    Go threshold: |acceleration| >= 2.0 m/s² → alarm. >=2.5 → sev4, >=3.0 → sev5.
    Cycles: 5 safe readings (|accel| < 1.5 m/s²) then 5 unsafe (2.5–4.5 m/s²).
    """
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (0.0, 0.5), "medium": (0.5, 1.5), "high": (2.5, 4.5)}

    def __init__(self, device_id: str, motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.motion_state   = motion_state if motion_state else MotionState()
        self._reading_count = 0
        self._unsafe_sign   = 1   # alternate braking / harsh acceleration events

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> AccelerometerReading:
        band = self._level_band()
        if band is not None:
            self._unsafe_sign *= -1
            mag = random.uniform(*band) * self._unsafe_sign
            x_val = round(mag * random.uniform(0.6, 0.9), 3)
            y_val = round(mag * random.uniform(0.1, 0.4), 3)
            z_val = round(9.81 + random.uniform(-0.1, 0.1), 3)
            return AccelerometerReading(timestamp=time.time(), device_id=self.device_id,
                                        x=x_val, y=y_val, z=z_val)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Harsh event: magnitude 2.5–4.5 m/s², alternate direction
            self._unsafe_sign *= -1
            mag   = random.uniform(2.5, 4.5) * self._unsafe_sign
            x_val = round(mag * random.uniform(0.6, 0.9), 3)
            y_val = round(mag * random.uniform(0.1, 0.4), 3)
        else:
            # Normal driving: |horizontal accel| < 1.5 m/s²
            x_val = round(self.motion_state.acceleration_x + random.uniform(-0.3, 0.3), 3)
            y_val = round(self.motion_state.acceleration_y + random.uniform(-0.3, 0.3), 3)
            x_val = max(-1.5, min(1.5, x_val))
            y_val = max(-1.5, min(1.5, y_val))

        z_val = round(9.81 + random.uniform(-0.1, 0.1), 3)  # gravity
        return AccelerometerReading(
            timestamp=time.time(),
            device_id=self.device_id,
            x=x_val,
            y=y_val,
            z=z_val
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
    LEVEL_BANDS = {"low": (350.0, 500.0), "medium": (600.0, 1000.0), "high": (1500.0, 3000.0)}

    def __init__(self, device_id: str, base_ppm: float = 400.0):
        super().__init__(device_id)
        self.current_ppm = base_ppm

    def generate(self) -> CO2Reading:
        band = self._level_band()
        if band is not None:
            self.current_ppm = random.uniform(*band)
        else:
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
    LEVEL_BANDS = {"low": (0.0, 2.0), "medium": (5.0, 15.0), "high": (30.0, 80.0)}

    def __init__(self, device_id: str, base_flow: float = 5.0):
        super().__init__(device_id)
        self.current_flow = base_flow
        self.total_volume = 0.0
        self.last_time = time.time()

    def generate(self) -> FlowReading:
        band = self._level_band()
        if band is not None:
            self.current_flow = random.uniform(*band)
        else:
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
    LEVEL_BANDS = {"low": (5.0, 20.0), "medium": (30.0, 60.0), "high": (75.0, 95.0)}

    def __init__(self, device_id: str, base_moisture: float = 45.0):
        super().__init__(device_id)
        self.current_moisture = base_moisture

    def generate(self) -> SoilMoistureReading:
        band = self._level_band()
        if band is not None:
            self.current_moisture = random.uniform(*band)
        else:
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
    LEVEL_BANDS = {"low": (4.0, 5.5), "medium": (6.0, 7.5), "high": (8.0, 9.5)}

    def __init__(self, device_id: str, base_ph: float = 6.5):
        super().__init__(device_id)
        self.current_ph = base_ph

    def generate(self) -> SoilPHReading:
        band = self._level_band()
        if band is not None:
            self.current_ph = random.uniform(*band)
        else:
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
    LEVEL_BANDS = {"low": (0.0, 50.0), "medium": (200.0, 2000.0), "high": (20000.0, 100000.0)}

    def __init__(self, device_id: str, base_lux: float = 10000.0):
        super().__init__(device_id)
        self.current_lux = base_lux

    def generate(self) -> LightIntensityReading:
        band = self._level_band()
        if band is not None:
            self.current_lux = random.uniform(*band)
        else:
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
    LEVEL_BANDS = {"low": (0.0, 1.0), "medium": (5.0, 15.0), "high": (30.0, 50.0)}

    def __init__(self, device_id: str, base_rain: float = 0.0):
        super().__init__(device_id)
        self.current_rain = base_rain

    def generate(self) -> RainReading:
        band = self._level_band()
        if band is not None:
            self.current_rain = random.uniform(*band)
        elif random.random() < 0.7:  # 70% chance of no rain
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
    LEVEL_BANDS = {"low": (0.0, 3.0), "medium": (8.0, 15.0), "high": (25.0, 30.0)}

    def __init__(self, device_id: str, base_speed: float = 3.0):
        super().__init__(device_id)
        self.current_speed = base_speed
        self.current_direction = random.uniform(0, 360)

    def generate(self) -> WindSpeedReading:
        band = self._level_band()
        if band is not None:
            self.current_speed = random.uniform(*band)
        else:
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
    """
    Vehicle speed sensor.
    Go threshold: 80 km/h → alarm. >=90 → sev4, >=100 → sev5.
    Cycles: 5 safe readings (20–78 km/h) then 5 unsafe (85–150 km/h).
    Speed stored in m/s internally; SenML encoder converts to km/h or MPH.
    """
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    # Bands in m/s. Low ≈ urban, Medium ≈ city/suburb, High ≈ highway/over-speed
    LEVEL_BANDS = {"low": (0.0, 8.0), "medium": (10.0, 20.0), "high": (25.0, 40.0)}

    # Go threshold is 80 km/h → 22.22 m/s
    SAFE_MAX_MS  = 21.5   # ~77.4 km/h
    UNSAFE_MIN_MS = 23.7  # ~85.3 km/h  — severity 3
    UNSAFE_HI_MS  = 41.7  # ~150 km/h   — severity 5

    def __init__(self, device_id: str, motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.motion_state   = motion_state if motion_state else MotionState()
        self._reading_count = 0
        self._unsafe_speed  = self.UNSAFE_MIN_MS

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> SpeedReading:
        band = self._level_band()
        if band is not None:
            speed_ms = round(random.uniform(*band), 2)
            return SpeedReading(timestamp=time.time(), device_id=self.device_id,
                                speed=speed_ms, heading=round(self.motion_state.heading, 1))

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Escalate through severity levels across the unsafe window
            pos_in_unsafe = (self._reading_count - 1) % (self.SAFE_READINGS + self.UNSAFE_READINGS) - self.SAFE_READINGS
            # readings 0-1 → sev3 (>80), 2-3 → sev4 (>90), 4 → sev5 (>100)
            if pos_in_unsafe <= 1:
                speed_ms = round(random.uniform(22.3, 25.0), 2)   # 80–90 km/h
            elif pos_in_unsafe <= 3:
                speed_ms = round(random.uniform(25.1, 27.7), 2)   # 90–99.7 km/h
            else:
                speed_ms = round(random.uniform(27.8, 41.7), 2)   # 100–150 km/h
        else:
            # Safe: use motion state but cap below threshold
            speed_ms = round(min(self.motion_state.speed, self.SAFE_MAX_MS), 2)
            if speed_ms < 1.0:
                speed_ms = round(random.uniform(5.0, 20.0), 2)    # at least some movement

        return SpeedReading(
            timestamp=time.time(),
            device_id=self.device_id,
            speed=speed_ms,
            heading=round(self.motion_state.heading, 1)
        )


class FuelConsumptionGenerator(DataGenerator):
    """
    Vehicle fuel consumption sensor.
    Go threshold: 12.0 L/100km → alarm. >=15.96 → sev4, >=20.04 → sev5.
    Cycles: 5 safe readings (7–11.9 L/100km) then 5 unsafe (13–25 L/100km).
    """
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    # Bands in L/100km. Low = efficient/highway cruise, Medium = normal, High = leak / heavy load
    LEVEL_BANDS = {"low": (5.0, 7.0), "medium": (8.0, 12.0), "high": (16.0, 25.0)}

    def __init__(self, device_id: str, tank_capacity: float = 50.0,
                 motion_state: Optional[MotionState] = None):
        super().__init__(device_id)
        self.fuel_level      = random.uniform(50, 100)
        self.total_consumed  = 0.0
        self.tank_capacity   = tank_capacity
        self.motion_state    = motion_state if motion_state else MotionState()
        self._reading_count  = 0
        self._consumption    = 8.0   # starting safe value

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> FuelConsumptionReading:
        band = self._level_band()
        if band is not None:
            consumption_l_100km = round(random.uniform(*band), 2)
            consumption_mpg = round(235.215 / consumption_l_100km, 1)
            # Still update fuel level + total to keep readings coherent
            speed_kmh = self.motion_state.speed * 3.6
            interval_hours = 5.0 / 3600.0
            distance_km = speed_kmh * interval_hours
            consumed = (consumption_l_100km / 100.0) * distance_km if distance_km > 0 else 0.8 * interval_hours
            self.total_consumed += consumed
            self.fuel_level = max(0.0, self.fuel_level - (consumed / self.tank_capacity) * 100)
            return FuelConsumptionReading(
                timestamp=time.time(), device_id=self.device_id,
                consumption_l_100km=consumption_l_100km, consumption_mpg=consumption_mpg,
                fuel_level=round(self.fuel_level, 1), total_consumed=round(self.total_consumed, 3))

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Escalate: sev3 (>12), sev4 (>=15.96), sev5 (>=20.04)
            pos = (self._reading_count - 1) % (self.SAFE_READINGS + self.UNSAFE_READINGS) - self.SAFE_READINGS
            if pos <= 1:
                consumption_l_100km = round(random.uniform(12.1, 15.9), 2)   # sev 3
            elif pos <= 3:
                consumption_l_100km = round(random.uniform(16.0, 20.0), 2)   # sev 4
            else:
                consumption_l_100km = round(random.uniform(20.1, 25.0), 2)   # sev 5 — possible leak
        else:
            # Safe: 7–11.9 L/100km, smooth drift
            drift = random.uniform(-0.5, 0.5)
            self._consumption   = round(max(7.0, min(11.9, self._consumption + drift)), 2)
            consumption_l_100km = self._consumption

        consumption_mpg = round(235.215 / consumption_l_100km, 1)

        # Update fuel level
        speed_kmh = self.motion_state.speed * 3.6
        interval_hours = 5.0 / 3600.0
        distance_km = speed_kmh * interval_hours
        consumed = (consumption_l_100km / 100.0) * distance_km if distance_km > 0 else 0.8 * interval_hours
        self.total_consumed += consumed
        self.fuel_level = max(0.0, self.fuel_level - (consumed / self.tank_capacity) * 100)

        return FuelConsumptionReading(
            timestamp=time.time(),
            device_id=self.device_id,
            consumption_l_100km=consumption_l_100km,
            consumption_mpg=consumption_mpg,
            fuel_level=round(self.fuel_level, 1),
            total_consumed=round(self.total_consumed, 3)
        )


# ==================== Water Metering Generators ====================

class WaterMeterGenerator(DataGenerator):
    """Generates water meter data — 5 safe readings then 5 unsafe (burst/leak), repeating."""

    # Unsafe threshold from Go script: flow_rate >= 50.0 L/min = burst pipe
    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (0.0, 2.0), "medium": (5.0, 15.0), "high": (50.0, 80.0)}

    def __init__(self, device_id: str, pipe_diameter_mm: float = 25.0):
        super().__init__(device_id)
        self.pipe_diameter_mm    = pipe_diameter_mm
        self.cumulative_volume   = 0.0   # m³
        self._prev_flow          = 0.0
        self._reading_count      = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> WaterMeterReading:
        band = self._level_band()
        if band is not None:
            flow_rate = round(random.uniform(*band), 3)
            leak_detected = self.level == "high"
            self._prev_flow = flow_rate
            interval_min = 5.0 / 60.0
            self.cumulative_volume += (flow_rate * interval_min) / 1000.0
            return WaterMeterReading(
                timestamp=time.time(), device_id=self.device_id,
                flow_rate=flow_rate,
                cumulative_volume=round(self.cumulative_volume, 6),
                leak_detected=leak_detected)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Burst pipe: flow_rate >= 50.0 L/min triggers valve close
            flow_rate      = round(random.uniform(50.0, 80.0), 3)
            leak_detected  = True
        else:
            # Normal residential flow: 0.5 – 15 L/min
            base_flow  = random.uniform(0.5, 8.0)
            flow_rate  = round(0.6 * self._prev_flow + 0.4 * base_flow + random.uniform(-0.1, 0.1), 3)
            flow_rate  = max(0.0, min(flow_rate, 49.0))
            leak_detected = False

        self._prev_flow = flow_rate
        interval_min = 5.0 / 60.0
        self.cumulative_volume += (flow_rate * interval_min) / 1000.0  # L → m³

        return WaterMeterReading(
            timestamp=time.time(),
            device_id=self.device_id,
            flow_rate=flow_rate,
            cumulative_volume=round(self.cumulative_volume, 6),
            leak_detected=leak_detected
        )


class WaterPHGenerator(DataGenerator):
    """Generates water pH — 5 safe readings (6.5–8.5) then 5 unsafe (< 6.5 or > 8.5)."""

    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (4.5, 6.4), "medium": (6.5, 8.5), "high": (8.6, 10.0)}

    def __init__(self, device_id: str, base_ph: float = 7.4):
        super().__init__(device_id)
        self.ph              = base_ph
        self._reading_count  = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> WaterPHReading:
        band = self._level_band()
        if band is not None:
            self.ph = round(random.uniform(*band), 2)
            return WaterPHReading(timestamp=time.time(), device_id=self.device_id, ph=self.ph)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Alternate between acidic (< 6.5) and alkaline (> 8.5) events
            if (self._reading_count // (self.SAFE_READINGS + self.UNSAFE_READINGS)) % 2 == 0:
                self.ph = round(random.uniform(4.5, 6.4), 2)   # too acidic
            else:
                self.ph = round(random.uniform(8.6, 10.0), 2)  # too alkaline
        else:
            drift   = random.gauss(0, 0.03)
            self.ph = round(max(6.5, min(8.5, self.ph + drift)), 2)

        return WaterPHReading(
            timestamp=time.time(),
            device_id=self.device_id,
            ph=self.ph
        )


class WaterTurbidityGenerator(DataGenerator):
    """Generates turbidity — 5 safe readings (< 4.0 NTU) then 5 unsafe (>= 4.0 NTU)."""

    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (0.05, 1.0), "medium": (1.0, 3.9), "high": (4.0, 12.0)}

    def __init__(self, device_id: str):
        super().__init__(device_id)
        self.turbidity       = random.uniform(0.1, 1.0)
        self._reading_count  = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> WaterTurbidityReading:
        band = self._level_band()
        if band is not None:
            self.turbidity = round(random.uniform(*band), 3)
            return WaterTurbidityReading(timestamp=time.time(), device_id=self.device_id,
                                         turbidity=self.turbidity)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # High turbidity: >= 4.0 NTU (contamination event)
            self.turbidity = round(random.uniform(4.0, 12.0), 3)
        else:
            self.turbidity = max(0.05, self.turbidity + random.gauss(0, 0.05))
            self.turbidity = round(min(self.turbidity, 3.9), 3)

        return WaterTurbidityReading(
            timestamp=time.time(),
            device_id=self.device_id,
            turbidity=self.turbidity
        )


class WaterTDSGenerator(DataGenerator):
    """Generates TDS/conductivity — 5 safe readings then 5 unsafe (TDS >= 1000 ppm)."""

    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (50.0, 150.0), "medium": (200.0, 500.0), "high": (1000.0, 1800.0)}

    def __init__(self, device_id: str, base_tds: float = 150.0):
        super().__init__(device_id)
        self.tds             = base_tds  # ppm
        self._reading_count  = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> WaterTDSReading:
        band = self._level_band()
        if band is not None:
            self.tds = round(random.uniform(*band), 1)
            conductivity = round(self.tds * 2.0 + random.uniform(-5, 5), 1)
            return WaterTDSReading(timestamp=time.time(), device_id=self.device_id,
                                   tds=self.tds, conductivity=max(0.0, conductivity))

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # TDS >= 1000 ppm → not suitable for drinking
            # Conductivity >= 1500 µS/cm → critical contamination
            self.tds    = round(random.uniform(1000.0, 1800.0), 1)
        else:
            drift    = random.gauss(0, 1.5)
            self.tds = round(max(50.0, min(999.0, self.tds + drift)), 1)

        conductivity = round(self.tds * 2.0 + random.uniform(-5, 5), 1)
        return WaterTDSReading(
            timestamp=time.time(),
            device_id=self.device_id,
            tds=self.tds,
            conductivity=max(0.0, conductivity)
        )


class ChlorineGenerator(DataGenerator):
    """Generates chlorine — 5 safe readings (0.1–4.0 mg/L) then 5 unsafe (< 0.1 or >= 4.0)."""

    SAFE_READINGS   = 5
    UNSAFE_READINGS = 5
    LEVEL_BANDS = {"low": (0.0, 0.09), "medium": (0.5, 2.0), "high": (4.0, 6.0)}

    def __init__(self, device_id: str, base_chlorine: float = 0.8):
        super().__init__(device_id)
        self.chlorine        = base_chlorine
        self._reading_count  = 0

    def _is_unsafe_phase(self) -> bool:
        cycle = self.SAFE_READINGS + self.UNSAFE_READINGS
        return (self._reading_count % cycle) >= self.SAFE_READINGS

    def generate(self) -> ChlorineReading:
        band = self._level_band()
        if band is not None:
            self.chlorine = round(random.uniform(*band), 3)
            return ChlorineReading(timestamp=time.time(), device_id=self.device_id,
                                   chlorine=self.chlorine)

        self._reading_count += 1
        unsafe = self._is_unsafe_phase()

        if unsafe:
            # Alternate under-chlorinated and over-chlorinated events
            if (self._reading_count // (self.SAFE_READINGS + self.UNSAFE_READINGS)) % 2 == 0:
                self.chlorine = round(random.uniform(0.0, 0.09), 3)   # too low → bacteria risk
            else:
                self.chlorine = round(random.uniform(4.0, 6.0), 3)    # too high → chemical risk
        else:
            drift         = random.gauss(0, 0.02)
            self.chlorine = round(max(0.1, min(3.99, self.chlorine + drift)), 3)

        return ChlorineReading(
            timestamp=time.time(),
            device_id=self.device_id,
            chlorine=self.chlorine
        )
