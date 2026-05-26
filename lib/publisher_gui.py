"""
IoT Device Simulator - Enhanced GUI Module
Contains the graphical user interface with matplotlib charts and animations
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog, simpledialog
import queue
import subprocess
import sys
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
    HumidityGenerator, AccelerometerGenerator, GyroscopeGenerator, CO2Generator,
    FlowGenerator, SoilMoistureGenerator, SoilPHGenerator,
    LightIntensityGenerator, RainGenerator, WindSpeedGenerator, FuelConsumptionGenerator,
    SpeedGenerator, MotionState,
    WaterMeterGenerator, WaterPHGenerator, WaterTurbidityGenerator,
    WaterTDSGenerator, ChlorineGenerator
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
        self.sensor_visible = {}  # Track which sensors are visible
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
            self.sensor_visible[sensor_name] = True  # Visible by default
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
            
        # Track if we have any visible data
        has_visible_data = False
        visible_x_data = []
        visible_y_data = []
        
        for sensor_name, data in self.sensor_data.items():
            if sensor_name in self.lines:
                time_slice = list(self.time_data)[-len(data):]
                # Only update and show line if sensor is visible
                if self.sensor_visible.get(sensor_name, True):
                    self.lines[sensor_name].set_data(time_slice, list(data))
                    self.lines[sensor_name].set_visible(True)
                    has_visible_data = True
                    # Collect data for axis scaling
                    visible_x_data.extend(time_slice)
                    visible_y_data.extend(list(data))
                else:
                    self.lines[sensor_name].set_visible(False)
        
        # Auto-scale based only on visible data
        if has_visible_data and visible_x_data and visible_y_data:
            # Set limits with a small margin
            x_min, x_max = min(visible_x_data), max(visible_x_data)
            y_min, y_max = min(visible_y_data), max(visible_y_data)
            
            # Add 5% margin
            x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 1
            y_margin = (y_max - y_min) * 0.05 if y_max > y_min else 1
            
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
        self.canvas.draw_idle()
    
    def set_sensor_visibility(self, sensor_name, visible):
        """Show or hide a specific sensor"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        if sensor_name in self.sensor_visible:
            self.sensor_visible[sensor_name] = visible
            self._update_plot()
    
    def get_sensor_names(self):
        """Get list of all sensor names in the chart"""
        return list(self.sensor_data.keys())
    
    def clear(self):
        """Clear all data"""
        if not MATPLOTLIB_AVAILABLE:
            return
            
        self.sensor_data.clear()
        self.sensor_visible.clear()
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

    DEFAULT_CONFIG_FILE = Path.home() / ".iot_simulator_config.json"

    def __init__(self, root, simulator_class):
        self.root = root
        # Main window is implicitly Device 001; spawned windows pass IOT_SIM_TITLE_SUFFIX
        title_suffix = os.environ.get("IOT_SIM_TITLE_SUFFIX", "Device 001").strip()
        self.root.title(f"IoT Device Simulator - Publisher{(' — ' + title_suffix) if title_suffix else ''}")
        self.root.geometry("1200x800")

        # Each window keeps its own config file so multiple devices don't fight over state.
        # IOT_SIM_CONFIG is set on spawned device windows; the original window uses the default.
        custom_cfg = os.environ.get("IOT_SIM_CONFIG", "").strip()
        self.CONFIG_FILE = Path(custom_cfg) if custom_cfg else self.DEFAULT_CONFIG_FILE

        self.simulator_class = simulator_class
        self.simulators = []           # one entry per simulated device
        self.simulator = None          # alias to simulators[0] for legacy code paths
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
        sensor_config_tab = ttk.Frame(self.notebook)
        logs_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(config_tab, text="⚙️  Configuration")
        self.notebook.add(dashboard_tab, text="📊 Dashboard")
        self.notebook.add(sensor_config_tab, text="🔧 Sensor Config")
        self.notebook.add(logs_tab, text="📝 Logs")
        
        # Populate tabs
        self._create_config_tab(config_tab)
        self._create_dashboard_tab(dashboard_tab)
        self._create_sensor_config_tab(sensor_config_tab)
        self._create_logs_tab(logs_tab)
    
    def _create_config_tab(self, parent):
        """Create configuration tab"""
        # Create canvas with scrollbars for scrollable content (vertical and horizontal)
        canvas = tk.Canvas(parent, highlightthickness=0)
        v_scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        h_scrollbar = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack canvas and scrollbars
        canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Enable mousewheel scrolling (vertical and horizontal with Shift)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _on_shift_mousewheel(event):
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Shift-MouseWheel>", _on_shift_mousewheel)
        
        # Main container inside scrollable frame
        main_frame = ttk.Frame(scrollable_frame, padding="10")
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

        # Spawn additional publisher windows — each is a fully independent device
        # with its own credentials, topic, and config file.
        ttk.Button(config_frame, text="➕ Open Device Windows…",
                   command=self._open_device_windows).grid(
            row=1, column=2, columnspan=2, sticky=tk.W, padx=(20, 0), pady=2)

        # Auth credentials live in the "Magistrala Client" section under Protocol Configuration.
        # StringVars are created here so they exist before that section is built.
        self.username_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")
        self.mqtt_client_name_var = tk.StringVar(value="")

        # Unit System Selection
        ttk.Label(config_frame, text="Unit System:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.unit_system_var = tk.StringVar(value="metric")
        unit_frame = ttk.Frame(config_frame)
        unit_frame.grid(row=1, column=1, sticky=tk.W, pady=2)
        ttk.Radiobutton(unit_frame, text="Metric (°C, km/h, L/100km)", variable=self.unit_system_var, 
                       value="metric").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(unit_frame, text="Imperial (°F, mph, MPG)", variable=self.unit_system_var, 
                       value="imperial").pack(side=tk.LEFT)
        
        # Sensor Selection
        sensor_frame = ttk.LabelFrame(main_frame, text="Sensors", padding="10")
        sensor_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N), pady=5, padx=(0, 5))
        
        # Create canvas with scrollbar for scrollable sensors
        sensor_canvas = tk.Canvas(sensor_frame, highlightthickness=0, height=280)
        sensor_scrollbar = ttk.Scrollbar(sensor_frame, orient="vertical", command=sensor_canvas.yview)
        scrollable_sensor_frame = ttk.Frame(sensor_canvas)
        
        scrollable_sensor_frame.bind(
            "<Configure>",
            lambda e: sensor_canvas.configure(scrollregion=sensor_canvas.bbox("all"))
        )
        
        sensor_canvas.create_window((0, 0), window=scrollable_sensor_frame, anchor="nw")
        sensor_canvas.configure(yscrollcommand=sensor_scrollbar.set)
        
        # Pack canvas and scrollbar
        sensor_canvas.pack(side="left", fill="both", expand=True)
        sensor_scrollbar.pack(side="right", fill="y")
        
        # Enable mousewheel scrolling for sensors
        def _on_sensor_mousewheel(event):
            sensor_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        sensor_canvas.bind("<Enter>", lambda e: sensor_canvas.bind_all("<MouseWheel>", _on_sensor_mousewheel))
        sensor_canvas.bind("<Leave>", lambda e: sensor_canvas.unbind_all("<MouseWheel>"))
        
        self.sensor_vars = {}
        sensors = [
            ("📍 Location (GPS)", "location"),
            ("🚗 Speed", "speed"),
            ("🌡️ Temperature", "temperature"),
            ("💨 Pressure", "pressure"),
            ("💧 Humidity", "humidity"),
            ("📊 Accelerometer", "accelerometer"),
            ("🔄 Gyroscope", "gyroscope"),
            ("🌫️ CO2 (PPM)", "co2"),
            ("🚰 Flow Rate", "flow"),
            ("🌱 Soil Moisture", "soil_moisture"),
            ("🧪 Soil pH", "soil_ph"),
            ("💡 Light Intensity", "light"),
            ("🌧️ Rain", "rain"),
            ("💨 Wind Speed", "wind"),
            ("⛽ Fuel Consumption", "fuel"),
            ("💧 Water Meter", "water_meter"),
            ("🧪 Water pH", "water_ph"),
            ("🌊 Water Turbidity", "water_turbidity"),
            ("⚗️ Water TDS / Conductivity", "water_tds"),
            ("🔬 Chlorine Level", "chlorine"),
        ]

        for i, (label, key) in enumerate(sensors):
            var = tk.BooleanVar(value=False)
            self.sensor_vars[key] = var
            ttk.Checkbutton(scrollable_sensor_frame, text=label, variable=var).grid(
                row=i, column=0, sticky=tk.W, pady=2)
        
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

        # Magistrala Client identity (used across MQTT/HTTP/WS/CoAP auth)
        client_frame = ttk.LabelFrame(protocol_frame, text="Magistrala Client", padding="5")
        client_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Label(client_frame, text="Client ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(client_frame, textvariable=self.username_var, width=36).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        ttk.Label(client_frame, text="(mosquitto_pub -u)",
                  font=('TkDefaultFont', 8)).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(client_frame, text="Client Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        secret_row = ttk.Frame(client_frame)
        secret_row.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        self.password_entry = ttk.Entry(secret_row, textvariable=self.password_var,
                                        width=32, show="*")
        self.password_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._secret_visible = False
        self.secret_toggle_btn = ttk.Button(secret_row, text="👁", width=3,
                                            command=self._toggle_secret_visibility)
        self.secret_toggle_btn.pack(side=tk.LEFT, padx=(2, 0))
        ttk.Label(client_frame, text="(mosquitto_pub -P)",
                  font=('TkDefaultFont', 8)).grid(row=1, column=2, sticky=tk.W)

        ttk.Label(client_frame, text="Client Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(client_frame, textvariable=self.mqtt_client_name_var, width=36).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))
        ttk.Label(client_frame, text="(MQTT -I; defaults to Device ID)",
                  font=('TkDefaultFont', 8)).grid(row=2, column=2, sticky=tk.W)

        # Magistrala Routing (composes the publish topic: m/<domain>/c/<channel>/<subtopic>)
        routing_frame = ttk.LabelFrame(protocol_frame, text="Magistrala Routing", padding="5")
        routing_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))

        ttk.Label(routing_frame, text="Domain ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.magistrala_domain_var = tk.StringVar(value="")
        ttk.Entry(routing_frame, textvariable=self.magistrala_domain_var, width=36).grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))

        ttk.Label(routing_frame, text="Channel ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.magistrala_channel_var = tk.StringVar(value="")
        ttk.Entry(routing_frame, textvariable=self.magistrala_channel_var, width=36).grid(
            row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))

        ttk.Label(routing_frame, text="Subtopic:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.magistrala_subtopic_var = tk.StringVar(value="")
        ttk.Entry(routing_frame, textvariable=self.magistrala_subtopic_var, width=36).grid(
            row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(0, 2))

        # Live preview of the composed topic
        self.topic_preview_var = tk.StringVar(value=self._compose_topic())
        ttk.Label(routing_frame, text="Topic:").grid(row=3, column=0, sticky=tk.W, pady=(4, 2))
        ttk.Label(routing_frame, textvariable=self.topic_preview_var,
                  font=('TkDefaultFont', 8), foreground='#0055cc').grid(
            row=3, column=1, sticky=tk.W, pady=(4, 2))

        # Keep the preview in sync with edits
        for var in (self.magistrala_domain_var, self.magistrala_channel_var, self.magistrala_subtopic_var):
            var.trace_add('write', lambda *_: self.topic_preview_var.set(self._compose_topic()))

        # Protocol-specific settings
        self.protocol_settings_frame = ttk.Frame(protocol_frame)
        self.protocol_settings_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
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
        parent.rowconfigure(0, weight=1)
        scrollable_frame.columnconfigure(0, weight=1)
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
        
        # Sensor filter panel
        filter_card = ttk.LabelFrame(dashboard_frame, text="Chart Filters", padding="10")
        filter_card.pack(fill=tk.X, pady=5)
        
        self.sensor_filter_frame = ttk.Frame(filter_card)
        self.sensor_filter_frame.pack(fill=tk.X)
        
        self.sensor_visibility_vars = {}  # Dictionary to store checkbox variables
        
        ttk.Label(self.sensor_filter_frame, text="Select sensors to display:", 
                 font=('TkDefaultFont', 9, 'italic')).pack(side=tk.LEFT, padx=5)
        
        self.filter_checkboxes_frame = ttk.Frame(filter_card)
        self.filter_checkboxes_frame.pack(fill=tk.X, pady=5)
        
        # Chart area
        chart_card = ttk.LabelFrame(dashboard_frame, text="Real-Time Sensor Data", padding="10")
        chart_card.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.sensor_chart = SensorDataChart(chart_card)
        self.sensor_chart.pack(fill=tk.BOTH, expand=True)
        
        # Chart controls
        chart_controls = ttk.Frame(chart_card)
        chart_controls.pack(fill=tk.X, pady=5)
        ttk.Button(chart_controls, text="Clear Chart", command=self._clear_chart).pack(side=tk.LEFT, padx=5)
    
    SENSOR_LEVELS = ("auto", "low", "medium", "high")
    SENSOR_LEVEL_LABELS = ("Auto", "Low", "Med", "High")

    # Generators that accept Auto / Low / Medium / High overrides. Sensors not in
    # this set show a disabled slider with an "Auto only" note.
    LEVEL_CAPABLE_SENSORS = {
        "temperature", "pressure", "humidity", "accelerometer", "co2", "flow",
        "soil_moisture", "soil_ph", "light", "rain", "wind", "speed", "fuel",
        "water_meter", "water_ph", "water_turbidity", "water_tds", "chlorine",
    }

    def _create_sensor_config_tab(self, parent):
        """Create sensor configuration tab"""
        main_frame = ttk.Frame(parent, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Motion Configuration
        motion_frame = ttk.LabelFrame(main_frame, text="Motion Configuration", padding="15")
        motion_frame.pack(fill=tk.X, pady=(0, 10))

        motion_label = ttk.Label(motion_frame, text="Motion Mode:", font=('TkDefaultFont', 10, 'bold'))
        motion_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        description = ttk.Label(motion_frame,
                               text="Select the motion profile for location-based sensors (GPS, Speed, Accelerometer, Fuel):",
                               font=('TkDefaultFont', 9))
        description.grid(row=1, column=0, sticky=tk.W, pady=(0, 15))

        self.motion_mode_var = tk.StringVar(value="low_speed")
        motion_modes = [
            ("🛑 Stationary", "stationary", "No movement - vehicle is parked"),
            ("🚶 Low Speed (0-36 km/h)", "low_speed", "Urban driving, residential areas"),
            ("🚙 Medium Speed (36-108 km/h)", "medium_speed", "City traffic, suburban roads"),
            ("🏎️ High Speed (108-250 km/h)", "high_speed", "Highway, motorway driving")
        ]

        for idx, (label, mode, desc) in enumerate(motion_modes):
            rb = ttk.Radiobutton(motion_frame, text=label, variable=self.motion_mode_var, value=mode)
            rb.grid(row=idx+2, column=0, sticky=tk.W, pady=5, padx=10)
            desc_label = ttk.Label(motion_frame, text=desc, font=('TkDefaultFont', 8), foreground='gray')
            desc_label.grid(row=idx+2, column=1, sticky=tk.W, pady=5, padx=(0, 10))

        # Sensor Level Overrides
        levels_frame = ttk.LabelFrame(main_frame, text="Sensor Levels", padding="15")
        levels_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(levels_frame,
                  text="Override the safe/unsafe cycle. Auto = built-in pattern; Low/Med/High clamp values to that band.",
                  font=('TkDefaultFont', 9)).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))

        # Scrollable container so 20+ sensor rows always fit
        canvas = tk.Canvas(levels_frame, highlightthickness=0, height=360)
        scrollbar = ttk.Scrollbar(levels_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        levels_frame.columnconfigure(0, weight=1)
        levels_frame.rowconfigure(1, weight=1)

        def _on_levels_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_levels_wheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Header row
        ttk.Label(scrollable, text="Sensor", font=('TkDefaultFont', 9, 'bold')).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 20), pady=(0, 6))
        ttk.Label(scrollable, text="Level", font=('TkDefaultFont', 9, 'bold')).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 10), pady=(0, 6))

        self.sensor_level_vars = {}
        self.sensor_level_labels = {}

        sensor_labels = {
            "location": "📍 Location (GPS)",
            "speed": "🚗 Speed",
            "temperature": "🌡️ Temperature",
            "pressure": "💨 Pressure",
            "humidity": "💧 Humidity",
            "accelerometer": "📊 Accelerometer",
            "gyroscope": "🔄 Gyroscope",
            "co2": "🌫️ CO2 (PPM)",
            "flow": "🚰 Flow Rate",
            "soil_moisture": "🌱 Soil Moisture",
            "soil_ph": "🧪 Soil pH",
            "light": "💡 Light Intensity",
            "rain": "🌧️ Rain",
            "wind": "💨 Wind Speed",
            "fuel": "⛽ Fuel Consumption",
            "water_meter": "💧 Water Meter",
            "water_ph": "🧪 Water pH",
            "water_turbidity": "🌊 Water Turbidity",
            "water_tds": "⚗️ Water TDS / Cond.",
            "chlorine": "🔬 Chlorine",
        }

        for row_idx, (key, label) in enumerate(sensor_labels.items(), start=1):
            ttk.Label(scrollable, text=label).grid(
                row=row_idx, column=0, sticky=tk.W, padx=(0, 20), pady=3)

            var = tk.IntVar(value=0)
            self.sensor_level_vars[key] = var

            level_capable = key in self.LEVEL_CAPABLE_SENSORS
            scale_state = tk.NORMAL if level_capable else tk.DISABLED

            def _on_scale_change(value, k=key, v=var):
                # Snap to nearest integer position 0..3
                snapped = max(0, min(3, round(float(value))))
                if v.get() != snapped:
                    v.set(snapped)
                self._update_level_label(k)

            scale = ttk.Scale(scrollable, from_=0, to=3, orient=tk.HORIZONTAL,
                              length=180, variable=var, command=_on_scale_change,
                              state=scale_state)
            scale.grid(row=row_idx, column=1, sticky=tk.W, padx=(0, 10), pady=3)

            current_label = ttk.Label(scrollable,
                                      text="Auto" if level_capable else "Auto only",
                                      font=('TkDefaultFont', 9),
                                      foreground='#0055cc' if level_capable else 'gray',
                                      width=10)
            current_label.grid(row=row_idx, column=2, sticky=tk.W, padx=(0, 10), pady=3)
            self.sensor_level_labels[key] = current_label

            # Tick marks under the slider
            ticks_frame = ttk.Frame(scrollable)
            ticks_frame.grid(row=row_idx, column=3, sticky=tk.W)
            for i, t in enumerate(self.SENSOR_LEVEL_LABELS):
                ttk.Label(ticks_frame, text=t,
                          font=('TkDefaultFont', 7),
                          foreground='gray').grid(row=0, column=i, padx=4)

    def _update_level_label(self, key: str) -> None:
        if key not in self.sensor_level_vars:
            return
        idx = max(0, min(3, self.sensor_level_vars[key].get()))
        if key in self.LEVEL_CAPABLE_SENSORS:
            self.sensor_level_labels[key].configure(text=self.SENSOR_LEVEL_LABELS[idx])

    def _sensor_level_str(self, key: str) -> str:
        """Return 'auto'/'low'/'medium'/'high' for the given sensor key."""
        if key not in self.sensor_level_vars:
            return "auto"
        idx = max(0, min(3, self.sensor_level_vars[key].get()))
        return self.SENSOR_LEVELS[idx]
    
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
    
    def _compose_topic(self) -> str:
        """Build the publish topic from the Magistrala routing fields."""
        domain = self.magistrala_domain_var.get().strip() if hasattr(self, 'magistrala_domain_var') else ''
        channel = self.magistrala_channel_var.get().strip() if hasattr(self, 'magistrala_channel_var') else ''
        subtopic = self.magistrala_subtopic_var.get().strip().lstrip('/') if hasattr(self, 'magistrala_subtopic_var') else ''
        base = f"m/{domain}/c/{channel}"
        return f"{base}/{subtopic}" if subtopic else base

    @staticmethod
    def _parse_legacy_topic(topic: str) -> Dict[str, str]:
        """Parse an old-style 'm/<dom>/c/<chan>/<subtopic>' string into routing fields."""
        parts = (topic or '').split('/')
        if len(parts) >= 4 and parts[0] == 'm' and parts[2] == 'c':
            return {
                'domain': parts[1],
                'channel': parts[3],
                'subtopic': '/'.join(parts[4:]) if len(parts) > 4 else '',
            }
        return {'domain': '', 'channel': '', 'subtopic': ''}

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

        elif protocol == "HTTP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.http_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.http_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.http_port_var = tk.StringVar(value="8443")
            self.http_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.http_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

            ttk.Label(self.protocol_settings_frame, text="Method:").grid(row=2, column=0, sticky=tk.W, pady=2)
            self.http_method_var = tk.StringVar(value="POST")
            self.http_method_var.trace_add('write', save_callback)
            ttk.Combobox(self.protocol_settings_frame, textvariable=self.http_method_var,
                        values=["POST", "PUT"], state="readonly", width=27).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)

        elif protocol == "WebSocket":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.ws_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.ws_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.ws_port_var = tk.StringVar(value="8443")
            self.ws_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.ws_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)

        elif protocol == "CoAP":
            ttk.Label(self.protocol_settings_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, pady=2)
            self.coap_host_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
            self.coap_host_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_host_var, width=30).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)

            ttk.Label(self.protocol_settings_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
            self.coap_port_var = tk.StringVar(value="5683")
            self.coap_port_var.trace_add('write', save_callback)
            ttk.Entry(self.protocol_settings_frame, textvariable=self.coap_port_var, width=30).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
    
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

        # Auto-switch MQTT port to match TLS mode: 1888 plain (Magistrala cloud),
        # 8883 TLS/mTLS. Only swaps when current port is a recognized default for
        # the *other* mode — custom ports are left alone.
        if hasattr(self, 'mqtt_port_var'):
            current = self.mqtt_port_var.get().strip()
            plain_defaults = {"1883", "1888"}
            tls_defaults = {"8883"}
            if tls_mode == "none" and current in tls_defaults:
                self.mqtt_port_var.set("1888")
            elif tls_mode in ("tls", "mtls") and current in plain_defaults:
                self.mqtt_port_var.set("8883")

        # Save config when TLS mode changes
        self._save_config()
    
    def _toggle_secret_visibility(self):
        """Reveal / re-mask the Client Secret field."""
        self._secret_visible = not self._secret_visible
        self.password_entry.configure(show="" if self._secret_visible else "*")
        self.secret_toggle_btn.configure(text="🙈" if self._secret_visible else "👁")

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
    
    def _build_simulator(self, device_id: str, motion_mode: str):
        """Instantiate one simulator + its generators + per-sensor levels."""
        sim = self.simulator_class(device_id)
        motion_state = MotionState(mode=motion_mode)

        ctors = {
            'location':        lambda: LocationGenerator(device_id, motion_state=motion_state),
            'speed':           lambda: SpeedGenerator(device_id, motion_state=motion_state),
            'temperature':     lambda: TemperatureGenerator(device_id),
            'pressure':        lambda: PressureGenerator(device_id),
            'humidity':        lambda: HumidityGenerator(device_id),
            'accelerometer':   lambda: AccelerometerGenerator(device_id, motion_state=motion_state),
            'gyroscope':       lambda: GyroscopeGenerator(device_id),
            'co2':             lambda: CO2Generator(device_id),
            'flow':            lambda: FlowGenerator(device_id),
            'soil_moisture':   lambda: SoilMoistureGenerator(device_id),
            'soil_ph':         lambda: SoilPHGenerator(device_id),
            'light':           lambda: LightIntensityGenerator(device_id),
            'rain':            lambda: RainGenerator(device_id),
            'wind':            lambda: WindSpeedGenerator(device_id),
            'fuel':            lambda: FuelConsumptionGenerator(device_id, motion_state=motion_state),
            'water_meter':     lambda: WaterMeterGenerator(device_id),
            'water_ph':        lambda: WaterPHGenerator(device_id),
            'water_turbidity': lambda: WaterTurbidityGenerator(device_id),
            'water_tds':       lambda: WaterTDSGenerator(device_id),
            'chlorine':        lambda: ChlorineGenerator(device_id),
        }
        for key, make in ctors.items():
            if self.sensor_vars[key].get():
                sim.add_generator(key, make())

        # Apply per-sensor level overrides from the Sensor Config tab.
        if hasattr(self, 'sensor_level_vars'):
            for name, gen in sim.generators.items():
                if hasattr(gen, 'set_level'):
                    gen.set_level(self._sensor_level_str(name))

        return sim

    def _open_device_windows(self):
        """Ask how many additional publisher windows to spawn, then launch them.

        Each spawned window is an independent process with its own config file —
        so users can plug in different Magistrala client credentials per device.
        """
        count = simpledialog.askinteger(
            "Open Device Windows",
            "How many additional device windows do you want to open?\n"
            "Each opens an independent publisher with its own config.",
            parent=self.root, minvalue=1, maxvalue=10, initialvalue=1,
        )
        if not count:
            return

        # Reuse main.py's entry point in independent processes
        main_py = Path(__file__).resolve().parent.parent / "main.py"
        cfg_dir = self.DEFAULT_CONFIG_FILE.parent
        spawned = 0
        claimed_slots = set()  # avoid re-picking the same slot before subprocess writes its file
        for i in range(count):
            # Main window is Device 001 — spawned windows start at 002.
            # Skip slots already on disk and ones we just handed out in this call.
            for n in range(2, 100):
                candidate = cfg_dir / f".iot_simulator_config-{n:03d}.json"
                if n not in claimed_slots and not candidate.exists():
                    break
            else:
                self._log("Couldn't find a free device config slot (2-99 all in use)")
                break
            claimed_slots.add(n)

            env = os.environ.copy()
            env["IOT_SIM_CONFIG"] = str(candidate)
            env["IOT_SIM_TITLE_SUFFIX"] = f"Device {n:03d}"
            try:
                subprocess.Popen([sys.executable, str(main_py)], env=env,
                                 cwd=str(main_py.parent))
                spawned += 1
            except Exception as e:
                self._log(f"Failed to spawn device window: {e}")
                break

        if spawned:
            self._log(f"Opened {spawned} additional device window(s)")

    def _start_simulation(self):
        try:
            if not any(var.get() for var in self.sensor_vars.values()):
                messagebox.showerror("Error", "Please select at least one sensor")
                return

            device_id = self.device_id_var.get().strip() or "device"
            motion_mode = self.motion_mode_var.get()
            protocol = self.protocol_var.get()
            config = self._get_protocol_config()
            fmt = self.format_var.get()
            unit_system = self.unit_system_var.get()
            interval = float(self.interval_var.get())

            self._log("="*60)
            self._log(f"Starting simulation — device: {device_id}")
            self._log(f"Protocol: {protocol}, Format: {fmt}, Interval: {interval}s")
            self._log(f"TLS Mode: {config.get('tls_mode', 'none')}")
            if protocol == "MQTT":
                self._log(f"MQTT Broker: {config.get('broker')}:{config.get('port')}")
                self._log(f"MQTT Topic: {config.get('topic')}")
                self._log(f"Client ID: {config.get('client_id')}")
                self._log(f"Username: {config.get('username', 'None')}")
            elif protocol == "HTTP":
                self._log(f"HTTP URL: {config.get('url')}")
                self._log(f"Method: {config.get('method')}")
            elif protocol == "WebSocket":
                self._log(f"WebSocket URL: {config.get('url')}")
            elif protocol == "CoAP":
                self._log(f"CoAP URL: {config.get('url')}")
            self._log("-"*60)
            self._log("Attempting to connect...")

            # Stop any leftover simulators from a previous run before re-arming.
            for prev in self.simulators:
                try:
                    prev.stop()
                except Exception:
                    pass
            self.simulators = []

            sim = self._build_simulator(device_id, motion_mode)
            sim.set_protocol(protocol, config)
            sim.set_format(fmt)
            sim.set_unit_system(unit_system)
            sim.interval = interval
            sim.start()

            self.simulators.append(sim)
            self.simulator = sim

            # Update UI
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_var.set(f"Status: Running ({protocol} - {fmt})")

            # Update dashboard
            self.status_led.set_status('connecting')
            self.connection_label.set("Connecting...")
            self.proto_display_var.set(f"{protocol} / {fmt}")

            self.root.after(1000, lambda: self.status_led.set_status('connected'))
            self.root.after(1000, lambda: self.connection_label.set("Connected"))

            self._log("✓ Simulation started successfully")
            self._log("="*60)
            self._update_log()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start simulation: {e}")
            self._log(f"Error: {e}")
    
    def _stop_simulation(self):
        for sim in self.simulators:
            try:
                sim.stop()
            except Exception as e:
                self._log(f"Error stopping device {sim.device_id}: {e}")
        self.simulators = []
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
        
        # Topic comes from the shared Magistrala routing fields
        topic = self._compose_topic()

        if protocol == "MQTT":
            client_name = self.mqtt_client_name_var.get().strip() if hasattr(self, 'mqtt_client_name_var') else ''
            config = {
                'broker': self.mqtt_broker_var.get(),
                'port': int(self.mqtt_port_var.get()),
                'topic': topic,
                'client_id': client_name or self.device_id_var.get(),
            }

            # Add username and password for MQTT
            if username:
                config['username'] = username
            if password:
                config['password'] = password
        elif protocol == "HTTP":
            host = self.http_host_var.get()
            port = self.http_port_var.get()

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
            host = self.ws_host_var.get()
            port = self.ws_port_var.get()

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
            host = self.coap_host_var.get()
            port = self.coap_port_var.get()
            
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
            # Clear filter checkboxes
            for widget in self.filter_checkboxes_frame.winfo_children():
                widget.destroy()
            self.sensor_visibility_vars.clear()
    
    def _update_sensor_filters(self):
        """Update the sensor filter checkboxes based on available sensors"""
        if not hasattr(self, 'sensor_chart'):
            return
        
        current_sensors = set(self.sensor_chart.get_sensor_names())
        existing_sensors = set(self.sensor_visibility_vars.keys())
        
        # Add checkboxes for new sensors
        new_sensors = current_sensors - existing_sensors
        for sensor_name in sorted(new_sensors):
            var = tk.BooleanVar(value=True)
            self.sensor_visibility_vars[sensor_name] = var
            
            cb = ttk.Checkbutton(
                self.filter_checkboxes_frame,
                text=sensor_name,
                variable=var,
                command=lambda s=sensor_name: self._toggle_sensor_visibility(s)
            )
            cb.pack(side=tk.LEFT, padx=5)
    
    def _toggle_sensor_visibility(self, sensor_name):
        """Toggle visibility of a sensor in the chart"""
        if sensor_name in self.sensor_visibility_vars:
            visible = self.sensor_visibility_vars[sensor_name].get()
            self.sensor_chart.set_sensor_visibility(sensor_name, visible)
    
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
                    
                    data_added = False  # Track if any data was added
                    
                    # Handle SenML format (array of objects)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'n' in item and 'v' in item:
                                sensor_name = item['n']
                                value = item['v']
                                if isinstance(value, (int, float)):
                                    self.sensor_chart.add_data_point(sensor_name, value)
                                    data_added = True
                    
                    # Handle regular JSON format (object with sensor names as keys)
                    elif isinstance(data, dict):
                        for sensor_name, sensor_data in data.items():
                            if isinstance(sensor_data, dict) and 'value' in sensor_data:
                                value = sensor_data['value']
                                if isinstance(value, (int, float)):
                                    self.sensor_chart.add_data_point(sensor_name, value)
                                    data_added = True
                            elif isinstance(sensor_data, (int, float)):
                                # Direct value
                                self.sensor_chart.add_data_point(sensor_name, sensor_data)
                                data_added = True
                    
                    # Update filter checkboxes if new data was added
                    if data_added:
                        self._update_sensor_filters()
                                
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
        self.motion_mode_var.trace_add('write', save_callback)
        self.unit_system_var.trace_add('write', save_callback)
        self.magistrala_domain_var.trace_add('write', save_callback)
        self.magistrala_channel_var.trace_add('write', save_callback)
        self.magistrala_subtopic_var.trace_add('write', save_callback)

        # Add traces to sensor checkboxes
        for var in self.sensor_vars.values():
            var.trace_add('write', save_callback)

        # Auto-save when a sensor level slider moves
        if hasattr(self, 'sensor_level_vars'):
            for var in self.sensor_level_vars.values():
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
                'motion_mode': self.motion_mode_var.get(),
                'unit_system': self.unit_system_var.get(),
                'sensors': {key: var.get() for key, var in self.sensor_vars.items()},
                'sensor_levels': {key: self._sensor_level_str(key)
                                  for key in (self.sensor_level_vars or {})},
                'magistrala': {
                    'domain': self.magistrala_domain_var.get() if hasattr(self, 'magistrala_domain_var') else '',
                    'channel': self.magistrala_channel_var.get() if hasattr(self, 'magistrala_channel_var') else '',
                    'subtopic': self.magistrala_subtopic_var.get() if hasattr(self, 'magistrala_subtopic_var') else '',
                },
            }

            # Protocol-specific settings (topic now lives under config['magistrala'])
            protocol = self.protocol_var.get()
            if protocol == "MQTT" and hasattr(self, 'mqtt_broker_var'):
                config['mqtt'] = {
                    'broker': self.mqtt_broker_var.get(),
                    'port': self.mqtt_port_var.get(),
                    'client_name': self.mqtt_client_name_var.get() if hasattr(self, 'mqtt_client_name_var') else '',
                }
            elif protocol == "HTTP" and hasattr(self, 'http_host_var'):
                config['http'] = {
                    'host': self.http_host_var.get(),
                    'port': self.http_port_var.get(),
                    'method': self.http_method_var.get()
                }
            elif protocol == "WebSocket" and hasattr(self, 'ws_host_var'):
                config['websocket'] = {
                    'host': self.ws_host_var.get(),
                    'port': self.ws_port_var.get(),
                }
            elif protocol == "CoAP" and hasattr(self, 'coap_host_var'):
                config['coap'] = {
                    'host': self.coap_host_var.get(),
                    'port': self.coap_port_var.get(),
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
            if 'motion_mode' in config:
                self.motion_mode_var.set(config['motion_mode'])
            if 'unit_system' in config:
                self.unit_system_var.set(config['unit_system'])
            
            # Restore sensor selections
            if 'sensors' in config:
                for key, value in config['sensors'].items():
                    if key in self.sensor_vars:
                        self.sensor_vars[key].set(value)

            # Restore sensor level overrides (Auto / Low / Medium / High)
            if 'sensor_levels' in config and hasattr(self, 'sensor_level_vars'):
                for key, level in config['sensor_levels'].items():
                    if key in self.sensor_level_vars and level in self.SENSOR_LEVELS:
                        self.sensor_level_vars[key].set(self.SENSOR_LEVELS.index(level))
                        self._update_level_label(key)
            
            # Refresh protocol settings UI BEFORE restoring values
            protocol = config.get('protocol', 'MQTT')
            self._create_protocol_settings()

            # Restore Magistrala routing — prefer the new block, fall back to
            # parsing a legacy per-protocol "topic" string for older saved configs.
            routing = config.get('magistrala')
            if routing is None:
                legacy_topic = ''
                for key in ('mqtt', 'http', 'websocket', 'coap'):
                    legacy_topic = config.get(key, {}).get('topic', '') if isinstance(config.get(key), dict) else ''
                    if legacy_topic:
                        break
                routing = self._parse_legacy_topic(legacy_topic)
            if hasattr(self, 'magistrala_domain_var'):
                self.magistrala_domain_var.set(routing.get('domain', ''))
            if hasattr(self, 'magistrala_channel_var'):
                self.magistrala_channel_var.set(routing.get('channel', ''))
            if hasattr(self, 'magistrala_subtopic_var'):
                self.magistrala_subtopic_var.set(routing.get('subtopic', ''))

            # Restore protocol-specific settings AFTER creating the widgets
            if protocol == "MQTT" and 'mqtt' in config:
                if hasattr(self, 'mqtt_broker_var'):
                    self.mqtt_broker_var.set(config['mqtt'].get('broker', ''))
                if hasattr(self, 'mqtt_port_var'):
                    self.mqtt_port_var.set(config['mqtt'].get('port', ''))
                if hasattr(self, 'mqtt_client_name_var'):
                    self.mqtt_client_name_var.set(config['mqtt'].get('client_name', ''))
            elif protocol == "HTTP" and 'http' in config:
                if hasattr(self, 'http_host_var'):
                    self.http_host_var.set(config['http'].get('host', ''))
                if hasattr(self, 'http_port_var'):
                    self.http_port_var.set(config['http'].get('port', ''))
                if hasattr(self, 'http_method_var'):
                    self.http_method_var.set(config['http'].get('method', ''))
            elif protocol == "WebSocket" and 'websocket' in config:
                if hasattr(self, 'ws_host_var'):
                    self.ws_host_var.set(config['websocket'].get('host', ''))
                if hasattr(self, 'ws_port_var'):
                    self.ws_port_var.set(config['websocket'].get('port', ''))
            elif protocol == "CoAP" and 'coap' in config:
                if hasattr(self, 'coap_host_var'):
                    self.coap_host_var.set(config['coap'].get('host', ''))
                if hasattr(self, 'coap_port_var'):
                    self.coap_port_var.set(config['coap'].get('port', ''))
            
        except Exception as e:
            # Silently fail - use defaults if config can't be loaded
            print(f"Warning: Could not load config: {e}")
    
    def _on_closing(self):
        """Handle window close event"""
        # Save configuration
        self._save_config()
        
        # Stop simulation if running
        if self.simulators:
            self._stop_simulation()
        
        # Close window
        self.root.destroy()

