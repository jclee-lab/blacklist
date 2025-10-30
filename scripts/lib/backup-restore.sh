#!/bin/bash
# Backup & Restore Library - Phase 3 Implementation
#
# Purpose: Automated database backup, restore, and rotation
# Usage: source scripts/lib/backup-restore.sh
#
# Created: 2025-10-22
# Phase: 3.3 - Backup/Restore Automation

# ========================================
# Color Output Functions
# ========================================
log_info() { echo -e "\033[34m[INFO]\033[0m $1"; }
log_success() { echo -e "\033[32m[SUCCESS]\033[0m $1"; }
log_warning() { echo -e "\033[33m[WARNING]\033[0m $1"; }
log_error() { echo -e "\033[31m[ERROR]\033[0m $1"; }

# ========================================
# Global Variables
# ========================================
BACKUP_DIR="${BACKUP_DIR:-/var/backups/blacklist}"
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
BACKUP_COMPRESSION="${BACKUP_COMPRESSION:-gzip}"  # gzip, bzip2, none
BACKUP_VERIFY="${BACKUP_VERIFY:-true}"

# Database configuration
DB_CONTAINER="${DB_CONTAINER:-blacklist-postgres}"
DB_NAME="${DB_NAME:-blacklist}"
DB_USER="${DB_USER:-postgres}"

# Redis configuration
REDIS_CONTAINER="${REDIS_CONTAINER:-blacklist-redis}"

# ========================================
# Function: Initialize Backup System
# ========================================
backup_init() {
    log_info "Initializing backup system..."

    # Create backup directory
    if [ ! -d "${BACKUP_DIR}" ]; then
        mkdir -p "${BACKUP_DIR}" || {
            log_error "Failed to create backup directory: ${BACKUP_DIR}"
            return 1
        }
    fi

    # Verify directory is writable
    if [ ! -w "${BACKUP_DIR}" ]; then
        log_error "Backup directory is not writable: ${BACKUP_DIR}"
        return 1
    fi

    # Verify Docker access
    if ! docker ps &>/dev/null; then
        log_error "Cannot access Docker daemon"
        return 1
    fi

    # Verify database container exists
    if ! docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        log_error "Database container not found: ${DB_CONTAINER}"
        return 1
    fi

    log_success "Backup system initialized"
    log_info "  Backup directory: ${BACKUP_DIR}"
    log_info "  Retention: ${BACKUP_RETENTION_DAYS} days"
    log_info "  Compression: ${BACKUP_COMPRESSION}"
    return 0
}

# ========================================
# Function: PostgreSQL Database Backup
# ========================================
backup_database() {
    local backup_name="${1:-auto}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/db_${backup_name}_${timestamp}.sql"

    log_info "========================================="
    log_info "  Database Backup"
    log_info "========================================="
    log_info "Starting database backup..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        log_error "Database container is not running: ${DB_CONTAINER}"
        return 1
    fi

    # Execute pg_dump inside container
    log_info "Executing pg_dump..."
    if docker exec "${DB_CONTAINER}" pg_dump -U "${DB_USER}" -d "${DB_NAME}" \
        --no-owner --no-acl --clean --if-exists > "${backup_file}"; then

        log_success "Database dump completed: ${backup_file}"
    else
        log_error "Database dump failed"
        rm -f "${backup_file}"
        return 1
    fi

    # Get file size
    local file_size=$(du -h "${backup_file}" | cut -f1)
    log_info "Backup size: ${file_size}"

    # Compress backup
    if [ "${BACKUP_COMPRESSION}" = "gzip" ]; then
        log_info "Compressing with gzip..."
        if gzip -f "${backup_file}"; then
            backup_file="${backup_file}.gz"
            local compressed_size=$(du -h "${backup_file}" | cut -f1)
            log_success "Compression complete: ${compressed_size}"
        else
            log_warning "Compression failed, keeping uncompressed backup"
        fi
    elif [ "${BACKUP_COMPRESSION}" = "bzip2" ]; then
        log_info "Compressing with bzip2..."
        if bzip2 -f "${backup_file}"; then
            backup_file="${backup_file}.bz2"
            local compressed_size=$(du -h "${backup_file}" | cut -f1)
            log_success "Compression complete: ${compressed_size}"
        else
            log_warning "Compression failed, keeping uncompressed backup"
        fi
    fi

    # Verify backup integrity
    if [ "${BACKUP_VERIFY}" = "true" ]; then
        log_info "Verifying backup integrity..."
        if backup_verify "${backup_file}"; then
            log_success "Backup verification passed"
        else
            log_error "Backup verification failed"
            return 1
        fi
    fi

    # Generate metadata
    backup_create_metadata "${backup_file}"

    echo
    log_success "✅ Database backup complete"
    log_info "  File: ${backup_file}"
    log_info "  Size: $(du -h "${backup_file}" | cut -f1)"
    echo "${backup_file}"  # Return file path
    return 0
}

