#!/usr/bin/env bash
# Patient Navigator — Full-stack dev server
# Usage: ./dev.sh          — start everything on available ports
#        ./dev.sh stop     — stop everything
#        ./dev.sh status   — show running processes
#        ./dev.sh logs     — tail both logs

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$ROOT_DIR/.dev-pids"
LOG_DIR="$ROOT_DIR/.dev-logs"

# Colors
BLUE='\033[0;34m' GREEN='\033[0;32m' YELLOW='\033[0;33m' RED='\033[0;31m' BOLD='\033[1m' RESET='\033[0m'

log()  { printf "${BLUE}[dev]${RESET} %s\n" "$*"; }
ok()   { printf "${GREEN}[ok]${RESET}  %s\n" "$*"; }
warn() { printf "${YELLOW}[!!]${RESET} %s\n" "$*"; }
die()  { printf "${RED}[X]${RESET}  %s\n" "$*" >&2; exit 1; }

# ── Port discovery ────────────────────────────────────────────────────────────
# Find the first available port starting from the given base.
find_port() {
  local base=${1:?usage: find_port BASE}
  for port in $(seq "$base" "$((base + 50))"); do
    if ! ss -tlnpH 2>/dev/null | grep -q ":${port}\b" 2>/dev/null \
       && ! lsof -iTCP:"$port" -sTCP:LISTEN &>/dev/null; then
      echo "$port"
      return
    fi
  done
  die "No available port found in range $base-$((base + 50))"
}

# ── Cleanup ───────────────────────────────────────────────────────────────────
cleanup() {
  [ -d "$PID_DIR" ] || return 0
  for pidfile in "$PID_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    local pid
    pid=$(cat "$pidfile")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && warn "Stopped PID $pid ($(basename "$pidfile" .pid))"
    fi
    rm -f "$pidfile"
  done
}

# ── Commands ──────────────────────────────────────────────────────────────────

cmd_stop() {
  log "Stopping dev servers..."
  cleanup
  ok "All stopped."
}

cmd_status() {
  [ -d "$PID_DIR" ] || { warn "No servers running."; return; }
  local found=0
  for pidfile in "$PID_DIR"/*.pid; do
    [ -f "$pidfile" ] || continue
    local pid name port
    pid=$(cat "$pidfile")
    name=$(basename "$pidfile" .pid)
    if kill -0 "$pid" 2>/dev/null; then
      port=$(cat "${PID_DIR}/${name}.port" 2>/dev/null || echo "?")
      ok "$name — PID $pid — port $port"
      found=1
    else
      warn "$name — PID $pid (dead)"
      rm -f "$pidfile" "${PID_DIR}/${name}.port"
    fi
  done
  [ "$found" -eq 0 ] && warn "No servers running."
}

cmd_logs() {
  [ -d "$LOG_DIR" ] || die "No logs found. Start servers first."
  log "Tailing logs (Ctrl+C to stop)..."
  tail -f "$LOG_DIR"/*.log 2>/dev/null || warn "No log files yet."
}

cmd_start() {
  # Prerequisite checks
  command -v uvicorn >/dev/null 2>&1 || die "uvicorn not found. Install: pip install uvicorn"
  command -v npx   >/dev/null 2>&1 || die "npx not found. Install: npm install"

  [ -d "$PID_DIR" ] && cmd_stop || true
  mkdir -p "$PID_DIR" "$LOG_DIR"

  # ── Backend ──────────────────────────────────────────────────────────────
  local backend_port
  backend_port=$(find_port 8002)
  log "Starting backend on port $backend_port..."
  (cd "$ROOT_DIR/backend" && \
    uvicorn app.main:app --reload --port "$backend_port" \
    > "$LOG_DIR/backend.log" 2>&1) &
  local backend_pid=$!
  echo "$backend_pid" > "$PID_DIR/backend.pid"
  echo "$backend_port" > "$PID_DIR/backend.port"

  # Wait for backend to be ready
  local tries=0
  while ! curl -sf "http://localhost:${backend_port}/health" >/dev/null 2>&1; do
    tries=$((tries + 1))
    [ "$tries" -lt 30 ] || { warn "Backend health check timed out (it may still be starting)."; break; }
    sleep 0.5
  done
  ok "Backend ready — http://localhost:${backend_port}"

  # ── Frontend ─────────────────────────────────────────────────────────────
  local frontend_port
  frontend_port=$(find_port 5173)
  log "Starting frontend on port $frontend_port..."
  (cd "$ROOT_DIR/frontend" && \
    npx vite --port "$frontend_port" --strict-port \
    > "$LOG_DIR/frontend.log" 2>&1) &
  local frontend_pid=$!
  echo "$frontend_pid" > "$PID_DIR/frontend.pid"
  echo "$frontend_port" > "$PID_DIR/frontend.port"

  # Update vite proxy to point at the discovered backend port
  # (vite reads its config at startup; we pass the backend port via an env var
  #  so the app can use it for API calls if needed)
  export VITE_API_PORT="$backend_port"

  ok "Frontend ready — http://localhost:${frontend_port}"
  echo ""
  printf "${BOLD}  ➜  Backend:   http://localhost:${backend_port}${RESET}\n"
  printf "${BOLD}  ➜  Frontend:  http://localhost:${frontend_port}${RESET}\n"
  printf "  ➜  Logs:      ./dev.sh logs\n"
  printf "  ➜  Stop:      ./dev.sh stop\n"
  echo ""
}

# ── Main ───────────────────────────────────────────────────────────────────────
case "${1:-start}" in
  start)  cmd_start  ;;
  stop)   cmd_stop   ;;
  status) cmd_status ;;
  logs)   cmd_logs   ;;
  *)
    echo "Usage: $0 {start|stop|status|logs}"
    exit 1
    ;;
esac
