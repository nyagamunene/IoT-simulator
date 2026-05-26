"""
IoT Device Simulator - Enhanced MQTT Subscriber GUI with Actuator Visualization
Subscribe to MQTT topics, view messages, and control actuators interactively
Enhanced with ttkbootstrap theming, status indicators, and config persistence
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import ssl
from pathlib import Path


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


class MQTTSubscriberGUI:
    """Enhanced GUI for MQTT Subscriber with Actuator Visualization"""
    
    CONFIG_FILE = Path.home() / ".iot_subscriber_config.json"
    
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Subscriber - IoT Simulator")
        self.root.geometry("1200x900")
        
        self.client = None
        self.connected = False
        self.message_count = 0
        self.topic_set = set()
        
        # Actuator states
        # Topics follow Magistrala format: m/<DOMAINID>/c/<CHANNELID>/<subtopic>
        # Replace {{DOMAINID}} and {{CHANNELID}} with actual UUIDs before connecting.
        self.actuator_states = {
            'bulb': {'on': False, 'brightness': 0, 'topic': 'm/{{DOMAINID}}/c/{{CHANNELID}}/actuators/bulb'},
            'relay': {'on': False, 'topic': 'm/{{DOMAINID}}/c/{{CHANNELID}}/actuators/relay'},
            'thermostat': {'target_temp': 22, 'mode': 'off', 'topic': 'm/{{DOMAINID}}/c/{{CHANNELID}}/actuators/thermostat'}
        }

        self._create_menu()
        self._create_widgets()
        self._load_config()
        self._setup_auto_save()

        # Force text widget colors AFTER ttkbootstrap theme is applied
        self.root.after(100, self._force_text_colors)

        # Save config on window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _force_text_colors(self):
        """Re-apply white background on text widgets after ttkbootstrap theme overrides."""
        white_widgets = []
        if hasattr(self, 'messages_text'):
            white_widgets.append(self.messages_text)
        if hasattr(self, 'topics_text'):
            white_widgets.append(self.topics_text)
        for w in white_widgets:
            w.configure(bg='white', fg='black', insertbackground='black')
        # Re-apply message tags so they show on white background
        if hasattr(self, 'messages_text'):
            self.messages_text.tag_config('timestamp', foreground='#555555')
            self.messages_text.tag_config('topic', foreground='#0055cc',
                                          font=('TkDefaultFont', 9, 'bold'))
            self.messages_text.tag_config('payload', foreground='#111111')

    def _create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Theme submenu
        theme_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Theme", menu=theme_menu)
        themes = ['darkly', 'solar', 'superhero', 'cyborg', 'vapor', 'cosmo', 'flatly', 'journal', 'litera', 'minty']
        for theme in themes:
            theme_menu.add_command(label=theme.capitalize(), command=lambda t=theme: self._change_theme(t))
        
        tools_menu.add_separator()
        tools_menu.add_command(label="Exit", command=self._on_closing)
    
    def _create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        connection_tab = ttk.Frame(self.notebook)
        messages_tab = ttk.Frame(self.notebook)
        actuators_tab = ttk.Frame(self.notebook)

        self.notebook.add(connection_tab, text="🔌 Connection")
        self.notebook.add(messages_tab, text="📨 Messages")
        self.notebook.add(actuators_tab, text="⚡ Actuators")

        # Populate tabs
        self._create_connection_tab(connection_tab)
        self._create_messages_tab(messages_tab)
        self._create_actuators_tab(actuators_tab)
    
    def _create_connection_tab(self, parent):
        """Create connection configuration tab"""
        # Main container
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status Dashboard
        dashboard_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding="10")
        dashboard_frame.pack(fill=tk.X, pady=(0, 10))
        
        status_inner = ttk.Frame(dashboard_frame)
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
        
        ttk.Label(status_inner, text="Topics:").pack(side=tk.LEFT, padx=5)
        self.topics_count_var = tk.StringVar(value="0")
        ttk.Label(status_inner, textvariable=self.topics_count_var, font=('TkDefaultFont', 12, 'bold'), foreground='cyan').pack(side=tk.LEFT, padx=5)
        
        # Connection Configuration
        config_frame = ttk.LabelFrame(main_frame, text="MQTT Broker Configuration", padding="10")
        config_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.broker_var = tk.StringVar(value="messaging.magistrala.absmach.eu")
        ttk.Entry(config_frame, textvariable=self.broker_var, width=25).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        ttk.Label(config_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.port_var = tk.StringVar(value="8883")
        ttk.Entry(config_frame, textvariable=self.port_var, width=10).grid(row=0, column=3, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(config_frame, text="Client ID:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.client_id_var = tk.StringVar(value="subscriber_001")
        ttk.Entry(config_frame, textvariable=self.client_id_var, width=25).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # Authentication
        ttk.Label(config_frame, text="Username:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value="")
        ttk.Entry(config_frame, textvariable=self.username_var, width=25).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        ttk.Label(config_frame, text="Password:").grid(row=2, column=2, sticky=tk.W, pady=2, padx=(20, 0))
        self.password_var = tk.StringVar(value="")
        ttk.Entry(config_frame, textvariable=self.password_var, width=15, show="*").grid(row=2, column=3, sticky=tk.W, pady=2, padx=5)
        
        # TLS/SSL Configuration
        ttk.Label(config_frame, text="TLS/SSL:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.use_tls_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="Enable TLS", variable=self.use_tls_var, 
                       command=self._toggle_tls).grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(config_frame, text="CA Cert:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.ca_cert_var = tk.StringVar(value="/etc/ssl/certs/ca-certificates.crt")
        ttk.Entry(config_frame, textvariable=self.ca_cert_var, width=35).grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2, padx=5)
        ttk.Button(config_frame, text="Browse", command=self._browse_ca_cert, width=8).grid(row=4, column=3, sticky=tk.W, pady=2, padx=5)
        
        # Topics Configuration
        topics_frame = ttk.LabelFrame(main_frame, text="Subscription Topics", padding="10")
        topics_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(topics_frame, text="Topics (one per line):").pack(anchor=tk.W, pady=2)
        
        topics_scrolled = ttk.Frame(topics_frame)
        topics_scrolled.pack(fill=tk.X, pady=5)
        
        self.topics_text = tk.Text(topics_scrolled, height=3, width=80, bg='white', fg='black')
        self.topics_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(topics_scrolled, orient=tk.VERTICAL, command=self.topics_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.topics_text['yscrollcommand'] = scrollbar.set
        
        # Default topics
        default_topics = """m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic"""
        self.topics_text.insert('1.0', default_topics)
        
        ttk.Label(topics_frame, text="Tip: Use # for wildcard (e.g., m/domainid/c/channelid/#)", 
                 font=('TkDefaultFont', 8, 'italic')).pack(anchor=tk.W)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.connect_btn = ttk.Button(button_frame, text="🔌 Connect & Subscribe", command=self._connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="⏹  Disconnect", command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_messages_tab(self, parent):
        """Create messages display tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="Clear Messages", command=self._clear_messages).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Detach Window", command=self._detach_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Save Logs", command=self._save_logs).pack(side=tk.LEFT, padx=5)
        
        # Received Messages Display
        messages_frame = ttk.LabelFrame(main_frame, text="Received Messages", padding="10")
        messages_frame.pack(fill=tk.BOTH, expand=True)
        
        self.messages_text = scrolledtext.ScrolledText(
            messages_frame, height=35, width=120, state=tk.DISABLED, wrap=tk.WORD,
            bg='white', fg='black'
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colored output
        self.messages_text.tag_config('timestamp', foreground='#555555')
        self.messages_text.tag_config('topic', foreground='#0055cc', font=('TkDefaultFont', 9, 'bold'))
        self.messages_text.tag_config('payload', foreground='#111111')
        
        # Detachable log window reference
        self.detached_log_window = None

    def _create_actuators_tab(self, parent):
        """Create actuators control tab"""
        main_frame = ttk.Frame(parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Actuator Visualization Frame
        actuator_frame = ttk.LabelFrame(main_frame, text="Actuator Control (Click to Toggle/Adjust)", padding="10")
        actuator_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for actuator widgets
        self.actuator_canvas = tk.Canvas(actuator_frame, height=200, bg='#f0f0f0')
        self.actuator_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Draw actuator widgets
        self._draw_actuators()
        
        # Bind click events
        self.actuator_canvas.bind('<Button-1>', self._on_actuator_click)
    
    def _draw_actuators(self):
        """Draw actuator visualization widgets on canvas"""
        self.actuator_canvas.delete('all')
        canvas_width = 880
        
        # Bulb Actuator (left)
        bulb_x, bulb_y = 150, 70
        bulb_state = self.actuator_states['bulb']
        
        # Bulb shape
        if bulb_state['on']:
            brightness = bulb_state['brightness']
            # Yellow with brightness
            yellow_intensity = int(255 * (brightness / 100))
            color = f'#{yellow_intensity:02x}{yellow_intensity:02x}00'
        else:
            color = '#cccccc'  # Gray when off
        
        self.actuator_canvas.create_oval(bulb_x-30, bulb_y-40, bulb_x+30, bulb_y+10, 
                                        fill=color, outline='black', width=2, tags='bulb')
        self.actuator_canvas.create_rectangle(bulb_x-15, bulb_y+10, bulb_x+15, bulb_y+25,
                                             fill='#888888', outline='black', tags='bulb')
        
        # Bulb label
        status = f"ON ({bulb_state['brightness']}%)" if bulb_state['on'] else "OFF"
        self.actuator_canvas.create_text(bulb_x, bulb_y+45, text=f"💡 Bulb: {status}",
                                        font=('TkDefaultFont', 10, 'bold'), tags='bulb')
        
        # Relay Actuator (center)
        relay_x, relay_y = canvas_width//2, 70
        relay_state = self.actuator_states['relay']
        
        # Relay switch
        switch_color = '#00ff00' if relay_state['on'] else '#ff0000'
        self.actuator_canvas.create_rectangle(relay_x-40, relay_y-30, relay_x+40, relay_y+20,
                                             fill='#666666', outline='black', width=2, tags='relay')
        self.actuator_canvas.create_oval(relay_x-25, relay_y-15, relay_x+25, relay_y+5,
                                        fill=switch_color, outline='black', width=2, tags='relay')
        
        # Relay label
        status = "ON" if relay_state['on'] else "OFF"
        self.actuator_canvas.create_text(relay_x, relay_y+45, text=f"🔌 Relay: {status}",
                                        font=('TkDefaultFont', 10, 'bold'), tags='relay')
        
        # Thermostat Actuator (right)
        thermo_x, thermo_y = canvas_width - 150, 70
        thermo_state = self.actuator_states['thermostat']
        
        # Thermostat display
        mode_color = {'heating': '#ff6600', 'cooling': '#0066ff', 'off': '#cccccc'}[thermo_state['mode']]
        self.actuator_canvas.create_oval(thermo_x-35, thermo_y-35, thermo_x+35, thermo_y+25,
                                        fill=mode_color, outline='black', width=3, tags='thermostat')
        self.actuator_canvas.create_text(thermo_x, thermo_y-10, text=f"{thermo_state['target_temp']}°C",
                                        font=('TkDefaultFont', 16, 'bold'), fill='white', tags='thermostat')
        
        # Thermostat label
        self.actuator_canvas.create_text(thermo_x, thermo_y+45, 
                                        text=f"🌡️ Thermostat: {thermo_state['mode'].upper()}",
                                        font=('TkDefaultFont', 10, 'bold'), tags='thermostat')
    
    def _on_actuator_click(self, event):
        """Handle clicks on actuator widgets"""
        if not self.connected:
            messagebox.showwarning("Not Connected", "Connect to MQTT broker first!")
            return
        
        # Get clicked item
        item = self.actuator_canvas.find_closest(event.x, event.y)
        if not item:
            return
        
        tags = self.actuator_canvas.gettags(item[0])
        
        if 'bulb' in tags:
            # Toggle bulb and cycle brightness
            bulb = self.actuator_states['bulb']
            if not bulb['on']:
                bulb['on'] = True
                bulb['brightness'] = 30
            elif bulb['brightness'] < 100:
                bulb['brightness'] = min(100, bulb['brightness'] + 25)
            else:
                bulb['on'] = False
                bulb['brightness'] = 0
            
            # Send MQTT command
            command = {'command': 'turn_on' if bulb['on'] else 'turn_off'}
            if bulb['on']:
                command['brightness'] = bulb['brightness']
            
            self._publish_actuator_command('bulb', command)
            self._draw_actuators()
            
        elif 'relay' in tags:
            # Toggle relay
            relay = self.actuator_states['relay']
            relay['on'] = not relay['on']
            
            command = {'command': 'turn_on' if relay['on'] else 'turn_off'}
            self._publish_actuator_command('relay', command)
            self._draw_actuators()
            
        elif 'thermostat' in tags:
            # Cycle thermostat mode
            thermo = self.actuator_states['thermostat']
            modes = ['off', 'heating', 'cooling']
            current_idx = modes.index(thermo['mode'])
            thermo['mode'] = modes[(current_idx + 1) % len(modes)]
            
            # Adjust temperature based on mode
            if thermo['mode'] == 'heating':
                thermo['target_temp'] = 24
            elif thermo['mode'] == 'cooling':
                thermo['target_temp'] = 20
            else:
                thermo['target_temp'] = 22
            
            command = {
                'command': 'set_temperature',
                'target_temperature': thermo['target_temp'],
                'mode': thermo['mode']
            }
            self._publish_actuator_command('thermostat', command)
            self._draw_actuators()
    
    def _publish_actuator_command(self, actuator_type, command):
        """Publish actuator control command to MQTT"""
        if not self.client or not self.connected:
            return
        
        topic = self.actuator_states[actuator_type]['topic']
        payload = json.dumps(command)
        
        try:
            self.client.publish(topic, payload, qos=1)
            self._log(f"→ Published command to {topic}: {payload}", 'topic')
        except Exception as e:
            self._log(f"✗ Failed to publish: {e}", 'topic')
    
    def _parse_actuator_message(self, topic, payload_str):
        """Parse and update actuator state from incoming MQTT message"""
        try:
            payload = json.loads(payload_str)
            
            if 'bulb' in topic:
                if 'command' in payload:
                    self.actuator_states['bulb']['on'] = payload['command'] == 'turn_on'
                if 'brightness' in payload:
                    self.actuator_states['bulb']['brightness'] = payload['brightness']
                self._draw_actuators()
                
            elif 'relay' in topic:
                if 'command' in payload:
                    self.actuator_states['relay']['on'] = payload['command'] == 'turn_on'
                self._draw_actuators()
                
            elif 'thermostat' in topic:
                if 'target_temperature' in payload:
                    self.actuator_states['thermostat']['target_temp'] = payload['target_temperature']
                if 'mode' in payload:
                    self.actuator_states['thermostat']['mode'] = payload['mode']
                self._draw_actuators()
        except:
            pass  # Not actuator message or invalid JSON

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            self.connected = True
            
            # Update status LED and label
            self.status_led.set_status('connected')
            self.connection_label.set("Connected")
            
            self._log("="*60, 'topic')
            self._log("✓ MQTT CONNECTION ESTABLISHED", 'topic')
            self._log(f"  Broker: {self.broker_var.get()}:{self.port_var.get()}", 'topic')
            self._log(f"  Client ID: {self.client_id_var.get()}", 'topic')
            self._log("="*60, 'topic')
            
            # Now enable disconnect button since we're actually connected
            self.disconnect_btn.config(state=tk.NORMAL)
            
            # Subscribe to all topics
            topics = self.topics_text.get('1.0', tk.END).strip().split('\n')
            self._log("Subscribing to topics:", 'payload')
            for topic in topics:
                topic = topic.strip()
                if topic:
                    result = client.subscribe(topic, qos=1)
                    if result[0] == 0:
                        self._log(f"  ✓ {topic}", 'payload')
                    else:
                        self._log(f"  ✗ Failed: {topic}", 'topic')
            
            self._log("-"*60, 'payload')
            self._log("Waiting for messages...", 'payload')
            self._log("="*60, 'topic')
        else:
            self.connected = False
            self.status_led.set_status('error')
            self.connection_label.set("Connection Failed")
            
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error (code {rc})")
            self.status_led.set_status('error')
            self.connection_label.set("Connection Failed")
            
            self._log("="*60, 'topic')
            self._log("✗ MQTT CONNECTION FAILED", 'topic')
            self._log(f"  Error Code: {rc}", 'topic')
            self._log(f"  Reason: {error_msg}", 'topic')
            self._log(f"  Broker: {self.broker_var.get()}:{self.port_var.get()}", 'topic')
            self._log("="*60, 'topic')
            
            messagebox.showerror("Connection Error", f"Failed to connect to broker.\n{error_msg}")
            
            # Re-enable connect button
            self.connect_btn.config(state=tk.NORMAL)
            
            # Clean up
            if self.client:
                try:
                    self.client.loop_stop()
                except:
                    pass
                self.client = None
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc == 0:
            self.status_led.set_status('off')
            self.connection_label.set("Disconnected")
            self._log("✓ Disconnected from broker", 'topic')
        else:
            self.status_led.set_status('error')
            self.connection_label.set(f"Unexpected Disconnection")
            self._log(f"✗ Unexpected disconnection (code {rc})", 'topic')
    
    def _on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        topic = msg.topic
        
        try:
            # Try to decode payload as UTF-8
            payload = msg.payload.decode('utf-8')
        except Exception:
            payload = f"<binary: {msg.payload.hex()}>"

        if not payload.startswith('<binary'):
            # Parse actuator messages to update visualization
            try:
                self._parse_actuator_message(topic, payload)
            except Exception:
                pass

            # Try to pretty-print JSON
            try:
                json_obj = json.loads(payload)
                payload = json.dumps(json_obj, indent=2)
            except Exception:
                pass  # Not JSON, use as-is
        
        # Display message
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, f"[{timestamp}]\n", 'timestamp')
        self.messages_text.insert(tk.END, f"Topic: {topic}\n", 'topic')
        self.messages_text.insert(tk.END, f"{payload}\n", 'payload')
        self.messages_text.insert(tk.END, "-" * 80 + "\n")
        self.messages_text.see(tk.END)
        self.messages_text.config(state=tk.DISABLED)
        
        # Update statistics
        self.message_count += 1
        self.msg_count_var.set(str(self.message_count))
        
        # Track unique topics
        self.topic_set.add(topic)
        self.topics_count_var.set(str(len(self.topic_set)))
        self.topics_count_var.set(f"Unique Topics: {len([t for t in self.unique_topics if '#' not in t and '+' not in t])}")
    
    def _log(self, message, tag='payload'):
        """Log a message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, f"[{timestamp}] ", 'timestamp')
        self.messages_text.insert(tk.END, f"{message}\n", tag)
        self.messages_text.see(tk.END)
        self.messages_text.config(state=tk.DISABLED)        
        # Also update detached log window if it exists
        if self.detached_log_window and hasattr(self.detached_log_window, 'log_text'):
            try:
                self.detached_log_window.log_text.config(state=tk.NORMAL)
                self.detached_log_window.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.detached_log_window.log_text.see(tk.END)
                self.detached_log_window.log_text.config(state=tk.DISABLED)
            except tk.TclError:
                # Window was closed
                self.detached_log_window = None    
    def _toggle_tls(self):
        """Toggle TLS and update default port"""
        if self.use_tls_var.get():
            # TLS enabled - use port 8883
            if self.port_var.get() == "1883":
                self.port_var.set("8883")
        else:
            # TLS disabled - use port 1883
            if self.port_var.get() == "8883":
                self.port_var.set("1883")
    
    def _browse_ca_cert(self):
        """Browse for CA certificate file"""
        filename = filedialog.askopenfilename(
            title="Select CA Certificate",
            filetypes=[("Certificate files", "*.crt *.pem"), ("All files", "*.*")]
        )
        if filename:
            self.ca_cert_var.set(filename)
    
    def _check_connection_timeout(self):
        """Check if connection attempt has timed out"""
        # If not connected after timeout period, show error
        if not self.connected and self.client is not None:
            self.status_led.set_status('error')
            self.connection_label.set("Connection Timeout")
            self._log("✗ Connection timeout - broker not reachable", 'topic')
            messagebox.showerror("Connection Timeout", 
                               f"Could not connect to {self.broker_var.get()}:{self.port_var.get()}\n\n"
                               "Please check:\n"
                               "• Broker is running (try: make mqtt-up)\n"
                               "• Broker address and port are correct\n"
                               "• No firewall blocking the connection")
            
            # Clean up and re-enable connect button
            if self.client:
                try:
                    self.client.loop_stop()
                except:
                    pass
                self.client = None
            
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
    
    def _connect(self):
        """Connect to MQTT broker"""
        try:
            broker = self.broker_var.get()
            port = int(self.port_var.get())
            client_id = self.client_id_var.get()
            username = self.username_var.get()
            password = self.password_var.get()
            use_tls = self.use_tls_var.get()
            
            if not broker:
                messagebox.showerror("Error", "Broker address is required")
                return
            
            # Log connection details
            self._log("="*60, 'topic')
            self._log("MQTT Subscriber - Connection Details", 'topic')
            self._log("-"*60, 'payload')
            self._log(f"Broker: {broker}:{port}", 'payload')
            self._log(f"Client ID: {client_id}", 'payload')
            self._log(f"TLS/SSL: {'Enabled' if use_tls else 'Disabled'}", 'payload')
            self._log(f"Authentication: {'Enabled (' + username + ')' if username else 'Disabled'}", 'payload')
            
            # Get topics
            topics = self.topics_text.get('1.0', tk.END).strip().split('\n')
            topic_list = [t.strip() for t in topics if t.strip()]
            self._log(f"Topics to subscribe ({len(topic_list)}):", 'payload')
            for topic in topic_list:
                self._log(f"  - {topic}", 'payload')
            self._log("-"*60, 'payload')
            
            # Create MQTT client
            self.client = mqtt.Client(client_id=client_id)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Set username and password if provided
            if username:
                self.client.username_pw_set(username, password)
                self._log(f"✓ Authentication configured", 'payload')
            
            # Configure TLS/SSL if enabled
            if use_tls:
                ca_cert = self.ca_cert_var.get()
                try:
                    # Use system CA certificates or custom CA cert
                    if ca_cert and ca_cert.strip():
                        import os
                        if os.path.exists(ca_cert):
                            self.client.tls_set(ca_certs=ca_cert, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
                            self._log(f"✓ TLS enabled with CA: {ca_cert}", 'payload')
                        else:
                            # File doesn't exist, use system default
                            self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
                            self._log("✓ TLS enabled with system CA certificates", 'payload')
                    else:
                        # No CA cert specified, use system default
                        self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
                        self._log("✓ TLS enabled with system CA certificates", 'payload')
                    
                    self.client.tls_insecure_set(False)
                except Exception as e:
                    messagebox.showerror("TLS Error", f"Failed to configure TLS: {e}")
                    self._log(f"✗ TLS configuration failed: {e}", 'topic')
                    self.connect_btn.config(state=tk.NORMAL)
                    return
            
            # Update status LED and label
            self.status_led.set_status('connecting')
            self.connection_label.set("Connecting...")
            
            self._log(f"⟳ Connecting to {broker}:{port}...", 'topic')
            
            # Disable connect button during connection attempt
            self.connect_btn.config(state=tk.DISABLED)
            
            # Connect to broker (this is non-blocking with loop_start)
            self.client.connect(broker, port, 60)
            self.client.loop_start()
            
            # Schedule a timeout check (5 seconds)
            self.root.after(5000, self._check_connection_timeout)
            
        except ValueError:
            messagebox.showerror("Error", "Port must be a valid number")
            self.connect_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            self.status_led.set_status('error')
            self.connection_label.set("Connection Failed")
            self.connect_btn.config(state=tk.NORMAL)
            if self.client:
                try:
                    self.client.loop_stop()
                except:
                    pass
                self.client = None
    
    def _disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.client = None
        
        # Update UI
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        
        # Update status LED and label
        self.status_led.set_status('off')
        self.connection_label.set("Disconnected")
    
    def _clear_messages(self):
        """Clear the messages display"""
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete('1.0', tk.END)
        self.messages_text.config(state=tk.DISABLED)
        self.message_count = 0
        self.msg_count_var.set("0")
        self.topic_set.clear()
        self.topics_count_var.set("0")
        
        # Also clear detached log window if it exists
        if self.detached_log_window and hasattr(self.detached_log_window, 'log_text'):
            try:
                self.detached_log_window.log_text.config(state=tk.NORMAL)
                self.detached_log_window.log_text.delete('1.0', tk.END)
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
        self.detached_log_window.title("MQTT Subscriber - Message Logs")
        self.detached_log_window.geometry("1200x700")
        
        # Create main frame
        main_frame = ttk.Frame(self.detached_log_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(button_frame, text="Clear Logs", command=self._clear_messages).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Save Logs", command=self._save_logs).grid(row=0, column=1, padx=5)
        
        # Log output
        log_frame = ttk.Frame(main_frame)
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.detached_log_window.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Courier', 10),
            bg='white',
            fg='black'
        )
        self.detached_log_window.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Copy existing logs to detached window
        current_logs = self.messages_text.get('1.0', tk.END)
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
                    logs = self.messages_text.get('1.0', tk.END)
                    f.write(logs)
                messagebox.showinfo("Success", f"Logs saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save logs: {e}")
    
    def _change_theme(self, theme_name):
        """Change the ttkbootstrap theme"""
        try:
            import ttkbootstrap as ttk_bootstrap
            style = ttk_bootstrap.Style.get_instance()
            if style:
                style.theme_use(theme_name)
                self._log_message(f"Theme changed to: {theme_name}")
                # Re-apply our text widget colors after theme resets them
                self.root.after(100, self._force_text_colors)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change theme: {e}")
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config = {
                'broker': self.broker_var.get(),
                'port': self.port_var.get(),
                'client_id': self.client_id_var.get(),
                'username': self.username_var.get(),
                'password': self.password_var.get(),
                'use_tls': self.use_tls_var.get(),
                'ca_cert': self.ca_cert_var.get(),
                'topics': self.topics_text.get('1.0', tk.END).strip()
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if not self.CONFIG_FILE.exists():
                return
            
            with open(self.CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            if 'broker' in config:
                self.broker_var.set(config['broker'])
            if 'port' in config:
                self.port_var.set(config['port'])
            if 'client_id' in config:
                self.client_id_var.set(config['client_id'])
            if 'username' in config:
                self.username_var.set(config['username'])
            if 'password' in config:
                self.password_var.set(config['password'])
            if 'use_tls' in config:
                self.use_tls_var.set(config['use_tls'])
            if 'ca_cert' in config:
                self.ca_cert_var.set(config['ca_cert'])
            if 'topics' in config:
                self.topics_text.delete('1.0', tk.END)
                self.topics_text.insert('1.0', config['topics'])
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
    
    def _setup_auto_save(self):
        """Setup auto-save traces on important variables"""
        def save_callback(*args):
            # Use after_idle to debounce multiple rapid changes
            if hasattr(self, '_save_job'):
                self.root.after_cancel(self._save_job)
            self._save_job = self.root.after(1000, self._save_config)  # Save after 1 second of no changes
        
        # Add traces to all StringVar fields
        self.broker_var.trace_add('write', save_callback)
        self.port_var.trace_add('write', save_callback)
        self.client_id_var.trace_add('write', save_callback)
        self.username_var.trace_add('write', save_callback)
        self.password_var.trace_add('write', save_callback)
        self.use_tls_var.trace_add('write', save_callback)
        self.ca_cert_var.trace_add('write', save_callback)
        
        # Bind to topics text widget for auto-save on changes
        def on_topics_change(event=None):
            save_callback()
        
        self.topics_text.bind('<KeyRelease>', on_topics_change)
    
    def _on_closing(self):
        """Handle window close event"""
        # Save configuration
        self._save_config()
        
        # Disconnect if connected
        if self.connected:
            self._disconnect()
        
        # Close window
        self.root.destroy()


def main():
    """Run the MQTT subscriber GUI"""
    import ttkbootstrap as ttk_bootstrap
    root = ttk_bootstrap.Window(themename="darkly")
    app = MQTTSubscriberGUI(root)
    
    def on_closing():
        if app.connected:
            if messagebox.askokcancel("Quit", "Disconnect from broker and quit?"):
                app._disconnect()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