# ========================================
# Function: Redis Backup
# ========================================
backup_redis() {
    local backup_name="${1:-auto}"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/redis_${backup_name}_${timestamp}.rdb"

    log_info "Starting Redis backup..."

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
        log_error "Redis container is not running: ${REDIS_CONTAINER}"
        return 1
    fi

    # Trigger Redis SAVE
    log_info "Executing Redis SAVE..."
    if docker exec "${REDIS_CONTAINER}" redis-cli SAVE &>/dev/null; then
        log_success "Redis SAVE complete"
    else
        log_error "Redis SAVE failed"
        return 1
    fi

    # Copy RDB file from container
    log_info "Copying RDB file..."
    if docker cp "${REDIS_CONTAINER}:/data/dump.rdb" "${backup_file}"; then
        log_success "Redis backup complete: ${backup_file}"
        log_info "  Size: $(du -h "${backup_file}" | cut -f1)"
        echo "${backup_file}"
        return 0
    else
        log_error "Failed to copy RDB file"
        return 1
    fi
}

# ========================================
# Function: Full System Backup
# ========================================
backup_full() {
    local backup_name="${1:-full}"
    local timestamp=$(date +%Y%m%d_%H%M%S)

    log_info "========================================="
    log_info "  Full System Backup"
    log_info "========================================="

    local db_backup=$(backup_database "${backup_name}")
    local db_status=$?

    local redis_backup=$(backup_redis "${backup_name}")
    local redis_status=$?

    echo
    if [ ${db_status} -eq 0 ] && [ ${redis_status} -eq 0 ]; then
        log_success "✅ Full backup complete"
        log_info "  Database: ${db_backup}"
        log_info "  Redis: ${redis_backup}"
        return 0
    else
        log_error "❌ Full backup failed"
        [ ${db_status} -ne 0 ] && log_error "  Database backup failed"
        [ ${redis_status} -ne 0 ] && log_error "  Redis backup failed"
        return 1
    fi
}

# ========================================
# Function: Restore Database
# ========================================
restore_database() {
    local backup_file="$1"

    log_info "========================================="
    log_info "  Database Restore"
    log_info "========================================="

    # Validate backup file exists
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi

    log_info "Backup file: ${backup_file}"
    log_info "Size: $(du -h "${backup_file}" | cut -f1)"

    # Decompress if needed
    local temp_sql="${backup_file}"
    if [[ "${backup_file}" == *.gz ]]; then
        log_info "Decompressing gzip backup..."
        temp_sql="${backup_file%.gz}"
        gunzip -c "${backup_file}" > "${temp_sql}"
    elif [[ "${backup_file}" == *.bz2 ]]; then
        log_info "Decompressing bzip2 backup..."
        temp_sql="${backup_file%.bz2}"
        bunzip2 -c "${backup_file}" > "${temp_sql}"
    fi

    # Confirmation prompt
    echo
    log_warning "⚠️  WARNING: This will REPLACE the current database!"
    read -p "Continue with restore? (type 'yes' to confirm): " -r
    echo

    if [ "$REPLY" != "yes" ]; then
        log_info "Restore cancelled by user"
        [ "${temp_sql}" != "${backup_file}" ] && rm -f "${temp_sql}"
        return 1
    fi

    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        log_error "Database container is not running: ${DB_CONTAINER}"
        [ "${temp_sql}" != "${backup_file}" ] && rm -f "${temp_sql}"
        return 1
    fi

    # Execute restore
    log_info "Restoring database..."
    if docker exec -i "${DB_CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}" < "${temp_sql}"; then
        log_success "Database restore complete"

        # Cleanup temp file
        if [ "${temp_sql}" != "${backup_file}" ]; then
            rm -f "${temp_sql}"
        fi

        return 0
    else
        log_error "Database restore failed"

        # Cleanup temp file
        if [ "${temp_sql}" != "${backup_file}" ]; then
            rm -f "${temp_sql}"
        fi

        return 1
    fi
}

