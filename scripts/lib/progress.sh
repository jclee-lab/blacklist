#!/bin/bash
# Progress Indicator Library - Phase 2 Implementation
#
# Purpose: Visual progress bars and ETA estimation for long-running operations
# Usage: source scripts/lib/progress.sh
#
# Created: 2025-10-22
# Phase: 2.3 - Progress Indicators

# ========================================
# Global Variables
# ========================================
PROGRESS_BAR_WIDTH=50
PROGRESS_START_TIME=0
PROGRESS_CURRENT_STEP=0
PROGRESS_TOTAL_STEPS=0

# ========================================
# Function: Initialize Progress Tracking
# ========================================
progress_init() {
    local total_steps="$1"
    PROGRESS_TOTAL_STEPS="${total_steps}"
    PROGRESS_CURRENT_STEP=0
    PROGRESS_START_TIME=$(date +%s)
}

# ========================================
# Function: Update Progress Bar
# ========================================
progress_update() {
    local current="$1"
    local total="$2"
    local message="${3:-Processing}"

    PROGRESS_CURRENT_STEP="${current}"

    # Calculate percentage
    local percent=$((current * 100 / total))

    # Calculate filled bars
    local filled=$((current * PROGRESS_BAR_WIDTH / total))
    local empty=$((PROGRESS_BAR_WIDTH - filled))

    # Calculate ETA
    local elapsed=$(($(date +%s) - PROGRESS_START_TIME))
    local eta="N/A"

    if [ "${current}" -gt 0 ]; then
        local rate=$((elapsed / current))
        local remaining=$((total - current))
        local eta_seconds=$((rate * remaining))

        # Format ETA
        if [ "${eta_seconds}" -lt 60 ]; then
            eta="${eta_seconds}s"
        elif [ "${eta_seconds}" -lt 3600 ]; then
            eta="$((eta_seconds / 60))m $((eta_seconds % 60))s"
        else
            eta="$((eta_seconds / 3600))h $(((eta_seconds % 3600) / 60))m"
        fi
    fi

    # Build progress bar
    printf "\r\033[34m[INFO]\033[0m %s [" "${message}"
    printf "%${filled}s" | tr ' ' '='
    printf "%${empty}s" | tr ' ' ' '
    printf "] %3d%% (%d/%d) ETA: %s" "${percent}" "${current}" "${total}" "${eta}"
}

# ========================================
# Function: Complete Progress
# ========================================
progress_complete() {
    local message="${1:-Complete}"
    echo  # New line after progress bar
    local elapsed=$(($(date +%s) - PROGRESS_START_TIME))

    # Format elapsed time
    local elapsed_formatted
    if [ "${elapsed}" -lt 60 ]; then
        elapsed_formatted="${elapsed}s"
    elif [ "${elapsed}" -lt 3600 ]; then
        elapsed_formatted="$((elapsed / 60))m $((elapsed % 60))s"
    else
        elapsed_formatted="$((elapsed / 3600))h $(((elapsed % 3600) / 60))m"
    fi

    echo -e "\033[32m[SUCCESS]\033[0m ${message} (took ${elapsed_formatted})"
}

# ========================================
# Function: Spinner for indefinite operations
# ========================================
progress_spinner() {
    local pid=$1
    local message="${2:-Processing}"
    local delay=0.1
    local spinstr='|/-\'

    while kill -0 "$pid" 2>/dev/null; do
        local temp=${spinstr#?}
        printf "\r\033[34m[INFO]\033[0m %s %c " "${message}" "${spinstr}"
        spinstr=${temp}${spinstr%"$temp"}
        sleep ${delay}
    done

    printf "\r\033[32m[SUCCESS]\033[0m %-60s\n" "${message}"
}

# ========================================
# Function: Step Progress (for multi-step operations)
# ========================================
progress_step() {
    local step_number="$1"
    local total_steps="$2"
    local step_name="$3"
    local status="${4:-in_progress}"  # in_progress, success, warning, error

    local percent=$((step_number * 100 / total_steps))

    case "${status}" in
        "success")
            echo -e "\033[32m[✓]\033[0m Step ${step_number}/${total_steps} (${percent}%): ${step_name}"
            ;;
        "warning")
            echo -e "\033[33m[⚠]\033[0m Step ${step_number}/${total_steps} (${percent}%): ${step_name}"
            ;;
        "error")
            echo -e "\033[31m[✗]\033[0m Step ${step_number}/${total_steps} (${percent}%): ${step_name}"
            ;;
        *)
            echo -e "\033[34m[→]\033[0m Step ${step_number}/${total_steps} (${percent}%): ${step_name}"
            ;;
    esac
}

# ========================================
# Function: File Copy Progress
# ========================================
progress_file_copy() {
    local source="$1"
    local destination="$2"
    local description="${3:-Copying files}"

    if command -v rsync &>/dev/null; then
        rsync -ah --info=progress2 "${source}" "${destination}" 2>&1 | \
        while IFS= read -r line; do
            if [[ "$line" =~ ([0-9]+)% ]]; then
                local percent="${BASH_REMATCH[1]}"
                printf "\r\033[34m[INFO]\033[0m %s... %3d%%" "${description}" "${percent}"
            fi
        done
        echo  # New line after progress
        echo -e "\033[32m[SUCCESS]\033[0m ${description} complete"
    else
        # Fallback to cp without progress
        cp -r "${source}" "${destination}"
        echo -e "\033[32m[SUCCESS]\033[0m ${description} complete"
    fi
}

# ========================================
# Function: Download Progress (for curl/wget)
# ========================================
progress_download() {
    local url="$1"
    local output="$2"
    local description="${3:-Downloading}"

    if command -v curl &>/dev/null; then
        curl -# -L -o "${output}" "${url}" 2>&1 | \
        while IFS= read -r line; do
            if [[ "$line" =~ ([0-9]+\.[0-9]+)% ]]; then
                local percent="${BASH_REMATCH[1]}"
                printf "\r\033[34m[INFO]\033[0m %s... %s%%" "${description}" "${percent}"
            fi
        done
        echo  # New line
        echo -e "\033[32m[SUCCESS]\033[0m ${description} complete"
    elif command -v wget &>/dev/null; then
        wget --progress=bar:force -O "${output}" "${url}" 2>&1 | \
        while IFS= read -r line; do
            echo "${line}"
        done
    else
        echo -e "\033[31m[ERROR]\033[0m No download tool available (curl/wget)"
        return 1
    fi
}

# ========================================
# Function: Time Estimate Display
# ========================================
progress_estimate() {
    local total_items="$1"
    local item_time_seconds="$2"
    local description="${3:-Operation}"

    local total_seconds=$((total_items * item_time_seconds))

    local hours=$((total_seconds / 3600))
    local minutes=$(((total_seconds % 3600) / 60))
    local seconds=$((total_seconds % 60))

    echo -e "\033[34m[INFO]\033[0m ${description} estimated time:"
    if [ "${hours}" -gt 0 ]; then
        echo -e "\033[34m[INFO]\033[0m   ${hours}h ${minutes}m ${seconds}s (${total_items} items @ ${item_time_seconds}s/item)"
    elif [ "${minutes}" -gt 0 ]; then
        echo -e "\033[34m[INFO]\033[0m   ${minutes}m ${seconds}s (${total_items} items @ ${item_time_seconds}s/item)"
    else
        echo -e "\033[34m[INFO]\033[0m   ${seconds}s (${total_items} items @ ${item_time_seconds}s/item)"
    fi
}
