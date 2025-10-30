#!/bin/bash
##############################################################################
# Migration 007: Create data directory structure
# Date: 2025-10-23
# Purpose: Ensure all required data directories exist for bind mounts
##############################################################################

set -euo pipefail

# Get project root (assuming script is in postgres/migrations/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[INFO] Creating data directory structure..."

# Create all required data directories
mkdir -p "${PROJECT_ROOT}/data/postgres"
mkdir -p "${PROJECT_ROOT}/data/redis"
mkdir -p "${PROJECT_ROOT}/data/collector"
mkdir -p "${PROJECT_ROOT}/data/app/logs"
mkdir -p "${PROJECT_ROOT}/data/app/uploads"
mkdir -p "${PROJECT_ROOT}/data/nginx/logs"

echo "[SUCCESS] Data directories created:"
find "${PROJECT_ROOT}/data/" -maxdepth 1 -type d -exec basename {} \;

echo ""
echo "[INFO] Directory structure:"
tree -L 2 "${PROJECT_ROOT}/data/" 2>/dev/null || find "${PROJECT_ROOT}/data/" -type d -print

echo ""
echo "✅ Migration 007 complete!"
