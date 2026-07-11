#!/usr/bin/env bash
# Opportunity Radar — one-command start (Linux/macOS)
# Usage: ./start.sh          Start everything
#        ./start.sh --stop   Stop Docker + local frontend
#        ./start.sh --help   Show help

set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

STATE_DIR="$ROOT/.radar"
FRONTEND_PID="$STATE_DIR/frontend.pid"
FRONTEND_LOG="$STATE_DIR/frontend.log"
FRONTEND_ENV="$ROOT/frontend/.env.local"

step()  { echo ""; echo ">> $*"; }
ok()    { echo "   OK: $*"; }
warn()  { echo "   WARN: $*"; }
die()   { echo "   ERROR: $*" >&2; exit 1; }

show_help() {
  cat <<'EOF'
Opportunity Radar — start script

  ./start.sh          Start Postgres + backend (Docker) and frontend (local dev)
  ./start.sh --stop     Stop all services
  ./start.sh --help     Show this help

Opens http://localhost:3000 when ready. API docs at http://localhost:8000/docs
Scraper controls live in the UI at /admin (passphrase from ADMIN_PASSWORD in .env).
EOF
}

port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -tlnH "sport = :$port" 2>/dev/null | grep -q .
    return
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -i ":$port" >/dev/null 2>&1
    return
  fi
  (echo >/dev/tcp/127.0.0.1/"$port") 2>/dev/null
}

container_state() {
  docker compose ps "$1" --format '{{.State}}' 2>/dev/null || true
}

show_backend_logs() {
  echo "" >&2
  echo "   --- backend logs (last 30 lines) ---" >&2
  docker compose logs backend --tail 30 >&2 || true
  echo "   ------------------------------------" >&2
}

wait_backend() {
  step "Waiting for backend (http://localhost:8000/api/v1/health)"
  local attempt=1
  local max=45
  while [ "$attempt" -le "$max" ]; do
    if curl -sf http://localhost:8000/api/v1/health >/dev/null 2>&1; then
      ok "Backend healthy"
      return 0
    fi

    local state
    state=$(container_state backend)
    case "$state" in
      exited|dead)
        show_backend_logs
        die "Backend container crashed — see logs above"
        ;;
      restarting)
        printf "."
        ;;
      *)
        if [ $((attempt % 5)) -eq 0 ]; then
          printf " [%ss]" "$((attempt * 2))"
        else
          printf "."
        fi
        ;;
    esac

    attempt=$((attempt + 1))
    sleep 2
  done

  echo ""
  show_backend_logs
  die "Backend not healthy after $((max * 2))s — is Docker running? Try: docker compose logs backend"
}

wait_url() {
  local url="$1" label="$2" max="${3:-60}"
  step "Waiting for $label"
  local attempt=1
  while [ "$attempt" -le "$max" ]; do
    if curl -sf "$url" >/dev/null 2>&1; then
      ok "$label ready"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 2
  done
  die "$label did not become ready ($url)"
}

ensure_env() {
  if [[ ! -f .env ]]; then
    warn ".env missing — creating from .env.example"
    cp .env.example .env
    ok "Created .env (edit ADMIN_PASSWORD before using /admin)"
  fi
  if grep -q '^NEXT_PUBLIC_API_URL=' .env 2>/dev/null; then
    grep '^NEXT_PUBLIC_API_URL=' .env > "$FRONTEND_ENV"
  elif [[ ! -f "$FRONTEND_ENV" ]]; then
    echo 'NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1' > "$FRONTEND_ENV"
  fi
}

ensure_docker() {
  command -v docker >/dev/null || die "Docker not installed"
  docker info >/dev/null 2>&1 || die "Docker daemon not running — start Docker and retry"
}

start_docker() {
  step "Starting Postgres + backend (Docker)"
  # Recreate backend if a previous run left it in a crashed state
  local state
  state=$(container_state backend)
  if [ "$state" = "exited" ] || [ "$state" = "dead" ]; then
    warn "Removing crashed backend container"
    docker compose rm -f backend >/dev/null 2>&1 || true
  fi
  docker compose up -d --build postgres backend
  ok "Docker services starting"
}

frontend_needs_install() {
  [[ ! -d frontend/node_modules ]] && return 0
  local swc
  swc=$(find frontend/node_modules/@next -maxdepth 2 -name 'swc-linux-*' -o -name 'swc-darwin-*' 2>/dev/null | head -1)
  [[ -z "$swc" ]]
}

start_frontend() {
  command -v npm >/dev/null || die "Node.js/npm not found — install Node 20+ for the frontend"

  if port_in_use 3000; then
    if curl -sf http://localhost:3000 >/dev/null 2>&1; then
      ok "Frontend already running on http://localhost:3000"
      return 0
    fi
    die "Port 3000 is in use but not responding — free the port or run ./start.sh --stop"
  fi

  step "Preparing frontend"
  if frontend_needs_install; then
    warn "Installing frontend dependencies (required on first run or after OS change)"
    (cd frontend && npm install)
  else
    ok "Frontend dependencies OK"
  fi

  mkdir -p "$STATE_DIR"
  : > "$FRONTEND_LOG"

  step "Starting frontend dev server"
  (
    cd frontend
    export HOSTNAME=0.0.0.0
    nohup npm run dev >>"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID"
  )
  ok "Frontend PID $(cat "$FRONTEND_PID") — log: $FRONTEND_LOG"

  wait_url "http://localhost:3000" "frontend" 90
}

stop_frontend() {
  if [[ -f "$FRONTEND_PID" ]]; then
    local pid
    pid=$(cat "$FRONTEND_PID")
    if kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
      sleep 1
      kill -9 "$pid" 2>/dev/null || true
      ok "Stopped frontend (PID $pid)"
    fi
    rm -f "$FRONTEND_PID"
  fi
}

stop_all() {
  step "Stopping services"
  stop_frontend
  docker compose --profile full down 2>/dev/null || docker compose down
  ok "Stopped"
}

print_summary() {
  local health=""
  health=$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null || true)
  echo ""
  echo "  RADAR ONLINE"
  echo "  Dashboard : http://localhost:3000"
  echo "  API docs  : http://localhost:8000/docs"
  if [[ -n "$health" ]]; then
    echo "  Backend   : $health"
  fi
  echo ""
  echo "  Scraper controls: http://localhost:3000/admin"
  echo "  Stop everything : ./start.sh --stop"
  echo "  Frontend log    : $FRONTEND_LOG"
  echo ""
}

case "${1:-}" in
  -h|--help) show_help; exit 0 ;;
  --stop)    stop_all; exit 0 ;;
  "")        ;;
  *)         die "Unknown option: $1 (try --help)" ;;
esac

echo ""
echo "  OPPORTUNITY RADAR"
echo ""

ensure_env
ensure_docker
start_docker
wait_backend
start_frontend
print_summary

echo "Press Ctrl+C to exit this script (frontend keeps running). Use ./start.sh --stop to shut down."
