#!/bin/bash
# generate-certs.sh - Generate test certificates for IoT simulator
# This creates self-signed certificates for testing TLS/mTLS

set -e

# Create directory for certificates
mkdir -p certs
cd certs

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     IoT Simulator - Certificate Generation Tool           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Generating test certificates for TLS/mTLS..."
echo ""

# Configuration
COUNTRY="US"
STATE="CA"
CITY="San Francisco"
ORG="IoT Test Org"
VALIDITY_DAYS=365

# Generate CA certificate
echo "[1/3] Generating CA certificate..."
openssl genrsa -out ca.key 2048 2>/dev/null
openssl req -x509 -new -nodes -key ca.key -sha256 -days $VALIDITY_DAYS -out ca.crt \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=Test CA" 2>/dev/null
echo "✓ CA certificate generated (ca.crt, ca.key)"

# Generate server certificate
echo ""
echo "[2/3] Generating server certificate..."
openssl genrsa -out server.key 2048 2>/dev/null
openssl req -new -key server.key -out server.csr \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=localhost" 2>/dev/null

# Create extensions file for SAN (Subject Alternative Names)
cat > server_ext.cnf << EOF
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = *.localhost
IP.1 = 127.0.0.1
IP.2 = ::1
EOF

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days $VALIDITY_DAYS -sha256 \
  -extfile server_ext.cnf 2>/dev/null
  
rm server.csr server_ext.cnf
echo "✓ Server certificate generated (server.crt, server.key)"

# Generate client certificate
echo ""
echo "[3/3] Generating client certificate..."
openssl genrsa -out client.key 2048 2>/dev/null
openssl req -new -key client.key -out client.csr \
  -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/CN=iot-device-001" 2>/dev/null
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out client.crt -days $VALIDITY_DAYS -sha256 2>/dev/null
  
rm client.csr
echo "✓ Client certificate generated (client.crt, client.key)"

# Set appropriate permissions
chmod 600 *.key
chmod 644 *.crt

cd ..

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                 Certificate Generation Complete!          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Generated files in ./certs/:"
echo ""
echo "  CA Certificate:      ca.crt"
echo "  CA Private Key:      ca.key"
echo ""
echo "  Server Certificate:  server.crt"
echo "  Server Private Key:  server.key"
echo ""
echo "  Client Certificate:  client.crt"
echo "  Client Private Key:  client.key"
echo ""
echo "Usage in IoT Simulator:"
echo ""
echo "  For TLS (server authentication only):"
echo "    - CA Cert: certs/ca.crt"
echo ""
echo "  For mTLS (mutual authentication):"
echo "    - CA Cert:     certs/ca.crt"
echo "    - Client Cert: certs/client.crt"
echo "    - Client Key:  certs/client.key"
echo ""
echo "For more information, see TLS_GUIDE.md"
echo ""
