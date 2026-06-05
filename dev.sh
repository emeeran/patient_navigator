#!/usr/bin/env bash
# Patient Navigator — Full-stack dev server
# Usage: ./dev.sh          — start everything
#        ./dev.sh stop     — stop everything
#        ./dev.sh status   — show process status

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.dev-pids"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31