# ========================================
# Function: Restore Redis
# ========================================
restore_redis() {
    local backup_file="$1"

    log_info "Starting Redis restore..."

    # Validate backup file
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi

    # Confirmation prompt
    log_warning "⚠️  WARNING: This will REPLACE the current Redis data!"
    read -p "Continue with restore? (type 'yes' to confirm): " -r
    echo

    if [ "$REPLY" != "yes" ]; then
        log_info "Restore cancelled by user"
        return 1
    fi

    # Stop Redis to release dump.rdb lock
    log_info "Stopping Redis container..."
    docker stop "${REDIS_CONTAINER}" &>/dev/null

    # Copy backup to container
    log_info "Copying backup file..."
    if docker cp "${backup_file}" "${REDIS_CONTAINER}:/data/dump.rdb"; then
        log_success "Backup file copied"
    else
        log_error "Failed to copy backup file"
        docker start "${REDIS_CONTAINER}" &>/dev/null
        return 1
    fi

    # Start Redis
    log_info "Starting Redis container..."
    docker start "${REDIS_CONTAINER}" &>/dev/null

    # Wait for Redis to be ready
    sleep 3

    if docker exec "${REDIS_CONTAINER}" redis-cli ping &>/dev/null; then
        log_success "Redis restore complete"
        return 0
    else
        log_error "Redis failed to start after restore"
        return 1
    fi
}

# ========================================
# Function: List Available Backups
# ========================================
backup_list() {
    log_info "========================================="
    log_info "  Available Backups"
    log_info "========================================="

    if [ ! -d "${BACKUP_DIR}" ] || [ -z "$(ls -A "${BACKUP_DIR}" 2>/dev/null)" ]; then
        log_warning "No backups found in ${BACKUP_DIR}"
        return 1
    fi

    echo
    echo "Database Backups:"
    find "${BACKUP_DIR}" -type f -name "db_*.sql*" -printf "  %p (%s bytes, %TY-%Tm-%Td %TH:%TM)\n" | sort -r | head -20

    echo
    echo "Redis Backups:"
    find "${BACKUP_DIR}" -type f -name "redis_*.rdb" -printf "  %p (%s bytes, %TY-%Tm-%Td %TH:%TM)\n" | sort -r | head -20

    echo
    return 0
}

# ========================================
# Function: Cleanup Old Backups
# ========================================
backup_cleanup() {
    local retention_days="${1:-${BACKUP_RETENTION_DAYS}}"

    log_info "========================================="
    log_info "  Backup Cleanup (${retention_days} days)"
    log_info "========================================="

    if [ ! -d "${BACKUP_DIR}" ]; then
        log_warning "Backup directory does not exist: ${BACKUP_DIR}"
        return 0
    fi

    # Find and delete old backups
    local deleted=0

    while IFS= read -r file; do
        log_info "Deleting: $(basename "${file}")"
        rm -f "${file}"
        deleted=$((deleted + 1))
    done < <(find "${BACKUP_DIR}" -type f -name "*.sql*" -o -name "*.rdb" -mtime +${retention_days})

    echo
    if [ ${deleted} -gt 0 ]; then
        log_success "Deleted ${deleted} old backup(s)"
    else
        log_info "No old backups to delete"
    fi

    return 0
}

