#!/bin/bash
# Quick start script for IoT Device Simulator

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          IoT Device Simulator - Quick Start               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Installation Complete!                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Quick Start Options:"
echo ""
echo "1. Launch the GUI simulator:"
echo "   python3 main.py"
echo ""
echo "2. Start a test HTTP server (in another terminal):"
echo "   python3 tests/test_http_server.py"
echo ""
echo "3. Start a test MQTT subscriber (in another terminal):"
echo "   python3 tests/test_mqtt_subscriber.py"
echo ""
echo "4. Start MQTT broker with Docker (requires Docker):"
echo "   docker compose -f docker/docker-compose.yml up -d mosquitto"
echo "   # Or use: make mqtt-up"
echo ""
echo "For more information, see README.md"
echo ""

# Ask if user wants to start the GUI
read -p "Do you want to launch the simulator GUI now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 main.py
fi
