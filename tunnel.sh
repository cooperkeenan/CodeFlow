#!/bin/bash
# Control script for the phone-access tunnel (Vite dev server + Cloudflare quick tunnel).
# Processes are launched detached so they survive terminal/session resets.
# Usage: ./tunnel.sh {start|stop|restart|url|status}

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_DIR="$ROOT_DIR/.tunnel"
mkdir -p "$RUN_DIR"

VITE_LOG="$RUN_DIR/vite.log"
CF_LOG="$RUN_DIR/cloudflared.log"
URL_FILE="$RUN_DIR/url.txt"

_vite_pid() { lsof -ti :5173 2>/dev/null; }
_cf_pid()   { pgrep -f "cloudflared tunnel --url http://localhost:5173"; }

start() {
    if [ -z "$(_vite_pid)" ]; then
        echo "Starting Vite dev server on :5173 ..."
        ( cd "$ROOT_DIR/frontend" && nohup npm run dev > "$VITE_LOG" 2>&1 & )
        sleep 3
    else
        echo "Vite already running on :5173"
    fi

    if [ -z "$(_cf_pid)" ]; then
        echo "Starting Cloudflare tunnel ..."
        : > "$CF_LOG"
        nohup cloudflared tunnel --url http://localhost:5173 > "$CF_LOG" 2>&1 &
    else
        echo "Tunnel already running"
    fi

    echo "Waiting for tunnel URL ..."
    for _ in $(seq 1 20); do
        url=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$CF_LOG" | head -1)
        [ -n "$url" ] && break
        sleep 1
    done
    if [ -n "$url" ]; then
        echo "$url" > "$URL_FILE"
        echo "URL: $url"
    else
        echo "Tunnel URL not found yet — check $CF_LOG"
        return 1
    fi
}

stop() {
    echo "Stopping tunnel ..."
    pkill -f "cloudflared tunnel --url http://localhost:5173" 2>/dev/null && echo "  tunnel stopped" || echo "  no tunnel running"
    vp="$(_vite_pid)"
    if [ -n "$vp" ]; then
        echo "$vp" | xargs kill 2>/dev/null && echo "  vite stopped"
    fi
    rm -f "$URL_FILE"
}

url() {
    if [ -f "$URL_FILE" ]; then
        cat "$URL_FILE"
    else
        grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" "$CF_LOG" 2>/dev/null | head -1 || echo "no URL — run: $0 start"
    fi
}

status() {
    [ -n "$(_vite_pid)" ] && echo "vite:        UP (:5173)" || echo "vite:        down"
    [ -n "$(_cf_pid)" ]   && echo "cloudflared: UP" || echo "cloudflared: down"
    echo "url:         $(url)"
}

case "$1" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 1; start ;;
    url)     url ;;
    status)  status ;;
    *)       echo "Usage: $0 {start|stop|restart|url|status}"; exit 1 ;;
esac
