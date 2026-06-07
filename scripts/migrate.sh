#!/usr/bin/env bash
# ── Safe Database Migration Runner ──────────────────
# Usage:
#   ./scripts/migrate.sh              # Apply pending migrations
#   ./scripts/migrate.sh --dry-run    # Show SQL without executing
#   ./scripts/migrate.sh --downgrade  # Roll back one migration
#
# Creates a backup before migrating (unless --dry-run).
# Verifies health endpoint after migration.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DRY_RUN=false
DOWNGRADE=false

for arg in "$@"; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --downgrade) DOWNGRADE=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# Load environment
if [ -f "$PROJECT_DIR/.env.production" ]; then
  source <(grep -v '^#' "$PROJECT_DIR/.env.production" | sed 's/^/export /')
elif [ -f "$PROJECT_DIR/backend/.env" ]; then
  source <(grep -v '^#' "$PROJECT_DIR/backend/.env" | sed 's/^/export /')
fi

cd "$PROJECT_DIR/backend"

if [ "$DRY_RUN" = true ]; then
  echo "=== DRY RUN: Showing SQL without executing ==="
  if [ "$DOWNGRADE" = true ]; then
    alembic downgrade -1 --sql
  else
    alembic upgrade head --sql
  fi
  exit 0
fi

# Create backup before real migration
echo "=== Creating pre-migration backup ==="
"$PROJECT_DIR/scripts/backup.sh"

if [ "$DOWNGRADE" = true ]; then
  echo "=== Rolling back one migration ==="
  alembic downgrade -1
else
  echo "=== Applying pending migrations ==="
  alembic upgrade head
fi

echo "=== Migration complete ==="
echo "Current revision:"
alembic current

# Verify health endpoint if backend is running
HEALTH_URL="${HEALTH_URL:-http://localhost:8000/health}"
if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
  echo "=== Health check: OK ==="
else
  echo "WARNING: Health check at $HEALTH_URL failed (backend may not be running)" >&2
fi
