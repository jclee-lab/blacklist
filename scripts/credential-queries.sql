-- Credential Management Queries
-- Run: docker exec blacklist-postgres psql -U postgres -d blacklist -f /path/to/this/file

-- ==========================================
-- 1. View all credentials (decrypted)
-- ==========================================
SELECT
    id,
    source,
    username,
    pgp_sym_decrypt(password::bytea, 'blacklist-secret-key-2024') as password,
    is_active,
    created_at,
    updated_at
FROM collection_credentials
ORDER BY source, created_at DESC;

-- ==========================================
-- 2. Add REGTECH credentials (INSERT)
-- ==========================================
INSERT INTO collection_credentials (source, username, password, is_active)
VALUES (
    'REGTECH',
    'YOUR_USERNAME',  -- Replace with actual username
    pgp_sym_encrypt('YOUR_PASSWORD', 'blacklist-secret-key-2024'),  -- Replace with actual password
    true
)
ON CONFLICT (source) DO UPDATE
SET
    username = EXCLUDED.username,
    password = EXCLUDED.password,
    is_active = true,
    updated_at = CURRENT_TIMESTAMP;

-- ==========================================
-- 3. Add SECUDIUM credentials (INSERT)
-- ==========================================
INSERT INTO collection_credentials (source, username, password, is_active)
VALUES (
    'SECUDIUM',
    'YOUR_USERNAME',  -- Replace with actual username
    pgp_sym_encrypt('YOUR_PASSWORD', 'blacklist-secret-key-2024'),  -- Replace with actual password
    true
)
ON CONFLICT (source) DO UPDATE
SET
    username = EXCLUDED.username,
    password = EXCLUDED.password,
    is_active = true,
    updated_at = CURRENT_TIMESTAMP;

-- ==========================================
-- 4. Update existing credentials
-- ==========================================
UPDATE collection_credentials
SET
    username = 'NEW_USERNAME',
    password = pgp_sym_encrypt('NEW_PASSWORD', 'blacklist-secret-key-2024'),
    updated_at = CURRENT_TIMESTAMP
WHERE source = 'REGTECH';  -- or 'SECUDIUM'

-- ==========================================
-- 5. Activate/Deactivate credentials
-- ==========================================
-- Deactivate
UPDATE collection_credentials SET is_active = false WHERE source = 'REGTECH';

-- Activate
UPDATE collection_credentials SET is_active = true WHERE source = 'REGTECH';

-- ==========================================
-- 6. Delete credentials
-- ==========================================
-- Delete specific source
DELETE FROM collection_credentials WHERE source = 'REGTECH';

-- Delete all
DELETE FROM collection_credentials;

-- ==========================================
-- 7. Quick verification (active only)
-- ==========================================
SELECT
    source,
    username,
    is_active,
    created_at
FROM collection_credentials
WHERE is_active = true;

-- ==========================================
-- Usage Examples
-- ==========================================

-- Example 1: Add REGTECH credentials
-- docker exec blacklist-postgres psql -U postgres -d blacklist << 'SQL'
-- INSERT INTO collection_credentials (source, username, password, is_active)
-- VALUES ('REGTECH', 'admin', pgp_sym_encrypt('password123', 'blacklist-secret-key-2024'), true)
-- ON CONFLICT (source) DO UPDATE SET username=EXCLUDED.username, password=EXCLUDED.password;
-- SQL

-- Example 2: View credentials
-- docker exec blacklist-postgres psql -U postgres -d blacklist -c \
--   "SELECT source, username, pgp_sym_decrypt(password::bytea, 'blacklist-secret-key-2024') FROM collection_credentials;"

-- Example 3: One-liner from host
-- export PGPASSWORD=postgres
-- docker exec -e PGPASSWORD blacklist-postgres psql -U postgres -d blacklist -c \
--   "INSERT INTO collection_credentials VALUES ('REGTECH', 'user', pgp_sym_encrypt('pass', 'blacklist-secret-key-2024'), true) \
--    ON CONFLICT (source) DO UPDATE SET password=EXCLUDED.password;"