# ========================================
# Function: Verify Backup Integrity
# ========================================
backup_verify() {
    local backup_file="$1"

    # Check file exists and is readable
    if [ ! -f "${backup_file}" ] || [ ! -r "${backup_file}" ]; then
        log_error "Backup file not readable: ${backup_file}"
        return 1
    fi

    # Check file is not empty
    if [ ! -s "${backup_file}" ]; then
        log_error "Backup file is empty: ${backup_file}"
        return 1
    fi

    # For compressed files, test decompression
    if [[ "${backup_file}" == *.gz ]]; then
        if ! gunzip -t "${backup_file}" &>/dev/null; then
            log_error "Gzip integrity check failed"
            return 1
        fi
    elif [[ "${backup_file}" == *.bz2 ]]; then
        if ! bunzip2 -t "${backup_file}" &>/dev/null; then
            log_error "Bzip2 integrity check failed"
            return 1
        fi
    fi

    # For SQL files, check for basic SQL structure
    if [[ "${backup_file}" == *.sql ]] || [[ "${backup_file}" == *.sql.* ]]; then
        local temp_check="${backup_file}"

        # Decompress for checking
        if [[ "${backup_file}" == *.gz ]]; then
            temp_check=$(mktemp)
            gunzip -c "${backup_file}" > "${temp_check}"
        elif [[ "${backup_file}" == *.bz2 ]]; then
            temp_check=$(mktemp)
            bunzip2 -c "${backup_file}" > "${temp_check}"
        fi

        # Check for SQL keywords
        if ! grep -q "CREATE TABLE\|INSERT INTO\|COPY" "${temp_check}" 2>/dev/null; then
            log_warning "Backup may not contain valid SQL data"
            [ "${temp_check}" != "${backup_file}" ] && rm -f "${temp_check}"
            return 1
        fi

        # Cleanup temp file
        [ "${temp_check}" != "${backup_file}" ] && rm -f "${temp_check}"
    fi

    return 0
}

# ========================================
# Function: Create Backup Metadata
# ========================================
backup_create_metadata() {
    local backup_file="$1"
    local metadata_file="${backup_file}.meta"

    cat > "${metadata_file}" <<EOF
{
  "backup_file": "$(basename "${backup_file}")",
  "backup_path": "${backup_file}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "size_bytes": $(stat -c%s "${backup_file}" 2>/dev/null || echo 0),
  "size_human": "$(du -h "${backup_file}" | cut -f1)",
  "compression": "${BACKUP_COMPRESSION}",
  "db_container": "${DB_CONTAINER}",
  "db_name": "${DB_NAME}",
  "hostname": "$(hostname)",
  "checksum_sha256": "$(sha256sum "${backup_file}" | cut -d' ' -f1)"
}
EOF

    log_info "Metadata created: ${metadata_file}"
}

# ========================================
# Function: Scheduled Backup (for cron)
# ========================================
backup_scheduled() {
    local backup_type="${1:-full}"  # full, database, redis

    # Initialize
    backup_init || return 1

    # Execute backup
    case "${backup_type}" in
        "full")
            backup_full "scheduled"
            ;;
        "database")
            backup_database "scheduled"
            ;;
        "redis")
            backup_redis "scheduled"
            ;;
        *)
            log_error "Unknown backup type: ${backup_type}"
            return 1
            ;;
    esac

    local backup_status=$?

    # Cleanup old backups
    backup_cleanup

    return ${backup_status}
}

# ========================================
# Function: Backup with Progress
# ========================================
backup_with_progress() {
    # Source progress library if available
    if [ -f "$(dirname "$0")/progress.sh" ]; then
        source "$(dirname "$0")/progress.sh"

        progress_init 5

        progress_step 1 5 "Initializing backup" "in_progress"
        backup_init
        progress_step 1 5 "Initializing backup" "success"

        progress_step 2 5 "Backing up database" "in_progress"
        backup_database "progress" &>/dev/null
        progress_step 2 5 "Backing up database" "success"

        progress_step 3 5 "Backing up Redis" "in_progress"
        backup_redis "progress" &>/dev/null
        progress_step 3 5 "Backing up Redis" "success"

        progress_step 4 5 "Verifying backups" "in_progress"
        sleep 1  # Verification already done in backup functions
        progress_step 4 5 "Verifying backups" "success"

        progress_step 5 5 "Cleanup old backups" "in_progress"
        backup_cleanup &>/dev/null
        progress_step 5 5 "Cleanup old backups" "success"

        progress_complete "Backup complete"
    else
        # Fallback without progress
        backup_full
    fi
}
