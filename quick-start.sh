#!/bin/bash
################################################################################
# Quick Start - One-command deployment from Git clone
################################################################################

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OFFLINE_DIR="${PROJECT_ROOT}/offline-packages"

echo "========================================="
echo "BLACKLIST Quick Start"
echo "========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose first."
    exit 1
fi

# Step 1: Load Docker images
if [ -d "${OFFLINE_DIR}" ] && [ -n "$(ls -A "${OFFLINE_DIR}"/*.tar.gz 2>/dev/null)" ]; then
    echo ""
    echo "[1/3] Loading pre-built Docker images..."
    "${OFFLINE_DIR}/load-images.sh"
else
    echo ""
    echo "[1/3] Building Docker images (first time)..."
    make build
fi

# Step 2: Setup environment
echo ""
echo "[2/3] Setting up environment..."

if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials!"
    echo "   - REGTECH_ID=<your_username>"
    echo "   - REGTECH_PW=<your_password>"
    echo ""
    read -r -p "Press Enter to continue after editing .env..."
fi

# Step 3: Start services
echo ""
echo "[3/3] Starting services..."
docker-compose up -d

# Wait for services
echo ""
echo "Waiting for services to be ready..."
sleep 5

# Health check
echo ""
echo "========================================="
echo "Health Check"
echo "========================================="

for i in {1..30}; do
    if curl -sf http://localhost:2542/health > /dev/null 2>&1; then
        echo "✓ Application is running!"
        break
    fi
    echo "Waiting for application... ($i/30)"
    sleep 2
done

echo ""
echo "========================================="
echo "✓ Deployment Complete!"
echo "========================================="
echo ""
echo "Access URLs:"
echo "  - Application: http://localhost:2542"
echo "  - Frontend:    http://localhost:2543"
echo "  - Health:      http://localhost:2542/health"
echo ""
echo "Useful commands:"
echo "  - View logs:   make logs"
echo "  - Stop:        make down"
echo "  - Restart:     make restart"
echo "  - Health:      make health"
echo ""
