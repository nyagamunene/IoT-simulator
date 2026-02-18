"""
IoT Device Simulator - Actuators Library
Contains actuator (controllable device) models
"""

import time
from typing import Dict, Any


# ==================== Actuators ====================

class Actuator:
    """Base class for actuators (controllable devices)"""
    
    def __init__(self, device_id: str, name: str):
        self.device_id = device_id
        self.name = name
        self.state = {}
        self.last_updated = time.time()
    
    def update_state(self, command: Dict[str, Any]):
        """Update actuator state based on command"""
        raise NotImplementedError
    
    def get_state(self) -> Dict[str, Any]:
        """Get current actuator state"""
        return {
            "device_id": self.device_id,
            "name": self.name,
            "timestamp": self.last_updated,
            **self.state
        }


class BulbActuator(Actuator):
    """Smart bulb actuator - can be turned on/off and brightness controlled"""
    
    def __init__(self, device_id: str, name: str = "Smart Bulb"):
        super().__init__(device_id, name)
        self.state = {
            "power": "off",
            "brightness": 0,
            "color": "#FFFFFF"
        }
    
    def update_state(self, command: Dict[str, Any]):
        """
        Update bulb state
        Expected command format: {"power": "on"/"off", "brightness": 0-100, "color": "#RRGGBB"}
        """
        self.last_updated = time.time()
        
        if "power" in command:
            power = str(command["power"]).lower()
            if power in ["on", "off", "1", "0", "true", "false"]:
                self.state["power"] = "on" if power in ["on", "1", "true"] else "off"
        
        if "brightness" in command and self.state["power"] == "on":
            try:
                brightness = int(command["brightness"])
                self.state["brightness"] = max(0, min(100, brightness))
            except (ValueError, TypeError):
                pass
        
        if "color" in command and self.state["power"] == "on":
            self.state["color"] = str(command["color"])
        
        # If turned off, set brightness to 0
        if self.state["power"] == "off":
            self.state["brightness"] = 0


class RelayActuator(Actuator):
    """Relay actuator - simple on/off switch"""
    
    def __init__(self, device_id: str, name: str = "Relay"):
        super().__init__(device_id, name)
        self.state = {
            "power": "off"
        }
    
    def update_state(self, command: Dict[str, Any]):
        """
        Update relay state
        Expected command format: {"power": "on"/"off"}
        """
        self.last_updated = time.time()
        
        if "power" in command:
            power = str(command["power"]).lower()
            if power in ["on", "off", "1", "0", "true", "false"]:
                self.state["power"] = "on" if power in ["on", "1", "true"] else "off"


class ThermostatActuator(Actuator):
    """Thermostat actuator - temperature control"""
    
    def __init__(self, device_id: str, name: str = "Thermostat"):
        super().__init__(device_id, name)
        self.state = {
            "power": "off",
            "mode": "auto",  # auto, heat, cool
            "target_temperature": 22.0,
            "current_temperature": 20.0
        }
    
    def update_state(self, command: Dict[str, Any]):
        """
        Update thermostat state
        Expected command format: {"power": "on"/"off", "mode": "auto"/"heat"/"cool", "target_temperature": float}
        """
        self.last_updated = time.time()
        
        if "power" in command:
            power = str(command["power"]).lower()
            if power in ["on", "off", "1", "0", "true", "false"]:
                self.state["power"] = "on" if power in ["on", "1", "true"] else "off"
        
        if "mode" in command and self.state["power"] == "on":
            mode = str(command["mode"]).lower()
            if mode in ["auto", "heat", "cool"]:
                self.state["mode"] = mode
        
        if "target_temperature" in command and self.state["power"] == "on":
            try:
                temp = float(command["target_temperature"])
                self.state["target_temperature"] = max(10, min(35, temp))
            except (ValueError, TypeError):
                pass
