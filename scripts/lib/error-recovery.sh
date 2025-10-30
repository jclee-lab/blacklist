#!/bin/bash
# Error Recovery Library - Phase 2 Implementation
#
# Purpose: Checkpoint/resume mechanism and rollback capability
# Usage: source scripts/lib/error-recovery.sh
#
# Created: 2025-10-22
# Phase: 2.4 - Error Recovery

# ========================================
# Global Variables
# ========================================
CHECKPOINT_DIR="${CHECKPOINT_DIR:-/tmp/blacklist-checkpoints}"
CHECKPOINT_FILE="${CHECKPOINT_DIR}/checkpoint.state"
CHECKPOINT_ENABLED="${CHECKPOINT_ENABLED:-true}"
ROLLBACK_STACK=()

# ========================================
# Function: Initialize Error Recovery
# ========================================
recovery_init() {
    local operation_name="$1"

    if [ "${CHECKPOINT_ENABLED}" = "true" ]; then
        mkdir -p "${CHECKPOINT_DIR}"

        # Create new checkpoint file
        cat > "${CHECKPOINT_FILE}" <<EOF
{
  "operation": "${operation_name}",
  "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "completed_steps": [],
  "failed_step": null,
  "status": "in_progress"
}
EOF

        echo -e "\033[34m[INFO]\033[0m Checkpointing enabled: ${CHECKPOINT_DIR}"
    fi
}

# ========================================
# Function: Save Checkpoint
# ========================================
checkpoint_save() {
    local step_name="$1"
    local step_data="${2:-{}}"

    if [ "${CHECKPOINT_ENABLED}" != "true" ] || [ ! -f "${CHECKPOINT_FILE}" ]; then
        return 0
    fi

    # Update checkpoint file with completed step
    local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

    # Use python/jq to update JSON (fallback to simple append)
    if command -v jq &>/dev/null; then
        local temp_file="${CHECKPOINT_FILE}.tmp"
        jq --arg step "${step_name}" \
           --arg time "${timestamp}" \
           --argjson data "${step_data}" \
           '.completed_steps += [{name: $step, timestamp: $time, data: $data}]' \
           "${CHECKPOINT_FILE}" > "${temp_file}"
        mv "${temp_file}" "${CHECKPOINT_FILE}"
    else
        # Fallback: simple text append
        echo "${timestamp} - Completed: ${step_name}" >> "${CHECKPOINT_FILE}.log"
    fi

    echo -e "\033[34m[INFO]\033[0m Checkpoint saved: ${step_name}"
}

# ========================================
# Function: Check if Step Completed
# ========================================
checkpoint_is_completed() {
    local step_name="$1"

    if [ "${CHECKPOINT_ENABLED}" != "true" ] || [ ! -f "${CHECKPOINT_FILE}" ]; then
        return 1  # Not completed
    fi

    if command -v jq &>/dev/null; then
        local completed=$(jq -r --arg step "${step_name}" \
            '.completed_steps[] | select(.name == $step) | .name' \
            "${CHECKPOINT_FILE}" 2>/dev/null)

        if [ -n "${completed}" ]; then
            return 0  # Completed
        fi
    else
        # Fallback: grep in log file
        if grep -q "Completed: ${step_name}" "${CHECKPOINT_FILE}.log" 2>/dev/null; then
            return 0  # Completed
        fi
    fi

    return 1  # Not completed
}

# ========================================
# Function: Resume from Checkpoint
# ========================================
checkpoint_resume() {
    if [ "${CHECKPOINT_ENABLED}" != "true" ] || [ ! -f "${CHECKPOINT_FILE}" ]; then
        echo -e "\033[33m[WARNING]\033[0m No checkpoint found, starting from beginning"
        return 1
    fi

    echo -e "\033[34m[INFO]\033[0m Found existing checkpoint"

    if command -v jq &>/dev/null; then
        local operation=$(jq -r '.operation' "${CHECKPOINT_FILE}")
        local start_time=$(jq -r '.start_time' "${CHECKPOINT_FILE}")
        local completed_count=$(jq -r '.completed_steps | length' "${CHECKPOINT_FILE}")

        echo -e "\033[34m[INFO]\033[0m Operation: ${operation}"
        echo -e "\033[34m[INFO]\033[0m Started: ${start_time}"
        echo -e "\033[34m[INFO]\033[0m Completed steps: ${completed_count}"

        # List completed steps
        echo -e "\033[34m[INFO]\033[0m Completed steps:"
        jq -r '.completed_steps[] | "  - \(.name) (\(.timestamp))"' "${CHECKPOINT_FILE}"
    else
        echo -e "\033[34m[INFO]\033[0m Checkpoint log:"
        cat "${CHECKPOINT_FILE}.log" 2>/dev/null | head -10
    fi

    read -p "Resume from checkpoint? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0  # Resume
    else
        return 1  # Start fresh
    fi
}

# ========================================
# Function: Clear Checkpoints
# ========================================
checkpoint_clear() {
    if [ -d "${CHECKPOINT_DIR}" ]; then
        rm -rf "${CHECKPOINT_DIR}"
        echo -e "\033[32m[SUCCESS]\033[0m Checkpoints cleared"
    fi
}

