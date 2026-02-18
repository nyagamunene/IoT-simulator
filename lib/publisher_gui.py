"""
IoT Device Simulator - Enhanced GUI Module
Contains the graphical user interface with matplotlib charts and animations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import queue
from typing import Dict, Any
import re
from collections import deque
import json
import os
from pathlib import Path

# Matplotlib for charts
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Import sensor generators
from lib.sensors import (
    LocationGenerator, TemperatureGenerator, PressureGenerator,
    HumidityGenerator, AccelerometerGenerator, CO2Generator,
    FlowGenerator, SoilMoistureGenerator, SoilPHGenerator,
    LightIntensityGenerator, RainGenerator, WindSpeedGenerator
)


class StatusIndicator(tk.Canvas):
    """Animated LED-style status indicator"""
    
    def __init__(self, parent, size=20):
        super().__init__(parent, width=size, height=size, highlightthickness=0, bg='#2b2b2b')
        self.size = size
        self.led = self.create_oval(2, 2, size-2, size-2, fill='gray', outline='')
        self.status = 'off'
        self.animation_id = None
        self.pulse_alpha = 0
        self.pulse_direction = 1
        
    def set_status(self, status):
        """Set status: off, connecting, connected, error"""
        self.status = status
        if self.animation_id:
            self.after_cancel(self.animation_id)
            self.animation_id = None
            
        if status == 'off':
            self.itemconfig(self.led, fill='#4a4a4a')
        elif status == 'connecting':
            self._animate_pulse()
        elif status == 'connected':
            self.itemconfig(self.led, fill='#00ff00')
        elif status == 'error':
            self.itemconfig(self.led, fill='#ff0000')
    
    def _animate_pulse(self):
        """Animate pulsing effect for connecting status"""
        if self.status != 'connecting':
            return
        
        self.pulse_alpha += self.pulse_direction * 0.1
        if self.pulse_alpha >= 1.0:
            self.pulse_alpha = 1.0
            self.pulse_direction = -1
        elif self.pulse_alpha <= 0.3:
            self.pulse_alpha = 0.3
            self.pulse_direction = 1
        
        # Calculate color based on pulse alpha
        brightness = int(255 * self.pulse_alpha)
        color = f'#{brightness:02x}{brightness:02x}00'
        self.itemconfig(self.led, fill=color)
        
        self.animation_id = self.after(50, self._animate_pulse)


class SensorDataChart(ttk.Frame):
    """Real-time sensor data chart using matplotlib"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        if not MATPLOTLIB_AVAILABLE:
            ttk.Label(self, text="Matplotlib not available. Install with: pip install matplotlib",
                     foreground='orange').pack(pady=20)
            return
        
        # Create figure
        self.fig = Figure(figsize=(8, 4), dpi=80, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111, facecolor='#1e1e1e')
        self.ax.set_xlabel('Time (samples)', color='white')
        self.ax.set_ylabel('Value', color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.2)
        
        # Data storage
        self.max_points = 100
        self.time_data = deque(maxlen=self.max_points)
        self.sensor_data = {}
        self.colors = ['#00ff00', '#00ffff', '#ff00ff', '#ffff00', '#ff8800']
        self.lines = {}
        self.time_counter = 0
        
        # Embed figure
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def add_data_point(self, sensor_name, value):
        """Add a new data point for a sensor"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        # Initialize sensor if new
        if sensor_name not in self.sensor_data:
            self.sensor_data[sensor_name] = deque(maxlen=self.max_points)
            color = self.colors[len(self.sensor_data) % len(self.colors)]
            line, = self.ax.plot([], [], label=sensor_name, color=color, linewidth=2)
            self.lines[sensor_name] = line
            self.ax.legend(loc='upper left', framealpha=0.7)
        
        # Add data
        self.sensor_data[sensor_name].append(value)
        
        # Update time data if needed
        if len(self.time_data) < len(self.sensor_data[sensor_name]):
            self.time_data.append(self.time_counter)
            self.time_counter += 1
        
        # Update plot
        self._update_plot()
    
    def _update_plot(self):
        """Redraw the plot with current data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        for sensor_name, data in self.sensor_data.items():
            if sensor_name in self.lines:
                time_slice = list(self.time_data)[-len(data):]
                self.lines[sensor_name].set_data(time_slice, list(data))
        
        # Auto-scale
        self.ax.relim()
        self.ax.autoscale_view()
        
        self.canvas.draw_idle()
    
    def clear(self):
        """Clear all data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.sensor_data.clear()
        self.lines.clear()
        self.time_data.clear()
        self.time_counter = 0
        self.ax.clear()
        self.ax.set_xlabel('Time (samples)', color='white')
        self.ax.set_ylabel('Value', color='white')
        self.ax.tick_params(colors='white')
        self.ax.grid(True, alpha=0.2)
        self.canvas.draw()


class SimulatorGUI:
    """GUI for IoT Device Simulator"""
    
    CONFIG_FILE = Path.home() / ".iot_simulator_config.json"
    
    def __init__(self, root, simulator_class):
        self.root = root
        self.root.title("IoT Device Simulator - Publisher")
        self.root.geometry("1200x800")
        
        self.simulator_class = simulator_class
        self.simulator = None
        self.log_update_job = None
        self.message_count = 0
        
        self._create_menu()
        self._create_widgets()
        self._load_config()
        self._setup_auto_save()
        
        # Save config on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="MQTT Subscriber...", command=self._launch_subscriber)
        tools_menu.add_separator()
        
        # Theme submenu
        theme_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Theme", menu=theme_menu)
        themes = ['darkly', 'solar', 'superhero', 'cyborg', 'vapor', 'cosmo', 'flatly', 'journal', 'litera', 'minty']
        for theme in themes:
            theme_menu.add_command(label=theme.capitalize(), command=lambda t=theme: self._change_theme(t))
        
        tools_menu.add_separator()
        tools_menu.add_command(label="Exit", command=self.root.quit)
    
    def _create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        config_tab = ttk.Frame(self.notebook)
        dashboard_tab = ttk.Frame(self.notebook)
        logs_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(config_tab, text="⚙️  Configuration")
        self.notebook.add(dashboard_tab, text="📊 Dashboard")
        self.notebook.add(logs_tab, text="📝 Logs")
        
        # Populate tabs
        self._create_config_tab(config_tab)
        self._create_dashboard_tab(dashboard_tab)
        self._create_logs_tab(logs_tab)
    
    def _create_config_tab(self, parent):
        """Create configuration tab"""
        # Main container
        main_frame = ttk.Frame(parent, padding="10")
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
            ("📍 Location (GPS)", "location"),
            ("🌡️  Temperature", "temperature"),
            ("💨 Pressure", "pressure"),
            ("💧 Humidity", "humidity"),
            ("📊 Accelerometer", "accelerometer"),
            ("🌫️  CO2 (PPM)", "co2"),
            ("🚰 Flow Rate", "flow"),
            ("🌱 Soil Moisture", "soil_moisture"),
            ("🧪 Soil pH", "soil_ph"),
            ("💡 Light Intensity", "light"),
            ("🌧️  Rain", "rain"),
            ("💨 Wind Speed", "wind")
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
        
        self.start_btn = ttk.Button(button_frame, text="▶  Start Simulation", command=self._start_simulation)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="⏹  Stop Simulation", command=self._stop_simulation, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Status: Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Configure grid weights
        parent.columnconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def _create_dashboard_tab(self, parent):
        """Create dashboard tab with status and charts"""
        dashboard_frame = ttk.Frame(parent, padding="10")
        dashboard_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status card
        status_card = ttk.LabelFrame(dashboard_frame, text="Connection Status", padding="10")
        status_card.pack(fill=tk.X, pady=5)
        
        status_inner = ttk.Frame(status_card)
        status_inner.pack(fill=tk.X)
        
        ttk.Label(status_inner, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_led = StatusIndicator(status_inner)
        self.status_led.pack(side=tk.LEFT, padx=5)
        self.status_led.set_status('off')
        
        self.connection_label = tk.StringVar(value="Disconnected")
        ttk.Label(status_inner, textvariable=self.connection_label, font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(status_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(status_inner, text="Messages:").pack(side=tk.LEFT, padx=5)
        self.msg_count_var = tk.StringVar(value="0")
        ttk.Label(status_inner, textvariable=self.msg_count_var, font=('TkDefaultFont', 12, 'bold'), foreground='green').pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(status_inner, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(status_inner, text="Protocol:").pack(side=tk.LEFT, padx=5)
        self.proto_display_var = tk.StringVar(value="None")
        ttk.Label(status_inner, textvariable=self.proto_display_var, font=('TkDefaultFont', 10, 'bold'), foreground='cyan').pack(side=tk.LEFT, padx=5)
        
        # Chart area
        chart_card = ttk.LabelFrame(dashboard_frame, text="Real-Time Sensor Data", padding="10")
        chart_card.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.sensor_chart = SensorDataChart(chart_card)
        self.sensor_chart.pack(fill=tk.BOTH, expand=True)
        
        # Chart controls
        chart_controls = ttk.Frame(chart_card)
        chart_controls.pack(fill=tk.X, pady=5)
        ttk.Button(chart_controls, text="Clear Chart", command=self._clear_chart).pack(side=tk.LEFT, padx=5)
    
    def _create_logs_tab(self, parent):
        """Create logs tab"""
        log_frame = ttk.Frame(parent, padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log toolbar
        toolbar = ttk.Frame(log_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Detach Window", command=self._detach_logs).pack(side=tk.LEFT, padx=5)
        
        # Log Output
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, width=120, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Detachable log window reference
        self.detached_log_window = None
        
        # Configure grid weights
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
    
    def _create_protocol_settings(self):
        # Clear existing widgets
        for widget in self.protocol_settings_frame.winfo_children():
            widget.destroy()
        
        protocol = self.protocol_var.get()
        
        # Auto-save callback for protocol-specific variables
        def save_callback(*args):
            if hasattr(self, '_save_job'):
                self.root.after_cancel(self._save_job)
            self._save_job = self.root.after(1000, self._save_config)
        
        if protocol == "MQTT":
            ttk.Label(self.protocol_settings_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.mqtt_broker_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.mqtt_broker_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_broker_var, width=20).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.mqtt_port_var = tk.StringVar(value="8883")
            self.mqtt_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_port_var, width=20).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.mqtt_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            self.mqtt_topic_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.mqtt_topic_var, width=20).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "HTTP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.http_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.http_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.http_port_var = tk.StringVar(value="8443")
            self.http_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.http_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            self.http_topic_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Method:").grid(row=3, column=0, sticky=tk.W, pady=2)
            self.http_method_var = tk.StringVar(value="POST")
            self.http_method_var.trace_add('write', save_callback)
            ttk.Combobox(self.protocol_settings_frame, textvariable=self.http_method_var, 
                        values=["POST", "PUT"], state="readonly", width=27).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "WebSocket":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.ws_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.ws_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.ws_port_var = tk.StringVar(value="8443")
            self.ws_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.ws_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            self.ws_topic_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        elif protocol == "CoAP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.coap_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.coap_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.coap_port_var = tk.StringVar(value="5683")
            self.coap_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
            
            ttk.Label(self.protocol_settings_frame, text="Topic/Path:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.coap_topic_var = tk.StringVar(value="m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic")
            self.coap_topic_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_topic_var, width=30).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
    
    def _on_protocol_change(self, event=None):
        self._create_protocol_settings()
        self._save_config()
    
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
        
        # Save config when TLS mode changes
        self._save_config()
    
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
            
            # Update dashboard
            self.status_led.set_status('connecting')
            self.connection_label.set("Connecting...")
            self.proto_display_var.set(f"{protocol} / {self.format_var.get()}")
            
            # Set to connected after a brief delay
            self.root.after(1000, lambda: self.status_led.set_status('connected'))
            self.root.after(1000, lambda: self.connection_label.set("Connected"))
            
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
        
        # Update dashboard
        self.status_led.set_status('off')
        self.connection_label.set("Disconnected")
        
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
        
        # Update message counter if message was sent
        if "Sent:" in message:
            self.message_count += 1
            self.msg_count_var.set(str(self.message_count))
            
            # Extract sensor data for charting
            self._extract_and_chart_data(message)
        
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
    
    def _clear_chart(self):
        """Clear the sensor data chart"""
        if hasattr(self, 'sensor_chart'):
            self.sensor_chart.clear()
    
    def _change_theme(self, theme_name):
        """Change the ttkbootstrap theme"""
        try:
            import ttkbootstrap as ttk_bootstrap
            style = ttk_bootstrap.Style.get_instance()
            if style:
                style.theme_use(theme_name)
                self._log(f"Theme changed to: {theme_name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change theme: {e}")
    
    def _extract_and_chart_data(self, message):
        """Extract sensor data from log messages and add to chart"""
        if not MATPLOTLIB_AVAILABLE or not hasattr(self, 'sensor_chart'):
            return
        
        try:
            import json
            
            # Try to find JSON in the message (after "Sent: ")
            if 'Sent: ' in message:
                # Extract everything after "Sent: "
                json_start = message.find('Sent: ') + 6
                json_str = message[json_start:].strip()
                
                try:
                    data = json.loads(json_str)
                    
                    # Handle SenML format (array of objects)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'n' in item and 'v' in item:
                                sensor_name = item['n']
                                value = item['v']
                                if isinstance(value, (int, float)):
                                    self.sensor_chart.add_data_point(sensor_name, value)
                    
                    # Handle regular JSON format (object with sensor names as keys)
                    elif isinstance(data, dict):
                        for sensor_name, sensor_data in data.items():
                            if isinstance(sensor_data, dict) and 'value' in sensor_data:
                                value = sensor_data['value']
                                if isinstance(value, (int, float)):
                                    self.sensor_chart.add_data_point(sensor_name, value)
                            elif isinstance(sensor_data, (int, float)):
                                # Direct value
                                self.sensor_chart.add_data_point(sensor_name, sensor_data)
                                
                except json.JSONDecodeError:
                    pass
        except Exception:
            # Silently ignore parsing errors
            pass
    
    def _setup_auto_save(self):
        """Setup auto-save traces on important variables"""
        def save_callback(*args):
            # Use after_idle to debounce multiple rapid changes
            if hasattr(self, '_save_job'):
                self.root.after_cancel(self._save_job)
            self._save_job = self.root.after(1000, self._save_config)  # Save after 1 second of no changes
        
        # Add traces to important variables
        self.device_id_var.trace_add('write', save_callback)
        self.interval_var.trace_add('write', save_callback)
        self.username_var.trace_add('write', save_callback)
        self.password_var.trace_add('write', save_callback)
        self.protocol_var.trace_add('write', save_callback)
        self.format_var.trace_add('write', save_callback)
        self.tls_mode_var.trace_add('write', save_callback)
        self.ca_cert_var.trace_add('write', save_callback)
        self.client_cert_var.trace_add('write', save_callback)
        self.client_key_var.trace_add('write', save_callback)
        
        # Add traces to sensor checkboxes
        for var in self.sensor_vars.values():
            var.trace_add('write', save_callback)
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config = {
                'device_id': self.device_id_var.get(),
                'interval': self.interval_var.get(),
                'username': self.username_var.get(),
                'password': self.password_var.get(),
                'protocol': self.protocol_var.get(),
                'format': self.format_var.get(),
                'tls_mode': self.tls_mode_var.get(),
                'ca_cert': self.ca_cert_var.get(),
                'client_cert': self.client_cert_var.get(),
                'client_key': self.client_key_var.get(),
                'sensors': {key: var.get() for key, var in self.sensor_vars.items()}
            }
            
            # Protocol-specific settings
            protocol = self.protocol_var.get()
            if protocol == "MQTT" and hasattr(self, 'mqtt_broker_var'):
                config['mqtt'] = {
                    'broker': self.mqtt_broker_var.get(),
                    'port': self.mqtt_port_var.get(),
                    'topic': self.mqtt_topic_var.get()
                }
            elif protocol == "HTTP" and hasattr(self, 'http_host_var'):
                config['http'] = {
                    'host': self.http_host_var.get(),
                    'port': self.http_port_var.get(),
                    'topic': self.http_topic_var.get(),
                    'method': self.http_method_var.get()
                }
            elif protocol == "WebSocket" and hasattr(self, 'ws_host_var'):
                config['websocket'] = {
                    'host': self.ws_host_var.get(),
                    'port': self.ws_port_var.get(),
                    'topic': self.ws_topic_var.get()
                }
            elif protocol == "CoAP" and hasattr(self, 'coap_host_var'):
                config['coap'] = {
                    'host': self.coap_host_var.get(),
                    'port': self.coap_port_var.get(),
                    'topic': self.coap_topic_var.get()
                }
            
            # Save to file
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
        except Exception as e:
            # Silently fail - don't interrupt user workflow
            print(f"Warning: Could not save config: {e}")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if not self.CONFIG_FILE.exists():
                return
            
            with open(self.CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            # Restore basic settings
            if 'device_id' in config:
                self.device_id_var.set(config['device_id'])
            if 'interval' in config:
                self.interval_var.set(config['interval'])
            if 'username' in config:
                self.username_var.set(config['username'])
            if 'password' in config:
                self.password_var.set(config['password'])
            if 'protocol' in config:
                self.protocol_var.set(config['protocol'])
            if 'format' in config:
                self.format_var.set(config['format'])
            if 'tls_mode' in config:
                self.tls_mode_var.set(config['tls_mode'])
                self._on_tls_mode_change()
            if 'ca_cert' in config:
                self.ca_cert_var.set(config['ca_cert'])
            if 'client_cert' in config:
                self.client_cert_var.set(config['client_cert'])
            if 'client_key' in config:
                self.client_key_var.set(config['client_key'])
            
            # Restore sensor selections
            if 'sensors' in config:
                for key, value in config['sensors'].items():
                    if key in self.sensor_vars:
                        self.sensor_vars[key].set(value)
            
            # Refresh protocol settings UI BEFORE restoring values
            protocol = config.get('protocol', 'MQTT')
            self._create_protocol_settings()
            
            # Restore protocol-specific settings AFTER creating the widgets
            if protocol == "MQTT" and 'mqtt' in config:
                if hasattr(self, 'mqtt_broker_var'):
                    self.mqtt_broker_var.set(config['mqtt'].get('broker', ''))
                if hasattr(self, 'mqtt_port_var'):
                    self.mqtt_port_var.set(config['mqtt'].get('port', ''))
                if hasattr(self, 'mqtt_topic_var'):
                    self.mqtt_topic_var.set(config['mqtt'].get('topic', ''))
            elif protocol == "HTTP" and 'http' in config:
                if hasattr(self, 'http_host_var'):
                    self.http_host_var.set(config['http'].get('host', ''))
                if hasattr(self, 'http_port_var'):
                    self.http_port_var.set(config['http'].get('port', ''))
                if hasattr(self, 'http_topic_var'):
                    self.http_topic_var.set(config['http'].get('topic', ''))
                if hasattr(self, 'http_method_var'):
                    self.http_method_var.set(config['http'].get('method', ''))
            elif protocol == "WebSocket" and 'websocket' in config:
                if hasattr(self, 'ws_host_var'):
                    self.ws_host_var.set(config['websocket'].get('host', ''))
                if hasattr(self, 'ws_port_var'):
                    self.ws_port_var.set(config['websocket'].get('port', ''))
                if hasattr(self, 'ws_topic_var'):
                    self.ws_topic_var.set(config['websocket'].get('topic', ''))
            elif protocol == "CoAP" and 'coap' in config:
                if hasattr(self, 'coap_host_var'):
                    self.coap_host_var.set(config['coap'].get('host', ''))
                if hasattr(self, 'coap_port_var'):
                    self.coap_port_var.set(config['coap'].get('port', ''))
                if hasattr(self, 'coap_topic_var'):
                    self.coap_topic_var.set(config['coap'].get('topic', ''))
            
        except Exception as e:
            # Silently fail - use defaults if config can't be loaded
            print(f"Warning: Could not load config: {e}")
    
    def _on_closing(self):
        """Handle window close event"""
        # Save configuration
        self._save_config()
        
        # Stop simulation if running
        if self.simulator:
            self._stop_simulation()
        
        # Close window
        self.root.destroy()

