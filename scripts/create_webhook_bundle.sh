#!/bin/bash

# Create webhook bundle script for GitBridge
# Creates a tar.gz archive of webhook documentation and configuration

# Set variables
TIMESTAMP=$(date +%Y%m%d_%H%M)
ARCHIVE_NAME="gitbridge_webhook_bundle_${TIMESTAMP}.tar.gz"
SPECS_DIR="/specs/webhook"

# Create specs directory if it doesn't exist
mkdir -p "${SPECS_DIR}"

# Create temporary directory
TEMP_DIR=$(mktemp -d)
BUNDLE_DIR="${TEMP_DIR}/webhook_bundle"
mkdir -p "${BUNDLE_DIR}"

# Copy documentation
echo "Copying documentation..."
mkdir -p "${BUNDLE_DIR}/docs"
cp -r docs/architecture/webhook_system.md "${BUNDLE_DIR}/docs/"
cp -r docs/COMPONENTS.md "${BUNDLE_DIR}/docs/"

# Copy examples
echo "Copying examples..."
mkdir -p "${BUNDLE_DIR}/docs/examples"
cp docs/examples/webhook_post_example.json "${BUNDLE_DIR}/docs/examples/"
cp docs/examples/event_flow_walkthrough.md "${BUNDLE_DIR}/docs/examples/"

# Copy configuration
echo "Copying configuration..."
mkdir -p "${BUNDLE_DIR}/config"
cp config/webhook_config.yaml "${BUNDLE_DIR}/config/"
cp config/validate_config.py "${BUNDLE_DIR}/config/"

# Copy monitoring
echo "Copying monitoring configuration..."
mkdir -p "${BUNDLE_DIR}/monitoring"
cp monitoring/prometheus_exporter.py "${BUNDLE_DIR}/monitoring/"
cp monitoring/mock_dashboard.json "${BUNDLE_DIR}/monitoring/"

# Copy development tools
echo "Copying development tools..."
mkdir -p "${BUNDLE_DIR}/dev_tools"
cp dev_tools/openapi_converter.py "${BUNDLE_DIR}/dev_tools/"

# Copy tests
echo "Copying tests..."
mkdir -p "${BUNDLE_DIR}/tests/integration"
cp tests/integration/test_webhook_flow.py "${BUNDLE_DIR}/tests/integration/"

# Copy requirements
echo "Copying requirements..."
cp requirements-webhook.txt "${BUNDLE_DIR}/"

# Create archive
echo "Creating archive..."
tar -czf "${SPECS_DIR}/${ARCHIVE_NAME}" -C "${TEMP_DIR}" "webhook_bundle"

# Generate checksum
echo "Generating checksum..."
sha256sum "${SPECS_DIR}/${ARCHIVE_NAME}" > "${SPECS_DIR}/${ARCHIVE_NAME}.sha256"

# Cleanup
rm -rf "${TEMP_DIR}"

echo "Bundle created: ${SPECS_DIR}/${ARCHIVE_NAME}"
echo "Checksum file: ${SPECS_DIR}/${ARCHIVE_NAME}.sha256"

# Output quick start instructions
cat << EOF

📦 GitBridge Webhook Bundle Quick Start
=====================================

1. Extract the bundle:
   tar xzf ${ARCHIVE_NAME}

2. Install dependencies:
   pip install -r webhook_bundle/requirements-webhook.txt

3. Start required services:
   docker-compose up -d redis prometheus grafana

4. Run integration tests:
   pytest webhook_bundle/tests/integration/

5. Start development server:
   python -m webhook_bundle.app --dev

For more information, see:
- docs/architecture/webhook_system.md
- docs/examples/event_flow_walkthrough.md

EOF 