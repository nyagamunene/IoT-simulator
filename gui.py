"""
IoT Device Simulator - GUI Module
Contains the graphical user interface for the simulator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import queue
from typing import Dict, Any

# Import sensor generators
from sensors import (
    LocationGenerator, TemperatureGenerator, PressureGenerator,
    HumidityGenerator, AccelerometerGenerator, CO2Generator,
    FlowGenerator, SoilMoistureGenerator, SoilPHGenerator,
    LightIntensityGenerator, RainGenerator, WindSpeedGenerator
)


class SimulatorGUI:
    """GUI for IoT Device Simulator"""
    
    def __init__(self, root, simulator_class):
        self.root = root
        self.root.title("IoT Device Simulator")
        self.root.geometry("900x700")
        
        self.simulator_class = simulator_class
        self.simulator = None
        self.log_update_job = None
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Device Configuration
        config_frame = ttk.LabelFrame(main_frame, text="Device Configuration", padding="10")
        config_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(config_frame, text="Device ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.device_id_var = tk.StringVar(value="device_001")
        ttk.Entry(config_frame, textvariable=self.device_id_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(config_frame, text="Interval (sec):").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.interval_var = tk.StringVar(value="5")
        ttk.Entry(config_frame, textvariable=self.interval_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Sensor Selection
        sensor_frame = ttk.LabelFrame(main_frame, text="Sensors", padding="10")
        sensor_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=5, padx=(0, 5))
        
        self.sensor_vars = {}
        sensors = [
            ("Location (GPS)", "location"),
            ("Temperature", "temperature"),
            ("Pressure", "pressure"),
            ("Humidity", "humidity"),
            ("Accelerometer", "accelerometer"),
            ("CO2 (PPM)", "co2"),
            ("Flow Rate", "flow"),
            ("Soil Moisture", "soil_moisture"),
            ("Soil pH", "soil_ph"),
            ("Light Intensity", "light"),
            ("Rain", "rain"),
            ("Wind Speed", "wind")
        ]
        
        for i, (label, key) in enumerate(sensors):
            var = tk.BooleanVar(value=True if i < 2 else False)
            self.sensor_vars[key] = var
            ttk.Checkbutton(sensor_frame, text=label, variable=var).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Protocol Configuration
        protocol_frame = ttk.LabelFrame(main_frame, text="Protocol Configuration", padding="10")
        protocol_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        ttk.Label(protocol_frame, text="Protocol:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.protocol_var = tk.StringVar(value="HTTP")
        protocol_combo = ttk.Combobox(protocol_frame, textvariable=self.protocol_var, 
                                      values=["MQTT", "HTTP", "WebSocket", "CoAP"], 
                                      state="readonly", width=15)
        protocol_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        protocol_combo.bind('<<ComboboxSelected>>', self._on_protocol_change)
        
        ttk.Label(protocol_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.format_var = tk.StringVar(value="JSON")
        ttk.Combobox(protocol_frame, textvariable=self.format_var, 
                     values=["JSON", "SenML"], state="readonly", width=15).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # TLS/Security Configuration
        tls_frame = ttk.LabelFrame(protocol_frame, text="Security (TLS/mTLS)", padding="5")
        tls_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        
        self.tls_mode_var = tk.StringVar(value="none")
        ttk.Radiobutton(tls_frame, text="None", variable=self.tls_mode_var, value="none",
                       command=self._on_tls_mode_change).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Radiobutton(tls_frame, text="TLS", variable=self.tls_mode_var, value="tls",
                       command=self._on_tls_mode_change).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(tls_frame, text="mTLS", variable=self.tls_mode_var, value="mtls",
                       command=self._on_tls_mode_change).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # TLS Certificate Frame
        self.tls_cert_frame = ttk.Frame(protocol_frame)
        self.tls_cert_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # CA Certificate (for both TLS and mTLS)
        ttk.Label(self.tls_cert_frame, text="CA Cert:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ca_cert_var = tk.StringVar(value="")
        ca_entry = ttk.Entry(self.tls_cert_frame, textvariable=self.ca_cert_var, width=20)
        ca_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        ttk.Button(self.tls_cert_frame, text="Browse", width=8,
                  command=lambda: self._browse_file(self.ca_cert_var)).grid(row=0, column=2, pady=2)
        
        # Client Certificate (for mTLS only)
        self.client_cert_label = ttk.Label(self.tls_cert_frame, text="Client Cert:")
        self.client_cert_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        self.client_cert_var = tk.StringVar(value="")
        self.client_cert_entry = ttk.Entry(self.tls_cert_frame, textvariable=self.client_cert_var, width=20)
        self.client_cert_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        self.client_cert_button = ttk.Button(self.tls_cert_frame, text="Browse", width=8,
                  command=lambda: self._browse_file(self.client_cert_var))
        self.client_cert_button.grid(row=1, column=2, pady=2)
        
        # Client Key (for mTLS only)
        self.client_key_label = ttk.Label(self.tls_cert_frame, text="Client Key:")
        self.client_key_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        self.client_key_var = tk.StringVar(value="")
        self.client_key_entry = ttk.Entry(self.tls_cert_frame, textvariable=self.client_key_var, width=20)
        self.client_key_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        self.client_key_button = ttk.Button(self.tls_cert_frame, text="Browse", width=8,
                  command=lambda: self._browse_file(self.client_key_var))
        self.client_key_button.grid(row=2, column=2, pady=2)
        
        # Initially hide TLS cert frame and client cert fields
        self.tls_cert_frame.grid_remove()
        self._hide_client_cert_fields()
        
        # Protocol-specific settings
        self.protocol_settings_frame = ttk.Frame(protocol_frame)
        self.protocol_settings_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self._create_protocol_settings()
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="Start Simulation", command=self._start_simulation)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Simulation", command=self._stop_simulation, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).grid(row=0, column=2, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def _create_protocol_settings(self):
        # Clear existing widgets
        for widget in self.protocol_settings_frame.winfo_children():
            widget.destroy()
        
        protocol = self.protocol_var.get()
        
        if protocol == "MQTT":
            ttk.Label(self.protocol_settings_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.mqtt_broker_var = tk.StringVar(value="localhost")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_broker_var, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.mqtt_port_var = tk.StringVar(value="1883")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_port_var, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.mqtt_topic_var = tk.StringVar(value="iot/data")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_topic_var, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "HTTP":
            ttk.Label(self.protocol_settings_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.http_url_var = tk.StringVar(value="http://localhost:8080/data")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_url_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Method:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.http_method_var = tk.StringVar(value="POST")
            ttk.Combobox(self.protocol_settings_frame, textvariable=self.http_method_var, 
                        values=["POST", "PUT"], state="readonly", width=27).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "WebSocket":
            ttk.Label(self.protocol_settings_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.ws_url_var = tk.StringVar(value="ws://localhost:8765/")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_url_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "CoAP":
            ttk.Label(self.protocol_settings_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.coap_url_var = tk.StringVar(value="coap://localhost:5683/data")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_url_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
    
    def _on_protocol_change(self, event=None):
        self._create_protocol_settings()
    
    def _on_tls_mode_change(self):
        """Handle TLS mode selection changes"""
        tls_mode = self.tls_mode_var.get()
        
        if tls_mode == "none":
            # Hide all certificate fields
            self.tls_cert_frame.grid_remove()
        elif tls_mode == "tls":
            # Show CA cert field only (hide client cert and key)
            self.tls_cert_frame.grid()
            self._hide_client_cert_fields()
        elif tls_mode == "mtls":
            # Show all certificate fields (CA cert, client cert, and client key)
            self.tls_cert_frame.grid()
            self._show_client_cert_fields()
    
    def _hide_client_cert_fields(self):
        """Hide client certificate and key fields (for TLS mode)"""
        self.client_cert_label.grid_remove()
        self.client_cert_entry.grid_remove()
        self.client_cert_button.grid_remove()
        self.client_key_label.grid_remove()
        self.client_key_entry.grid_remove()
        self.client_key_button.grid_remove()
    
    def _show_client_cert_fields(self):
        """Show client certificate and key fields (for mTLS mode)"""
        self.client_cert_label.grid()
        self.client_cert_entry.grid()
        self.client_cert_button.grid()
        self.client_key_label.grid()
        self.client_key_entry.grid()
        self.client_key_button.grid()
    
    def _browse_file(self, var):
        """Open file browser to select certificate/key file"""
        filename = filedialog.askopenfilename(
            title="Select Certificate/Key File",
            filetypes=[
                ("Certificate Files", "*.pem *.crt *.cer *.key"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            var.set(filename)
    
    def _start_simulation(self):
        try:
            # Create simulator
            device_id = self.device_id_var.get()
            self.simulator = self.simulator_class(device_id)
            
            # Add selected sensors
            if self.sensor_vars['location'].get():
                self.simulator.add_generator('location', LocationGenerator(device_id))
            if self.sensor_vars['temperature'].get():
                self.simulator.add_generator('temperature', TemperatureGenerator(device_id))
            if self.sensor_vars['pressure'].get():
                self.simulator.add_generator('pressure', PressureGenerator(device_id))
            if self.sensor_vars['humidity'].get():
                self.simulator.add_generator('humidity', HumidityGenerator(device_id))
            if self.sensor_vars['accelerometer'].get():
                self.simulator.add_generator('accelerometer', AccelerometerGenerator(device_id))
            if self.sensor_vars['co2'].get():
                self.simulator.add_generator('co2', CO2Generator(device_id))
            if self.sensor_vars['flow'].get():
                self.simulator.add_generator('flow', FlowGenerator(device_id))
            if self.sensor_vars['soil_moisture'].get():
                self.simulator.add_generator('soil_moisture', SoilMoistureGenerator(device_id))
            if self.sensor_vars['soil_ph'].get():
                self.simulator.add_generator('soil_ph', SoilPHGenerator(device_id))
            if self.sensor_vars['light'].get():
                self.simulator.add_generator('light', LightIntensityGenerator(device_id))
            if self.sensor_vars['rain'].get():
                self.simulator.add_generator('rain', RainGenerator(device_id))
            if self.sensor_vars['wind'].get():
                self.simulator.add_generator('wind', WindSpeedGenerator(device_id))
            
            if not any(var.get() for var in self.sensor_vars.values()):
                messagebox.showerror("Error", "Please select at least one sensor")
                return
            
            # Set protocol
            protocol = self.protocol_var.get()
            config = self._get_protocol_config()
            self.simulator.set_protocol(protocol, config)
            
            # Set format
            self.simulator.set_format(self.format_var.get())
            
            # Set interval
            self.simulator.interval = float(self.interval_var.get())
            
            # Start simulator
            self.simulator.start()
            
            # Update UI
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Status: Running ({protocol} - {self.format_var.get()})")
            
            self._log("Simulation started")
            self._update_log()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start simulation: {e}")
            self._log(f"Error: {e}")
    
    def _stop_simulation(self):
        if self.simulator:
            self.simulator.stop()
            self.simulator = None
        
        if self.log_update_job:
            self.root.after_cancel(self.log_update_job)
            self.log_update_job = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Status: Stopped")
        self._log("Simulation stopped")
    
    def _get_protocol_config(self) -> Dict[str, Any]:
        protocol = self.protocol_var.get()
        tls_mode = self.tls_mode_var.get()
        
        # Base config for each protocol  
        config = {}
        
        if protocol == "MQTT":
            config = {
                'broker': self.mqtt_broker_var.get(),
                'port': int(self.mqtt_port_var.get()),
                'topic': self.mqtt_topic_var.get(),
                'client_id': self.device_id_var.get()
            }
        elif protocol == "HTTP":
            config = {
                'url': self.http_url_var.get(),
                'method': self.http_method_var.get()
            }
        elif protocol == "WebSocket":
            config = {
                'url': self.ws_url_var.get()
            }
        elif protocol == "CoAP":
            config = {
                'url': self.coap_url_var.get()
            }
        
        # Add TLS configuration if enabled
        if tls_mode != "none":
            config['tls_mode'] = tls_mode
            
            # Add CA certificate if provided
            ca_cert = self.ca_cert_var.get().strip()
            if ca_cert:
                config['ca_cert'] = ca_cert
            
            # Add client certificate and key for mTLS
            if tls_mode == "mtls":
                client_cert = self.client_cert_var.get().strip()
                client_key = self.client_key_var.get().strip()
                
                if client_cert:
                    config['client_cert'] = client_cert
                if client_key:
                    config['client_key'] = client_key
        
        return config
    
    def _update_log(self):
        if self.simulator:
            try:
                while True:
                    message = self.simulator.message_queue.get_nowait()
                    self._log(message)
            except queue.Empty:
                pass
            
            # Schedule next update
            self.log_update_job = self.root.after(100, self._update_log)
    
    def _log(self, message: str):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
