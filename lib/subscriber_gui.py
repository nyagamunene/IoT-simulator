"""
IoT Device Simulator - MQTT Subscriber GUI with Actuator Visualization
Subscribe to MQTT topics, view messages, and control actuators interactively
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import paho.mqtt.client as mqtt
from datetime import datetime
import json
import ssl


class MQTTSubscriberGUI:
    """GUI for MQTT Subscriber with Actuator Visualization"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("MQTT Subscriber - IoT Simulator")
        self.root.geometry("900x1000")
        
        self.client = None
        self.connected = False
        
        # Actuator states
        self.actuator_states = {
            'bulb': {'on': False, 'brightness': 0, 'topic': 'iot/actuators/bulb'},
            'relay': {'on': False, 'topic': 'iot/actuators/relay'},
            'thermostat': {'target_temp': 22, 'mode': 'off', 'topic': 'iot/actuators/thermostat'}
        }
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection Configuration
        config_frame = ttk.LabelFrame(main_frame, text="MQTT Broker Configuration", padding="10")
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
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
        topics_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(topics_frame, text="Topics (one per line):").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        topics_scrolled = ttk.Frame(topics_frame)
        topics_scrolled.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.topics_text = tk.Text(topics_scrolled, height=3, width=60)
        self.topics_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        scrollbar = ttk.Scrollbar(topics_scrolled, orient=tk.VERTICAL, command=self.topics_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.topics_text['yscrollcommand'] = scrollbar.set
        
        # Default topics
        default_topics = """m/{{DOMAINID}}/c/{{CHANNELID}}/subtopic"""
        self.topics_text.insert('1.0', default_topics)
        
        ttk.Label(topics_frame, text="Tip: Use # for wildcard (e.g., m/domainid/c/channelid/#)", 
                 font=('TkDefaultFont', 8, 'italic')).grid(row=2, column=0, sticky=tk.W)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=10)
        
        self.connect_btn = ttk.Button(button_frame, text="Connect & Subscribe", command=self._connect)
        self.connect_btn.grid(row=0, column=0, padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", command=self._disconnect, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="Clear Messages", command=self._clear_messages).grid(row=0, column=2, padx=5)
        
        ttk.Button(button_frame, text="Detach Logs", command=self._detach_logs).grid(row=0, column=3, padx=5)
        
        # Status
        self.status_var = tk.StringVar(value="Status: Disconnected")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Actuator Visualization Frame
        actuator_frame = ttk.LabelFrame(main_frame, text="Actuator Control (Click to Toggle/Adjust)", padding="10")
        actuator_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Canvas for actuator widgets
        self.actuator_canvas = tk.Canvas(actuator_frame, height=120, bg='#f0f0f0')
        self.actuator_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Draw actuator widgets
        self._draw_actuators()
        
        # Bind click events
        self.actuator_canvas.bind('<Button-1>', self._on_actuator_click)
        
        # Statistics
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.msg_count_var = tk.StringVar(value="Messages: 0")
        ttk.Label(stats_frame, textvariable=self.msg_count_var).grid(row=0, column=0, padx=10)
        
        self.topics_count_var = tk.StringVar(value="Topics: 0")
        ttk.Label(stats_frame, textvariable=self.topics_count_var).grid(row=0, column=1, padx=10)
        
        # Received Messages Display
        messages_frame = ttk.LabelFrame(main_frame, text="Received Messages", padding="10")
        messages_frame.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.messages_text = scrolledtext.ScrolledText(messages_frame, height=30, width=100, state=tk.DISABLED, wrap=tk.WORD)
        self.messages_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Detachable log window reference
        self.detached_log_window = None
        
        # Configure text tags for colored output
        self.messages_text.tag_config('timestamp', foreground='gray')
        self.messages_text.tag_config('topic', foreground='blue', font=('TkDefaultFont', 9, 'bold'))
        self.messages_text.tag_config('payload', foreground='black')
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        messages_frame.columnconfigure(0, weight=1)
        messages_frame.rowconfigure(0, weight=1)
        
        self.message_count = 0
        self.unique_topics = set()
    
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
            self.status_var.set(f"Status: Connected to {self.broker_var.get()}:{self.port_var.get()}")
            
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
                    self.unique_topics.add(topic)
            
            self.topics_count_var.set(f"Topics: {len(self.unique_topics)}")
            self._log("-"*60, 'payload')
            self._log("Waiting for messages...", 'payload')
            self._log("="*60, 'topic')
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized"
            }
            error_msg = error_messages.get(rc, f"Unknown error (code {rc})")
            self.status_var.set(f"Status: Connection failed")
            
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
            self.status_var.set("Status: Disconnected")
            self._log("✓ Disconnected from broker", 'topic')
        else:
            self.status_var.set(f"Status: Unexpected disconnection (code {rc})")
            self._log(f"✗ Unexpected disconnection (code {rc})", 'topic')
    
    def _on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        topic = msg.topic
        
        try:
            # Try to decode payload as UTF-8
            payload = msg.payload.decode('utf-8')
            
            # Parse actuator messages to update visualization
            self._parse_actuator_message(topic, payload)
            
            # Try to pretty-print JSON
            try:
                json_obj = json.loads(payload)
                payload = json.dumps(json_obj, indent=2)
            except:
                pass  # Not JSON, use as-is
        except:
            # If decode fails, show as hex
            payload = f"<binary: {msg.payload.hex()}>"
        
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
        self.msg_count_var.set(f"Messages: {self.message_count}")
        
        # Track unique topics (without wildcards)
        self.unique_topics.add(topic)
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
            self.status_var.set("Status: Connection timeout")
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
            
            self.status_var.set("Status: Connecting...")
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
            self.status_var.set("Status: Connection failed")
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
        self.status_var.set("Status: Disconnected")
    
    def _clear_messages(self):
        """Clear the messages display"""
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete('1.0', tk.END)
        self.messages_text.config(state=tk.DISABLED)
        self.message_count = 0
        self.msg_count_var.set("Messages: 0")
        
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
            font=('Courier', 10)
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


def main():
    """Run the MQTT subscriber GUI"""
    root = tk.Tk()
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
