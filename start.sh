#!/bin/bash
#
# Blacklist System Startup Script
# Version: 3.3.8
# Purpose: Quick start with auto-patch support
#

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.yml"

echo ""
echo "=========================================="
echo "  Blacklist System Startup v3.3.8"
echo "=========================================="
echo ""

# Check prerequisites
echo "[1/4] Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found or outdated."
    exit 1
fi

echo "✓ Prerequisites OK"
echo ""

# Create required directories
echo "[2/4] Creating data directories..."
mkdir -p data/postgres data/redis data/uploads
echo "✓ Directories created"
echo ""

# Start services
echo "[3/4] Starting Docker services..."
echo "→ docker compose up -d"
docker compose up -d

echo ""
echo "✓ Services started"
echo ""

# Wait for services
echo "[4/4] Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "Checking service health:"
for service in blacklist-app blacklist-postgres blacklist-redis blacklist-nginx; do
    if docker ps | grep -q "$service"; then
        echo "✓ $service running"
    else
        echo "⚠  $service not running (may still be starting)"
    fi
done

echo ""
echo "=========================================="
echo "✓ Startup complete!"
echo "=========================================="
echo ""
echo "Access points:"
echo "  • Web UI:    https://localhost (or http://localhost)"
echo "  • API Docs:  http://localhost:2542/api/docs"
echo "  • Health:    http://localhost:2542/health"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker compose logs -f"
echo "  • Check status:  docker compose ps"
echo "  • Stop all:      docker compose down"
echo "  • Run tests:     docker exec blacklist-app pytest tests/ -v"
echo ""
echo "Note: Auto-patch system is active!"
echo "  Patches from ./patch/ are automatically applied on start."
echo "  View patch history: docker exec blacklist-app cat /app/.applied_patches"
echo ""
