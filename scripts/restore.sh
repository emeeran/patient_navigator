#!/usr/bin/env bash
# ── Patient Navigator Database Restore ───────────────
# Usage: ./scripts/restore.sh <backup_file.sql.gz>
# Stops the backend, restores the database, then exits.
# Reads connection details from .env.production.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file.sql.gz>" >&2
    echo "Available backups:" >&2
    ls -1t "${PROJECT_DIR}/backups/"patient_nav_*.sql.gz 2>/dev/null || echo "  (none)" >&2
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: File not found: $BACKUP_FILE" >&2
    exit 1
fi

# Load environment
if [ -f "$PROJECT_DIR/.env.production" ]; then
    # shellcheck disable=SC1091
    source <(grep -v '^#' "$PROJECT_DIR/.env.production" | sed 's/^/export /')
else
    echo "ERROR: .env.production not found in $PROJECT_DIR" >&2
    exit 1
fi

if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "ERROR: POSTGRES_PASSWORD not set in .env.production" >&2
    exit 1
fi

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-patient_nav}"
DB_USER="${DB_USER:-navigator}"

echo "WARNING: This will REPLACE the $DB_NAME database!"
read -rp "Type 'yes' to continue: " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Stop backend if running via docker compose
if [ -f "$PROJECT_DIR/docker-compose.prod.yml" ]; then
    echo "Stopping backend..."
    docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" stop backend migrate
fi

echo "Restoring from $BACKUP_FILE ..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    --quiet

echo "Restore complete."

# Restart backend
if [ -f "$PROJECT_DIR/docker-compose.prod.yml" ]; then
    echo "Starting backend..."
    docker compose -f "$PROJECT_DIR/docker-compose.prod.yml" start backend
fi

echo "Done."
