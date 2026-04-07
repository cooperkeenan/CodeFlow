#!/bin/bash

VENV_DIR="venv"
PID_FILE=".pids"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

activate_venv() {
    source "$ROOT_DIR/$VENV_DIR/bin/activate"
}

start_service() {
    local name=$1
    local dir=$2
    local port=$3

    uvicorn main:app \
        --app-dir "$ROOT_DIR/$dir" \
        --host 0.0.0.0 \
        --port "$port" \
        --reload &
    echo "$!" >> "$ROOT_DIR/$PID_FILE"
    echo "  ✓ $name on port $port (pid $!)"
}

kill_ports() {
    local ports=(8000 8002 8003 8004 5173 5174 5175 5176 5177)
    for port in "${ports[@]}"; do
        pids=$(lsof -ti :"$port")
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null
            echo "  ✓ Cleared port $port"
        fi
    done
}

activate_venv
> "$ROOT_DIR/$PID_FILE"

echo ""
echo "==============================="
echo "   CodeFlow Dev Runner"
echo "==============================="
echo ""
echo "Clearing ports..."
kill_ports
sleep 1

echo ""
echo "Starting services..."
start_service "API Gateway"     api                   8000
start_service "Profiler Agent"  agents/profiler_agent 8002
start_service "Tracer Agent"    agents/tracer_agent   8003
start_service "Render Agent"    agents/render_agent   8004

echo ""
echo "Starting frontend..."
cd "$ROOT_DIR/frontend"
npm run dev &
echo "$!" >> "$ROOT_DIR/$PID_FILE"
echo "  ✓ Frontend on port 5173 (pid $!)"
cd "$ROOT_DIR"

echo ""
echo "All services running. PIDs saved to .pids"