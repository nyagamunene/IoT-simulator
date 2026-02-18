"""
IoT Device Simulator - GUI Module
Contains the graphical user interface for the simulator
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import queue
from typing import Dict, Any

# Import sensor generators
from lib.sensors import (
    LocationGenerator, TemperatureGenerator, PressureGenerator,
    HumidityGenerator, AccelerometerGenerator, CO2Generator,
    FlowGenerator, SoilMoistureGenerator, SoilPHGenerator,
    LightIntensityGenerator, RainGenerator, WindSpeedGenerator
)


class SimulatorGUI:
    """GUI for IoT Device Simulator"""
    
    def __init__(self, root, simulator_class):
        self.root = root
        self.root.title("IoT Device Simulator - Publisher")
        self.root.geometry("900x700")
        
        self.simulator_class = simulator_class
        self.simulator = None
        self.log_update_job = None
        
        self._create_menu()
        self._create_widgets()
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="MQTT Subscriber...", command=self._launch_subscriber)
        tools_menu.add_separator()
        tools_menu.add_command(label="Exit", command=self.root.quit)
    
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
        
        # Authentication (for all protocols)
        ttk.Label(config_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value="")
        ttk.Entry(config_frame, textvariable=self.username_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(config_frame, text="Password:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.password_var = tk.StringVar(value="")
        ttk.Entry(config_frame, textvariable=self.password_var, width=10, show="*").grid(row=1, column=3, sticky=tk.W, pady=2)
        
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
            var = tk.BooleanVar(value=True if key == 'temperature' else False)
            self.sensor_vars[key] = var
            ttk.Checkbutton(sensor_frame, text=label, variable=var).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Protocol Configuration
        protocol_frame = ttk.LabelFrame(main_frame, text="Protocol Configuration", padding="10")
        protocol_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N), pady=5)
        
        ttk.Label(protocol_frame, text="Protocol:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.protocol_var = tk.StringVar(value="MQTT")
        protocol_combo = ttk.Combobox(protocol_frame, textvariable=self.protocol_var, 
                                      values=["MQTT", "HTTP", "WebSocket", "CoAP"], 
                                      state="readonly", width=15)
        protocol_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        protocol_combo.bind('<<ComboboxSelected>>', self._on_protocol_change)
        
        ttk.Label(protocol_frame, text="Format:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.format_var = tk.StringVar(value="SenML")
        ttk.Combobox(protocol_frame, textvariable=self.format_var, 
                     values=["JSON", "SenML"], state="readonly", width=15).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # TLS/Security Configuration
        tls_frame = ttk.LabelFrame(protocol_frame, text="Security (TLS/mTLS)", padding="5")
        tls_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 5))
        
        self.tls_mode_var = tk.StringVar(value="tls")
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
        self.ca_cert_var = tk.StringVar(value="/etc/ssl/certs/ca-certificates.crt")
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
        
        # Initially show TLS cert frame (TLS is default) and hide client cert fields
        self.tls_cert_frame.grid()
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
        
        ttk.Button(button_frame, text="Detach Logs", command=self._detach_logs).grid(row=0, column=3, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=100, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Detachable log window reference
        self.detached_log_window = None
        
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
            self.mqtt_broker_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_broker_var, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.mqtt_port_var = tk.StringVar(value="8883")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_port_var, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.mqtt_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_topic_var, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "HTTP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.http_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.http_port_var = tk.StringVar(value="8443")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.http_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Method:").grid(row=3, column=0, sticky=tk.W, pady=2)
            self.http_method_var = tk.StringVar(value="POST")
            ttk.Combobox(self.protocol_settings_frame, textvariable=self.http_method_var, 
                        values=["POST", "PUT"], state="readonly", width=27).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "WebSocket":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.ws_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.ws_port_var = tk.StringVar(value="8443")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.ws_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "CoAP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.coap_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.coap_port_var = tk.StringVar(value="5683")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.coap_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
    
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
            
            # Log detailed configuration
            self._log("="*60)
            self._log(f"Starting simulation with {protocol} protocol")
            self._log(f"Format: {self.format_var.get()}")
            self._log(f"Device ID: {device_id}")
            self._log(f"Interval: {self.interval_var.get()}s")
            self._log("-"*60)
            
            if protocol == "MQTT":
                self._log(f"MQTT Broker: {config.get('broker')}:{config.get('port')}")
                self._log(f"MQTT Topic: {config.get('topic')}")
                self._log(f"Client ID: {config.get('client_id')}")
                self._log(f"Username: {config.get('username', 'None')}")
                self._log(f"TLS Mode: {config.get('tls_mode', 'none')}")
            elif protocol == "HTTP":
                self._log(f"HTTP URL: {config.get('url')}")
                self._log(f"Method: {config.get('method')}")
                self._log(f"Auth Header: {'Set' if config.get('auth_header') else 'None'}")
            elif protocol == "WebSocket":
                self._log(f"WebSocket URL: {config.get('url')}")
            elif protocol == "CoAP":
                self._log(f"CoAP URL: {config.get('url')}")
                self._log(f"Auth: {'Set' if config.get('auth') else 'None'}")
            
            self._log("-"*60)
            self._log("Attempting to connect...")
            
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
            
            self._log("✓ Simulation started successfully")
            self._log("="*60)
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
        
        # Get global credentials (used for all protocols)
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Base config for each protocol  
        config = {}
        
        if protocol == "MQTT":
            config = {
                'broker': self.mqtt_broker_var.get(),
                'port': int(self.mqtt_port_var.get()),
                'topic': self.mqtt_topic_var.get(),
                'client_id': self.device_id_var.get()
            }
            
            # Add username and password for MQTT
            if username:
                config['username'] = username
            if password:
                config['password'] = password
        elif protocol == "HTTP":
            # Build URL from host, port, and topic
            host = self.http_host_var.get()
            port = self.http_port_var.get()
            topic = self.http_topic_var.get()
            
            # Use HTTPS for secure ports (443, 8443), HTTP for others
            protocol_scheme = 'https' if port in ['443', '8443'] else 'http'
            url = f"{protocol_scheme}://{host}:{port}/{topic.lstrip('/')}"
            
            config = {
                'url': url,
                'method': self.http_method_var.get()
            }
            
            if username and password:
                config['auth_header'] = f"Client {password}"
        elif protocol == "WebSocket":
            # Build URL from host, port, and topic
            host = self.ws_host_var.get()
            port = self.ws_port_var.get()
            topic = self.ws_topic_var.get()
            
            # Use WSS for secure ports (443, 8443), WS for others
            protocol_scheme = 'wss' if port in ['443', '8443'] else 'ws'
            url = f"{protocol_scheme}://{host}:{port}/{topic.lstrip('/')}"
            
            # Add authorization as URL parameter for WebSocket (as per wscat example)
            if password:
                separator = '&' if '?' in url else '?'
                url = f"{url}{separator}authorization={password}"
            
            config = {
                'url': url
            }
        elif protocol == "CoAP":
            # Build URL from host, port, and topic
            host = self.coap_host_var.get()
            port = self.coap_port_var.get()
            topic = self.coap_topic_var.get()
            
            # Use COAPS for secure ports (5684), COAP for others
            protocol_scheme = 'coaps' if port == '5684' else 'coap'
            url = f"{protocol_scheme}://{host}:{port}/{topic.lstrip('/')}"
            
            config = {
                'url': url
            }
            
            # Add auth for CoAP (-a flag in coap-cli)
            if password:
                config['auth'] = password
        
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
        
        # Also update detached log window if it exists
        if self.detached_log_window and hasattr(self.detached_log_window, 'log_text'):
            try:
                self.detached_log_window.log_text.config(state=tk.NORMAL)
                self.detached_log_window.log_text.insert(tk.END, message + "\n")
                self.detached_log_window.log_text.see(tk.END)
                self.detached_log_window.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Window was closed
                self.detached_log_window = None
    
    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Also clear detached log window if it exists
        if self.detached_log_window and hasattr(self.detached_log_window, 'log_text'):
            try:
                self.detached_log_window.log_text.config(state=tk.NORMAL)
                self.detached_log_window.log_text.delete(1.0, tk.END)
                self.detached_log_window.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Window was closed
                self.detached_log_window = None
    
    def _detach_logs(self):
        """Create a detachable log window"""
        if self.detached_log_window and self.detached_log_window.winfo_exists():
            # Window already exists, bring it to front
            self.detached_log_window.lift()
            self.detached_log_window.focus_force()
            return
        
        # Create new detached window
        self.detached_log_window = tk.Toplevel(self.root)
        self.detached_log_window.title("IoT Simulator - Debug Logs")
        self.detached_log_window.geometry("1000x600")
        
        # Create main frame
        main_frame = ttk.Frame(self.detached_log_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(button_frame, text="Clear Logs", command=self._clear_log).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save Logs", command=self._save_logs).grid(row=0, column=1, padx=5)
        
        # Log output
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.detached_log_window.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            state=tk.DISABLED,
            font=('Courier', 10)
        )
        self.detached_log_window.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Copy existing logs to detached window
        current_logs = self.log_text.get(1.0, tk.END)
        self.detached_log_window.log_text.config(state=tk.NORMAL)
        self.detached_log_window.log_text.insert(tk.END, current_logs)
        self.detached_log_window.log_text.see(tk.END)
        self.detached_log_window.log_text.config(state=tk.DISABLED)
        
        # Configure grid weights for resizing
        self.detached_log_window.columnconfigure(0, weight=1)
        self.detached_log_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Handle window close
        def on_close():
            self.detached_log_window.destroy()
            self.detached_log_window = None
        
        self.detached_log_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def _save_logs(self):
        """Save logs to a file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    logs = self.log_text.get(1.0, tk.END)
                    f.write(logs)
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def _launch_subscriber(self):
        """Launch MQTT Subscriber window"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "-m", "lib.subscriber_gui"])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch MQTT Subscriber: {e}")
