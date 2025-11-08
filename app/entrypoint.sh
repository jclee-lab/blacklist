#!/bin/bash
#
# Blacklist Application Entrypoint
# =================================
# Auto-applies UNAPPLIED patches on container start (smart detection)
#
# Version: 3.3.8+
# Date: 2025-10-30
# Author: Claude Code

set -eo pipefail

# Color codes
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
NC=$'\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Blacklist Application Entrypoint${NC}"
echo -e "${BLUE}========================================${NC}"

# Patch system disabled (no patches directory configured)
echo -e "${YELLOW}⚠️  Patch system disabled - skipping auto-patching${NC}"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Flask application...${NC}"
echo -e "${BLUE}========================================${NC}"

# Start Flask application
exec python run_app.py
