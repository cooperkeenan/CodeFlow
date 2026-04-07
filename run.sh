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
    local ports=(8000 8001 8002 8003 8004 5173 5174 5175 5176 5177)
    for port in "${ports[@]}"; do
        pids=$(lsof -ti :"$port")
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null
            echo "  ✓ Cleared port $port"
        fi
    done
}


start_all() {
    activate_venv
    > "$ROOT_DIR/$PID_FILE"
    echo "Clearing ports..."
    kill_ports
    sleep 1
    echo ""
    echo "Starting services..."

    start_service "API Gateway"            api                                    8000
    start_service "Platform Orchestrator"  agents/platform_orchestrator           8001
    start_service "Profiler Agent"         agents/profiler_agent                  8002
    start_service "Tracer Agent"           agents/tracer_agent                    8003
    start_service "Render Agent"           agents/render_agent                    8004

    echo ""
    echo "Starting frontend..."
    cd "$ROOT_DIR/frontend"
    npm run dev &
    echo "$!" >> "$ROOT_DIR/$PID_FILE"
    echo "  ✓ Frontend on port 5173 (pid $!)"
    cd "$ROOT_DIR"

    echo ""
    echo "All services running. PIDs saved to .pids"
}

stop_all() {
    if [ ! -f "$ROOT_DIR/$PID_FILE" ]; then
        echo "No running services found."
        return
    fi

    echo ""
    echo "Stopping services..."
    while read -r pid; do
        if kill "$pid" 2>/dev/null; then
            echo "  ✓ Stopped pid $pid"
        fi
    done < "$ROOT_DIR/$PID_FILE"

    rm "$ROOT_DIR/$PID_FILE"
    echo "All services stopped."
}

echo ""
echo "==============================="
echo "   Doc Generator Dev Runner"
echo "==============================="
echo ""
echo "  1) Start all"
echo "  2) Stop all"
echo ""
read -rp "Select option: " choice
echo ""

case $choice in
    1) start_all ;;
    2) stop_all ;;
    *) echo "Invalid option." ;;
esac