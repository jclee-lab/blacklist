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

# Applied patches tracking file
APPLIED_PATCHES_FILE="/app/.applied_patches"

# Create tracking file if not exists
if [ ! -f "$APPLIED_PATCHES_FILE" ]; then
    touch "$APPLIED_PATCHES_FILE"
    echo -e "${BLUE}📝 Created patch tracking file: $APPLIED_PATCHES_FILE${NC}"
fi

# Patch directories (support both absolute and relative paths)
PATCH_DIRS=(
    "/patches"                          # Volume mount (docker-compose.yml)
    "/app/patches"                      # Relative to app directory
    "./offline-packages/patches"        # Offline package path
)

# Find available patch directory
PATCH_DIR=""
for dir in "${PATCH_DIRS[@]}"; do
    if [ -d "$dir" ] && [ "$(ls -A "$dir"/*.sh 2>/dev/null)" ]; then
        PATCH_DIR="$dir"
        echo -e "${BLUE}📦 Patches directory found: $PATCH_DIR${NC}"
        break
    fi
done

# Function to check if patch already applied
is_patch_applied() {
    local patch_name="$1"
    grep -q "^${patch_name}$" "$APPLIED_PATCHES_FILE" 2>/dev/null
}

# Function to mark patch as applied
mark_patch_applied() {
    local patch_name="$1"
    echo "$patch_name" >> "$APPLIED_PATCHES_FILE"
}

# Apply patches if directory found
if [ -n "$PATCH_DIR" ]; then
    # Scan for available patches
    TOTAL_PATCHES=$(find "$PATCH_DIR" -name "*.sh" 2>/dev/null | wc -l)

    if [ "$TOTAL_PATCHES" -eq 0 ]; then
        echo -e "${YELLOW}⚠️  No patch files (.sh) found in $PATCH_DIR${NC}"
    else
        echo -e "${BLUE}🔍 Scanning patches: $TOTAL_PATCHES total${NC}"

        # Track applied patches
        APPLIED_COUNT=0
        SKIPPED_COUNT=0
        FAILED_COUNT=0

        # Apply only unapplied patches (sorted by name)
        for patch_file in $(ls "$PATCH_DIR"/*.sh 2>/dev/null | sort); do
            if [ -f "$patch_file" ]; then
                patch_name=$(basename "$patch_file")

                # Check if already applied
                if is_patch_applied "$patch_name"; then
                    echo -e "${BLUE}  ⊙ $patch_name (already applied, skipping)${NC}"
                    SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
                    continue
                fi

                # Apply new patch
                echo -e "${YELLOW}  → Applying: $patch_name${NC}"

                # Execute patch (suppress output unless it fails)
                if bash "$patch_file" > /tmp/patch_${patch_name}.log 2>&1; then
                    echo -e "${GREEN}  ✓ $patch_name applied successfully${NC}"
                    mark_patch_applied "$patch_name"
                    APPLIED_COUNT=$((APPLIED_COUNT + 1))
                else
                    echo -e "${RED}  ✗ $patch_name failed (non-critical, continuing...)${NC}"
                    cat /tmp/patch_${patch_name}.log
                    FAILED_COUNT=$((FAILED_COUNT + 1))
                fi
            fi
        done

        # Summary
        echo -e "${GREEN}✓ Summary: Applied: $APPLIED_COUNT | Skipped: $SKIPPED_COUNT | Failed: $FAILED_COUNT${NC}"

        # Show applied patches history
        if [ -f "$APPLIED_PATCHES_FILE" ]; then
            HISTORY_COUNT=$(wc -l < "$APPLIED_PATCHES_FILE")
            echo -e "${BLUE}📋 Total patches in history: $HISTORY_COUNT${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  No patches directory found - skipping auto-patching${NC}"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Starting Flask application...${NC}"
echo -e "${BLUE}========================================${NC}"

# Start Flask application
exec python run_app.py
