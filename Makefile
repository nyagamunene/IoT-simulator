.PHONY: help install run clean servers-up servers-down servers-logs mqtt-up http-up ws-up coap-up

VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

help:
	@echo "Available targets:"
	@echo "  make install       - Create virtual environment and install dependencies"
	@echo "  make run           - Install dependencies and run the simulator"
	@echo "  make clean         - Remove virtual environment"
	@echo ""
	@echo "Test Infrastructure (Docker):"
	@echo "  make servers-up    - Start all test servers (MQTT, HTTP, WebSocket, CoAP)"
	@echo "  make servers-down  - Stop all test servers"
	@echo "  make servers-logs  - View logs from all servers"
	@echo ""
	@echo "Individual Servers:"
	@echo "  make mqtt-up       - Start MQTT broker only"
	@echo "  make http-up       - Start HTTP server only"
	@echo "  make ws-up         - Start WebSocket server only"
	@echo "  make coap-up       - Start CoAP server only"

$(VENV_DIR)/bin/activate:
	python3 -m venv $(VENV_DIR)

install: $(VENV_DIR)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installation complete!"

run: install
	$(PYTHON) main.py

clean:
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed"

# Start all test servers
servers-up:
	@echo "Starting all test servers..."
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "✓ All servers running:"
	@echo "  - MQTT:      localhost:1883"
	@echo "  - HTTP:      localhost:8080"
	@echo "  - WebSocket: localhost:8765"
	@echo "  - CoAP:      localhost:5683"

servers-down:
	docker compose -f docker/docker-compose.yml down

servers-logs:
	docker compose -f docker/docker-compose.yml logs -f

# Individual server controls
mqtt-up:
	@echo "Starting MQTT broker..."
	docker compose -f docker/docker-compose.yml up -d mosquitto
	@echo "✓ MQTT broker: localhost:1883"

http-up:
	@echo "Starting HTTP server..."
	docker compose -f docker/docker-compose.yml up -d http-server
	@echo "✓ HTTP server: localhost:8080"

ws-up:
	@echo "Starting WebSocket server..."
	docker compose -f docker/docker-compose.yml up -d websocket-server
	@echo "✓ WebSocket server: localhost:8765"

coap-up:
	@echo "Starting CoAP server..."
	docker compose -f docker/docker-compose.yml up -d coap-server
	@echo "✓ CoAP server: localhost:5683"

