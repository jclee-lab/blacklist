#!/bin/bash
set -euo pipefail

CONTAINER="blacklist-postgres"
DB_NAME="blacklist"
DB_USER="postgres"

# PostgreSQL 비밀번호 가져오기
if [ -f .env ]; then
    PGPASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
else
    PGPASSWORD="postgres"
fi
export PGPASSWORD

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Credential Management"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 메뉴
echo "Select operation:"
echo "  [1] View credentials (decrypted)"
echo "  [2] Add REGTECH credentials"
echo "  [3] Add SECUDIUM credentials"
echo "  [4] Delete all credentials"
echo "  [0] Exit"
echo ""
read -p "Choice: " choice

case $choice in
    1)
        echo ""
        echo "📊 Current credentials:"
        docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'SQL'
SELECT
    id,
    source,
    username,
    pgp_sym_decrypt(password::bytea, 'blacklist-secret-key-2024') as password,
    is_active,
    created_at
FROM collection_credentials
ORDER BY source, created_at DESC;
SQL
        ;;

    2)
        echo ""
        echo "➕ Add REGTECH credentials"
        read -p "Username: " username
        read -sp "Password: " password
        echo ""

        docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << SQL
INSERT INTO collection_credentials (source, username, password, is_active)
VALUES (
    'REGTECH',
    '$username',
    pgp_sym_encrypt('$password', 'blacklist-secret-key-2024'),
    true
)
ON CONFLICT (source) DO UPDATE
SET
    username = EXCLUDED.username,
    password = EXCLUDED.password,
    is_active = true,
    updated_at = CURRENT_TIMESTAMP;
SQL

        if [ $? -eq 0 ]; then
            echo "✅ REGTECH credentials saved"
        else
            echo "❌ Failed to save credentials"
        fi
        ;;

    3)
        echo ""
        echo "➕ Add SECUDIUM credentials"
        read -p "Username: " username
        read -sp "Password: " password
        echo ""

        docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << SQL
INSERT INTO collection_credentials (source, username, password, is_active)
VALUES (
    'SECUDIUM',
    '$username',
    pgp_sym_encrypt('$password', 'blacklist-secret-key-2024'),
    true
)
ON CONFLICT (source) DO UPDATE
SET
    username = EXCLUDED.username,
    password = EXCLUDED.password,
    is_active = true,
    updated_at = CURRENT_TIMESTAMP;
SQL

        if [ $? -eq 0 ]; then
            echo "✅ SECUDIUM credentials saved"
        else
            echo "❌ Failed to save credentials"
        fi
        ;;

    4)
        echo ""
        read -p "⚠️  Delete ALL credentials? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            docker exec -e PGPASSWORD="$PGPASSWORD" "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" << 'SQL'
DELETE FROM collection_credentials;
SQL
            echo "✅ All credentials deleted"
        else
            echo "❌ Cancelled"
        fi
        ;;

    0)
        echo "Bye!"
        exit 0
        ;;

    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
