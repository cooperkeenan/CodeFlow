#!/bin/bash

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUTS_DIR="$ROOT_DIR/shared/outputs"
GATEWAY="http://localhost:8000"

mkdir -p "$OUTPUTS_DIR"

get_env_value() {
    grep -E "^${1}=" "$ROOT_DIR/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '[:space:]'
}

while true; do
    echo ""
    echo "==============================="
    echo "   CodeFlow Dev Runner"
    echo "==============================="
    echo "  Repo: $(basename "$(get_env_value LOCAL_REPO_PATH)")"
    echo ""
    echo "  1) Profiler "
    echo "  2) Tracer "
    echo "  3) Render "
    echo "  4) Stop "
    echo ""
    read -rp "Select: " choice

    case $choice in
        1)
            response=$(curl -sf -X POST "$GATEWAY/analyse/local" -H "Content-Type: application/json")
            [ $? -ne 0 ] && echo "✗ Failed" && continue
            echo "$response" | python3 -m json.tool | tee \
                >(python3 -c "import json,sys; d=json.load(sys.stdin); open('$OUTPUTS_DIR/profiler_output.json','w').write(json.dumps(d['profile'], indent=2))") \
                >(python3 -c "import json,sys; d=json.load(sys.stdin); open('$OUTPUTS_DIR/tracer_output.json','w').write(json.dumps(d['trace'], indent=2))") \
                > /dev/null
            echo "✓ Saved profiler_output.json + tracer_output.json"
            ;;
        2)
            [ ! -f "$OUTPUTS_DIR/profiler_output.json" ] && echo "✗ No stored profiler output" && continue
            response=$(curl -sf -X POST "$GATEWAY/analyse/from-profile" \
                -H "Content-Type: application/json" \
                -d @"$OUTPUTS_DIR/profiler_output.json")
            [ $? -ne 0 ] && echo "✗ Failed" && continue
            echo "$response" | python3 -m json.tool | \
                python3 -c "import json,sys; d=json.load(sys.stdin); open('$OUTPUTS_DIR/tracer_output.json','w').write(json.dumps(d['trace'], indent=2))"
            echo "✓ Saved tracer_output.json"
            ;;
        3)
            [ ! -f "$OUTPUTS_DIR/tracer_output.json" ] && echo "✗ No stored tracer output" && continue
            curl -sf -X POST "$GATEWAY/analyse/from-trace" \
                -H "Content-Type: application/json" \
                -d @"$OUTPUTS_DIR/tracer_output.json" | python3 -m json.tool
            ;;
        4)
            echo "Stopping..."
            for port in 8000 8002 8003 8004; do
                pids=$(lsof -ti :"$port")
                if [ -n "$pids" ]; then
                    echo "$pids" | xargs kill -9 2>/dev/null
                    echo "  ✓ Cleared port $port"
                fi
            done
            exit 0
            ;;
    esac
done