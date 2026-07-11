#!/usr/bin/env bash
set -euo pipefail

REGISTRY="ghcr.io/cooperkeenan"
TAG="${1:-latest}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

build_and_push() {
  local name="$1"
  local dir="$2"
  local image="$REGISTRY/codeflow-$name:$TAG"
  echo "▶ Building $name ($dir) → $image"
  docker build \
    --build-arg SERVICE_DIR="$dir" \
    --platform linux/amd64 \
    -t "$image" \
    "$REPO_ROOT"
  echo "▶ Pushing $image"
  docker push "$image"
  echo "✓ $name done"
}

build_and_push api                api
build_and_push profiler           agents/profiler_agent
build_and_push tracer             agents/tracer_agent
build_and_push render             agents/render_agent
build_and_push layout             agents/layout_agent

echo ""
echo "All images pushed. Railway image URLs:"
echo "  api:      $REGISTRY/codeflow-api:$TAG"
echo "  profiler: $REGISTRY/codeflow-profiler:$TAG"
echo "  tracer:   $REGISTRY/codeflow-tracer:$TAG"
echo "  render:   $REGISTRY/codeflow-render:$TAG"
echo "  layout:   $REGISTRY/codeflow-layout:$TAG"
