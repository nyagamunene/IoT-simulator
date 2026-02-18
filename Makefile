.PHONY: help install run subscriber clean servers-up servers-down servers-logs mqtt-up http-up ws-up coap-up mqtt-logs http-logs ws-logs coap-logs

VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

# Load environment variables from docker/.env
include docker/.env
export

help:
	@echo "Available targets:"
	@echo "  make install       - Create virtual environment and install dependencies"
	@echo "  make run           - Install dependencies and run the simulator"
	@echo "  make subscriber    - Launch MQTT subscriber GUI"
	@echo "  make clean         - Remove virtual environment"
	@echo ""
	@echo "Test Infrastructure (Docker):"
	@echo "  make servers-up    - Start all test servers (MQTT, HTTP, WebSocket, CoAP)"
	@echo "  make servers-down  - Stop all test servers"
	@echo "  make servers-logs  - View logs from all servers (live)"
	@echo ""
	@echo "Individual Servers:"
	@echo "  make mqtt-up       - Start MQTT broker only"
	@echo "  make http-up       - Start HTTP server only"
	@echo "  make ws-up         - Start WebSocket server only"
	@echo "  make coap-up       - Start CoAP server only"
	@echo ""
	@echo "Debug Logs:"
	@echo "  make mqtt-logs     - View MQTT broker logs (live)"
	@echo "  make http-logs     - View HTTP server logs (live)"
	@echo "  make ws-logs       - View WebSocket server logs (live)"
	@echo "  make coap-logs     - View CoAP server logs (live)"

$(VENV_DIR)/bin/activate:
	python3 -m venv $(VENV_DIR)

install: $(VENV_DIR)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installation complete!"

run: install
	$(PYTHON) main.py

subscriber: install
	$(PYTHON) -m lib.subscriber_gui

clean:
	rm -rf $(VENV_DIR)
	@echo "Virtual environment removed"

# Start all test servers
servers-up:
	@echo "Starting all test servers..."
	docker compose -f docker/docker-compose.yml up -d
	@echo ""
	@echo "✓ All servers running:"
	@echo "  - MQTT:      localhost:$(MQTT_PORT)"
	@echo "  - HTTP:      localhost:$(HTTP_PORT)"
	@echo "  - WebSocket: localhost:$(WEBSOCKET_PORT)"
	@echo "  - CoAP:      localhost:$(COAP_PORT)"

servers-down:
	docker compose -f docker/docker-compose.yml down

servers-logs:
	docker compose -f docker/docker-compose.yml logs -f

# Individual server controls
mqtt-up:
	@echo "Starting MQTT broker..."
	docker compose -f docker/docker-compose.yml up -d mosquitto
	@echo "✓ MQTT broker: localhost:$(MQTT_PORT)"

http-up:
	@echo "Starting HTTP server..."
	docker compose -f docker/docker-compose.yml up -d http-server
	@echo "✓ HTTP server: localhost:$(HTTP_PORT)"

ws-up:
	@echo "Starting WebSocket server..."
	docker compose -f docker/docker-compose.yml up -d websocket-server
	@echo "✓ WebSocket server: localhost:$(WEBSOCKET_PORT)"

coap-up:
	@echo "Starting CoAP server..."
	docker compose -f docker/docker-compose.yml up -d coap-server
	@echo "✓ CoAP server: localhost:$(COAP_PORT)"

# Individual server logs
mqtt-logs:
	@echo "Viewing MQTT broker logs (Ctrl+C to exit)..."
	docker compose -f docker/docker-compose.yml logs -f mosquitto

http-logs:
	@echo "Viewing HTTP server logs (Ctrl+C to exit)..."
	docker compose -f docker/docker-compose.yml logs -f http-server

ws-logs:
	@echo "Viewing WebSocket server logs (Ctrl+C to exit)..."
	docker compose -f docker/docker-compose.yml logs -f websocket-server

coap-logs:
	@echo "Viewing CoAP server logs (Ctrl+C to exit)..."
	docker compose -f docker/docker-compose.yml logs -f coap-server