# ========================================
# Function: Mark Operation Complete
# ========================================
checkpoint_complete() {
    if [ "${CHECKPOINT_ENABLED}" = "true" ] && [ -f "${CHECKPOINT_FILE}" ]; then
        local end_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        if command -v jq &>/dev/null; then
            local temp_file="${CHECKPOINT_FILE}.tmp"
            jq --arg time "${end_time}" \
               '.status = "completed" | .end_time = $time' \
               "${CHECKPOINT_FILE}" > "${temp_file}"
            mv "${temp_file}" "${CHECKPOINT_FILE}"
        fi

        echo -e "\033[32m[SUCCESS]\033[0m Operation completed, checkpoint saved"
    fi
}

# ========================================
# Function: Mark Operation Failed
# ========================================
checkpoint_fail() {
    local step_name="$1"
    local error_message="${2:-Unknown error}"

    if [ "${CHECKPOINT_ENABLED}" = "true" ] && [ -f "${CHECKPOINT_FILE}" ]; then
        local fail_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        if command -v jq &>/dev/null; then
            local temp_file="${CHECKPOINT_FILE}.tmp"
            jq --arg step "${step_name}" \
               --arg error "${error_message}" \
               --arg time "${fail_time}" \
               '.status = "failed" | .failed_step = $step | .error = $error | .fail_time = $time' \
               "${CHECKPOINT_FILE}" > "${temp_file}"
            mv "${temp_file}" "${CHECKPOINT_FILE}"
        else
            echo "${fail_time} - FAILED: ${step_name} - ${error_message}" >> "${CHECKPOINT_FILE}.log"
        fi

        echo -e "\033[31m[ERROR]\033[0m Failure recorded: ${step_name}"
        echo -e "\033[34m[INFO]\033[0m Checkpoint saved at: ${CHECKPOINT_FILE}"
    fi
}

# ========================================
# Function: Add Rollback Action
# ========================================
rollback_add() {
    local description="$1"
    local command="$2"

    ROLLBACK_STACK+=("${description}|${command}")
    echo -e "\033[34m[INFO]\033[0m Rollback action added: ${description}"
}

# ========================================
# Function: Execute Rollback
# ========================================
rollback_execute() {
    local reason="${1:-Manual rollback}"

    echo -e "\033[33m[WARNING]\033[0m Executing rollback: ${reason}"
    echo -e "\033[34m[INFO]\033[0m Rollback actions: ${#ROLLBACK_STACK[@]}"

    # Execute rollback actions in reverse order
    local idx=${#ROLLBACK_STACK[@]}
    while [ ${idx} -gt 0 ]; do
        idx=$((idx - 1))
        local entry="${ROLLBACK_STACK[${idx}]}"

        local description="${entry%%|*}"
        local command="${entry#*|}"

        echo -e "\033[34m[INFO]\033[0m Rolling back: ${description}"

        if eval "${command}"; then
            echo -e "\033[32m[SUCCESS]\033[0m   ✓ ${description}"
        else
            echo -e "\033[31m[ERROR]\033[0m   ✗ ${description} (rollback failed)"
        fi
    done

    echo -e "\033[32m[SUCCESS]\033[0m Rollback complete"

    # Clear rollback stack
    ROLLBACK_STACK=()
}

# ========================================
# Function: Clear Rollback Stack
# ========================================
rollback_clear() {
    ROLLBACK_STACK=()
    echo -e "\033[34m[INFO]\033[0m Rollback stack cleared"
}

# ========================================
# Function: Set Error Trap
# ========================================
recovery_trap() {
    local step_name="${1:-unknown_step}"

    trap 'recovery_error_handler "${step_name}" $? $LINENO' ERR
}

# ========================================
# Function: Error Handler
# ========================================
recovery_error_handler() {
    local step_name="$1"
    local exit_code="$2"
    local line_number="$3"

    echo -e "\033[31m[ERROR]\033[0m Error in step: ${step_name}"
    echo -e "\033[31m[ERROR]\033[0m Exit code: ${exit_code}"
    echo -e "\033[31m[ERROR]\033[0m Line: ${line_number}"

    # Save failure to checkpoint
    checkpoint_fail "${step_name}" "Exit code ${exit_code} at line ${line_number}"

    # Ask for rollback
    read -p "Execute rollback? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rollback_execute "Error recovery"
    fi

    exit "${exit_code}"
}

# ========================================
# Function: Safe Command Execution
# ========================================
recovery_safe_exec() {
    local description="$1"
    local command="$2"
    local rollback_command="${3:-}"

    echo -e "\033[34m[INFO]\033[0m Executing: ${description}"

    # Add rollback if provided
    if [ -n "${rollback_command}" ]; then
        rollback_add "${description}" "${rollback_command}"
    fi

    # Execute command
    if eval "${command}"; then
        echo -e "\033[32m[SUCCESS]\033[0m   ✓ ${description}"
        checkpoint_save "${description}"
        return 0
    else
        local exit_code=$?
        echo -e "\033[31m[ERROR]\033[0m   ✗ ${description} (exit code: ${exit_code})"
        checkpoint_fail "${description}" "Exit code ${exit_code}"
        return ${exit_code}
    fi
}
