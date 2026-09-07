#!/usr/bin/env bash
# Oryvex Research — start/stop the store. Never fails with "address in use".
#
#   ./run.sh          foreground with --reload  (Ctrl+C to stop)
#   ./run.sh bg       background, logs to server.log
#   ./run.sh stop     stop it
#   ./run.sh status   what's running, on which port
#   PORT=8020 ./run.sh
set -uo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8012}"
APP="backend.main:app"
PY="$([ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)"

# PID listening on $1, via ss (fall back to lsof, then fuser).
port_pid() {
  local p
  p=$(ss -ltnpH "sport = :$1" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1)
  [ -z "$p" ] && p=$(lsof -tiTCP:"$1" -sTCP:LISTEN 2>/dev/null | head -1)
  [ -z "$p" ] && p=$(fuser -n tcp "$1" 2>/dev/null | tr -d ' ' | head -1)
  echo "$p"
}

# Is this PID our own server? True for the uvicorn parent AND for the worker
# that `--reload` forks (whose cmdline is a multiprocessing spawn line, but
# whose cwd is still this project).
is_ours() {
  [ -n "${1:-}" ] || return 1
  local cmd cwd
  cmd=$(tr '\0' ' ' < "/proc/$1/cmdline" 2>/dev/null)
  echo "$cmd" | grep -q "uvicorn.*${APP}" && return 0
  cwd=$(readlink -f "/proc/$1/cwd" 2>/dev/null)
  [ "$cwd" = "$PWD" ] && echo "$cmd" | grep -q "python" && return 0
  return 1
}

# Walk up to the process that actually owns the server, so killing a --reload
# worker doesn't just make its parent respawn one.
owner_pid() {
  local pid=$1 ppid
  while :; do
    ppid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null)
    [ -z "$ppid" ] || [ "$ppid" = "1" ] && break
    is_ours "$ppid" || break
    pid=$ppid
  done
  echo "$pid"
}

# Free $PORT if we own it. If a foreign process holds it, hop to the next
# free port instead of dying — the point is that starting always works.
claim_port() {
  local pid tries=0
  while [ $tries -lt 20 ]; do
    pid=$(port_pid "$PORT")
    if [ -z "$pid" ]; then return 0; fi                 # free
    if is_ours "$pid"; then
      pid=$(owner_pid "$pid")
      echo "→ replacing our server on :$PORT (pid $pid)"
      kill "$pid" 2>/dev/null
      for _ in $(seq 1 20); do
        [ -z "$(port_pid "$PORT")" ] && return 0
        sleep 0.25
      done
      kill -9 "$pid" 2>/dev/null; sleep 0.5
      [ -z "$(port_pid "$PORT")" ] && return 0
    fi
    echo "→ :$PORT held by another program (pid ${pid:-?}) — trying $((PORT+1))"
    PORT=$((PORT+1)); tries=$((tries+1))
  done
  echo "✗ no free port found in range"; exit 1
}

wait_up() {
  for _ in $(seq 1 60); do
    curl -sf -o /dev/null "http://127.0.0.1:${PORT}/" && return 0
    sleep 0.5
  done
  return 1
}

case "${1:-fg}" in
  stop)
    pid=$(port_pid "$PORT")
    if is_ours "$pid"; then kill "$pid" 2>/dev/null; sleep 1; fi
    pkill -f "uvicorn ${APP}" 2>/dev/null
    sleep 1
    echo "✓ stopped — :$PORT $( [ -z "$(port_pid "$PORT")" ] && echo free || echo 'still held by another program')"
    ;;
  status)
    pid=$(port_pid "$PORT")
    if [ -z "$pid" ]; then echo ":$PORT free"
    elif is_ours "$pid"; then echo "✓ Oryvex running on :$PORT (pid $pid)"
    else echo "✗ :$PORT held by a different program (pid $pid)"; fi
    ;;
  bg)
    claim_port
    setsid nohup "$PY" -m uvicorn "$APP" --host 127.0.0.1 --port "$PORT" \
      > server.log 2>&1 < /dev/null &
    if wait_up; then
      echo "✓ http://127.0.0.1:${PORT}   (logs: server.log · stop: ./run.sh stop)"
    else
      echo "✗ failed to start — last lines of server.log:"; tail -15 server.log; exit 1
    fi
    ;;
  *)
    claim_port
    echo "✓ starting on http://127.0.0.1:${PORT}   (Ctrl+C to stop)"
    exec "$PY" -m uvicorn "$APP" --host 127.0.0.1 --port "$PORT" --reload
    ;;
esac
