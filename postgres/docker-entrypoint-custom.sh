#!/bin/bash
# ============================================================================
# PostgreSQL Custom Entrypoint - Always-Run Migrations
# ============================================================================
# Purpose: Run schema updates on EVERY container start (not just first time)
# Execution: Wraps official postgres entrypoint
# ============================================================================

set -e

echo "============================================"
echo "🔄 Blacklist PostgreSQL Custom Entrypoint"
echo "============================================"

# ============================================================================
# STEP 1: Start PostgreSQL in background for migrations
# ============================================================================
if [ "$1" = 'postgres' ]; then
    echo "🚀 Starting PostgreSQL for migrations..."

    # Wait for PostgreSQL to be ready
    export PGPASSWORD="${POSTGRES_PASSWORD:-postgres}"

    # Function to check if PostgreSQL is ready
    wait_for_postgres() {
        local max_attempts=30
        local attempt=0

        until pg_isready -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-blacklist}" > /dev/null 2>&1; do
            attempt=$((attempt + 1))
            if [ $attempt -ge $max_attempts ]; then
                echo "❌ PostgreSQL failed to start after ${max_attempts} attempts"
                return 1
            fi
            echo "⏳ Waiting for PostgreSQL to be ready (attempt $attempt/$max_attempts)..."
            sleep 1
        done

        echo "✅ PostgreSQL is ready"
        return 0
    }

    # ============================================================================
    # STEP 2: Run migrations if /migrations directory exists
    # ============================================================================
    if [ -d "/migrations" ] && [ "$(ls -A /migrations/*.sql 2>/dev/null)" ]; then
        echo ""
        echo "🔍 Found migrations directory"
        echo "📁 Path: /migrations"
        echo ""

        # Start postgres in background temporarily
        docker-entrypoint.sh postgres &
        PG_PID=$!

        # Wait for PostgreSQL to accept connections
        wait_for_postgres

        echo ""
        echo "============================================"
        echo "🔄 Running Database Migrations"
        echo "============================================"

        # Run all migration files in order
        for migration in /migrations/*.sql; do
            if [ -f "$migration" ]; then
                filename=$(basename "$migration")
                echo ""
                echo "▶️  Executing: $filename"
                echo "-------------------------------------------"

                if psql -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-blacklist}" -f "$migration" 2>&1 | grep -v "^$"; then
                    echo "✅ $filename completed successfully"
                else
                    echo "❌ $filename failed"
                fi
                echo "-------------------------------------------"
            fi
        done

        echo ""
        echo "============================================"
        echo "✅ All migrations completed"
        echo "============================================"
        echo ""

        # Stop temporary postgres
        kill $PG_PID
        wait $PG_PID 2>/dev/null || true

        # Small delay to ensure clean shutdown
        sleep 2
    else
        echo "ℹ️  No migrations found in /migrations"
    fi

    # ============================================================================
    # STEP 3: Start PostgreSQL normally (foreground)
    # ============================================================================
    echo ""
    echo "🚀 Starting PostgreSQL in production mode..."
    echo "============================================"
    echo ""
fi

# Execute original entrypoint
exec docker-entrypoint.sh "$@"
