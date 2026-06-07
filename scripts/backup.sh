#!/usr/bin/env bash
# ── Patient Navigator Database Backup ────────────────
# Usage: ./scripts/backup.sh
# Reads connection details from .env.production in the project root.
# Keeps the last 30 days of backups (configurable via RETENTION_DAYS).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment
if [ -f "$PROJECT_DIR/.env.production" ]; then
    # shellcheck disable=SC1091
    source <(grep -v '^#' "$PROJECT_DIR/.env.production" | sed 's/^/export /')
else
    echo "ERROR: .env.production not found in $PROJECT_DIR" >&2
    exit 1
fi

# Defaults
RETENTION_DAYS="${RETENTION_DAYS:-30}"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/patient_nav_${TIMESTAMP}.sql.gz"

# Parse DATABASE_URL if individual vars not set
if [ -z "${POSTGRES_PASSWORD:-}" ]; then
    echo "ERROR: POSTGRES_PASSWORD not set in .env.production" >&2
    exit 1
fi

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-patient_nav}"
DB_USER="${DB_USER:-navigator}"

mkdir -p "$BACKUP_DIR"

echo "Backing up $DB_NAME to $BACKUP_FILE ..."

PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-privileges \
    --clean \
    --if-exists \
    | gzip > "$BACKUP_FILE"

SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "Backup complete: $BACKUP_FILE ($SIZE)"

# Prune old backups
echo "Pruning backups older than $RETENTION_DAYS days ..."
find "$BACKUP_DIR" -name "patient_nav_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete
echo "Done."
